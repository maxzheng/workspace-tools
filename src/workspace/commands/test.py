import argparse
import logging
import os
import re
import sys

import simplejson as json

from workspace.commands.helpers import expand_product_groups, ToxIni
from workspace.config import config
from workspace.scm import repo_check, product_name, repo_path, product_repos, product_path
from workspace.utils import run, split_doc, log_exception

log = logging.getLogger(__name__)


def setup_test_parser(subparsers):
  doc, docs = split_doc(test.__doc__)
  test_parser = subparsers.add_parser('test', description=doc, help=doc)
  test_parser.add_argument('env_or_file', nargs='*', help=docs['env_or_file'])
  test_parser.add_argument('-s', action='store_true', dest='show_output', help=docs['show_output'])
  test_parser.add_argument('-k', metavar='NAME_PATTERN', dest='match_test', help=docs['match_test'])
  group = test_parser.add_mutually_exclusive_group()
  group.add_argument('-d', '--show-dependencies', action='store_true', help=docs['show_dependencies'])
  group.add_argument('-r', '--redevelop', action='store_true', help=docs['redevelop'])
  group.add_argument('-R', '--recreate', action='store_true', help=docs['recreate'])

  test_parser.set_defaults(command=test)

  return test_parser


def test(env_or_file=None, show_dependencies=False, redevelop=False, recreate=False, show_output=False, match_test=None, tox_cmd=None, tox_ini=None, tox_commands={}, additional_requirements=None, debug=False, silent=False, **kwargs):
  """
  Run tests and manage test environments for product.

  :param list env_or_file: The tox environment to act upon, or a file to pass to py.test (only used
                           if file exists, we don't need to redevelop, and py.test is used as a command
                           for the default environements). Defaults to the envlist in tox.
  :param bool show_dependencies: Show where product dependencies are installed from and their versions.
                            Dependencies can be configured to be installed in editable mode in workspace.cfg
                            with [test] editable_product_dependencies setting.
  :param bool redevelop: Redevelop the test environment by installing on top of existing one.
                         This is implied if test environment does not exist, or whenever setup.py or
                         requirements.txt is modified after the environment was last updated.
  :param bool recreate: Completely recreate the test environment by removing the existing one first.
  :param bool show_output: Show output from tests
  :param bool match_test: Only run tests with method name that matches pattern
  :param list tox_cmd: Alternative tox command to run.
                       If recreate is True, '-r' will be appended.
                       If env is passed in (from env_or_file), '-e env' will be appended as well.
  :param str tox_ini: Path to tox_ini file.
  :param dict tox_commands: Map of env to list of commands to override "[testenv:env] commands" setting for env.
                            Only used when not developing.
  :param list additional_requirements: Additional requirements files to check for modified time to auto develop when changed.
                                       By default, setup.py and requirements.txt are checked.
  :param bool silent: Run tox/py.test silently. Only errors are printed and followed by exit.
  :return: Dict of env to commands ran on success
  """
  repo_check()
  repo = repo_path()

  # Strip out venv bin path to python to avoid issues with it being removed when running tox
  if 'VIRTUAL_ENV' in os.environ:
    venv_bin = os.environ['VIRTUAL_ENV']
    os.environ['PATH'] = os.pathsep.join([p for p in os.environ['PATH'].split(os.pathsep)
                                          if os.path.exists(p) and not p.startswith(venv_bin)])

  envs = []
  files = []

  if env_or_file:
    for ef in env_or_file:
      if os.path.exists(ef):
        files.append(os.path.abspath(ef))
      else:
        envs.append(ef)

  pytest_args = ''
  if show_output or match_test or files:
    pytest_args = []
    if show_output:
      pytest_args.append('-s')
    if match_test:
      pytest_args.append('-k ' + match_test)
    if files:
      pytest_args.extend(files)
    pytest_args = ' '.join(pytest_args)
    os.environ['PYTESTARGS'] = pytest_args

  tox = ToxIni(repo, tox_ini)

  if not envs:
    envs = tox.envlist

  env_commands = {}

  if show_dependencies:
    for env in envs:
      show_installed_dependencies(tox, env)

  elif redevelop or recreate:
    if tox_cmd:
      cmd = tox_cmd
    else:
      cmd = ['tox', '-c', tox.path]

    if envs:
      cmd.extend(['-e', ','.join(envs)])

    if recreate:
      cmd.append('-r')

    if not run(cmd, cwd=repo, raises=False, silent=silent):
      sys.exit(1)

    for env in envs:
      env_commands[env] = ' '.join(cmd)
      strip_version_from_entry_scripts(tox, env)
      install_editable_dependencies(tox, env, silent, debug)

  else:
    for env in envs:
      envdir = tox.envdir(env)

      def requirements_updated():
        req_mtime = os.stat(os.path.join(repo, 'setup.py')).st_mtime
        requirements_files = ['requirements.txt']
        if additional_requirements:
          requirements_files.extend(additional_requirements)
        for req_file in requirements_files:
          req_path = os.path.join(repo, req_file)
          if os.path.exists(req_path):
            req_mtime = max(req_mtime, os.stat(req_path).st_mtime)
        return req_mtime > os.stat(envdir).st_mtime

      if not os.path.exists(envdir) or requirements_updated():
        env_commands.update(test([env], redevelop=True, tox_cmd=tox_cmd, tox_ini=tox_ini, tox_commands=tox_commands,
                                 show_output=show_output, match_test=match_test, silent=silent, debug=debug))
        continue

      if len(envs) > 1 and not silent:
          print env

      commands = tox_commands.get(env) or tox.commands(env)
      env_commands[env] = '\n'.join(commands)

      for command in commands:
        full_command = os.path.join(envdir, 'bin', command)

        command_path = full_command.split()[0]
        if os.path.exists(command_path):
          if 'py.test' in full_command:
            if 'PYTESTARGS' in full_command:
              full_command = full_command.replace('{env:PYTESTARGS:}', pytest_args)
            else:
              full_command += ' ' + pytest_args
          activate = '. ' + os.path.join(envdir, 'bin', 'activate')
          if not run(activate + '; ' + full_command, shell=True, cwd=repo, raises=False, silent=silent):
            sys.exit(1)
          if env != envs[-1] and not silent:
            print
        else:
          log.error('%s does not exist', command_path)
          sys.exit(1)

  return env_commands

def strip_version_from_entry_scripts(tox, env):
  """ Strip out version spec "==1.2.3" from entry scripts as they require re-develop when version is changed in develop mode. """
  name = product_name(tox.repo)
  script_bin = tox.bindir(env)

  if os.path.exists(script_bin):
    name_version_re = re.compile('%s==[0-9\.]+' % name)
    removed_from = []
    for script in os.listdir(script_bin):
      script_path = os.path.join(script_bin, script)

      with open(script_path) as fp:
        script = fp.read()

      if name_version_re.search(script):
        new_script = name_version_re.sub(name, script)
        with open(script_path, 'w') as fp:
          fp.write(new_script)
        removed_from.append(os.path.basename(script_path))

    if removed_from:
      log.debug('Removed version spec from entry script(s): %s', ', '.join(removed_from))




def show_installed_dependencies(tox, env, return_output = False):
  script_template = """
import json
import os
import pkg_resources
import sys

# Required params to run this script
package = '%s'
json_output = %s
env = '%s'

cwd = os.getcwd()
workspace_dir = os.path.dirname(cwd)

try:
  libs = [r.key for r in pkg_resources.get_distribution(package).requires()]
except pkg_resources.DistributionNotFound as e:
  print "%%s: %%s is not installed" %% (env, e)
  sys.exit(1)
except Exception as e:
  print e
  sys.exit(1)

output = []

if not json_output:
  print env + ':'

def strip_cwd(dir):
  if dir.startswith(cwd + '/'):
    dir = dir[len(cwd):].lstrip('/')
  elif dir.startswith(workspace_dir):
    dir = os.path.join('..', dir[len(workspace_dir):].lstrip('/'))
  return dir

for lib in sorted(libs):
  try:
    dist = pkg_resources.get_distribution(lib)
    if json_output:
      output.append((lib, dist.version, dist.location))
    else:
      output.append('  %%-25s %%-10s  %%s' %% (lib, dist.version, strip_cwd(dist.location)))
  except pkg_resources.DistributionNotFound:
    if json_output:
      output.append((lib, None, None))
    else:
      print '  %%s is not installed' %% lib
  except Exception as e:
    if not json_output:
      print '  %%s' %% e

if json_output:
  print json.dumps(output)
else:
  print '\\n'.join(output)
"""

  name = product_name(tox.repo)
  script = script_template % (name, return_output, env)

  python = tox.bindir(env, 'python')

  if not os.path.exists(python):
    log.error('Test environment %s is not installed. Please run without -d / --show-dependencies to install it first.', env)
    sys.exit(1)

  return run([python, '-c', script], return_output=return_output, raises=False)


def install_editable_dependencies(tox, env, silent, debug):
  if not config.test.editable_product_dependencies:
    return

  name = product_name(tox.repo)

  dependencies_output = show_installed_dependencies(tox, env, return_output=True)
  product_dependencies_list = json.loads(dependencies_output)
  product_dependencies = {}

  for dep, _, path in product_dependencies_list:
    product_dependencies[dep] = path

  editable_dependencies = expand_product_groups(config.test.editable_product_dependencies.split())
  available_products = [os.path.basename(r) for r in product_repos()]
  libs = [d for d in editable_dependencies if d in available_products and d in product_dependencies and tox.workdir in product_dependencies[d]]

  pip = tox.bindir(env, 'pip')

  for lib in libs:
    if not silent or debug:
      log.info('%s: Installing %s in editable mode' % (env, lib))

    with log_exception('An error occurred when installing %s in editable mode' % lib):
      run([pip, 'uninstall', lib, '-y'], raises=False, silent=not debug)

      lib_path = product_path(lib)
      run([pip, 'install', '--editable', lib_path], silent=not debug)
