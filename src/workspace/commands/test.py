import argparse
import logging
import os
import re
import sys

from workspace.commands.helpers import expand_product_groups, ToxIni
from workspace.config import config
from workspace.scm import repo_check, product_name, repo_path
from workspace.utils import run, split_doc

log = logging.getLogger(__name__)


def setup_test_parser(subparsers):
  doc, docs = split_doc(test.__doc__)
  test_parser = subparsers.add_parser('test', description=doc, help=doc)
  test_parser.add_argument('env_or_file', nargs='*', help=docs['env_or_file'])
  group = test_parser.add_mutually_exclusive_group()
  group.add_argument('-d', '--dependencies', action='store_true', help=docs['dependencies'])
  group.add_argument('-r', '--redevelop', action='store_true', help=docs['redevelop'])
  group.add_argument('-R', '--recreate', action='store_true', help=docs['recreate'])
  test_parser.add_argument('-s', action='store_true', dest='show_output', help=docs['show_output'])
  test_parser.add_argument('-k', metavar='NAME_PATTERN', dest='match_test', help=docs['match_test'])

  test_parser.set_defaults(command=test)

  return test_parser


def test(env_or_file=None, dependencies=False, redevelop=False, recreate=False, show_output=False, match_test=None, debug=False, **kwargs):
  """
  Run tests and manage test environments for product.

  :param list env_or_file: The tox environment to act upon, or a file to pass to py.test (only used
                           if file exists, we don't need to redevelop, and py.test is used as a command
                           for the default environements). Defaults to the envlist in tox.
  :param bool dependencies: Show where product dependencies are installed from and their versions.
  :param bool redevelop: Redevelop the test environments by running installing on top of existing one.
                         This is implied if test environment does not exist, or whenever setup.py or
                         requirements.txt is modified after the environment was last updated.
  :param bool recreate: Completely recreate the test environments by removing the existing ones first
  :param bool show_output: Show test output [if we don't need to develop].
  :param bool match_test: Only run tests that contains text [if we don't need to develop].
  """
  repo_check()
  repo = repo_path()

  if dependencies:
    show_installed_dependencies(repo)
    sys.exit(0)

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

  tox = ToxIni(repo)

  if redevelop or recreate:
    cmd = ['tox', '-c', tox.path]

    if envs:
      cmd.extend(['-e', ','.join(envs)])

    if recreate:
      cmd.append('-r')

    run(cmd, cwd=repo)

    for env in envs:
      strip_version_from_entry_scripts(repo, env)
      install_editable_dependencies(repo, env)

  else:
    if not envs:
      envs = tox.envlist

    for env in envs:
      envdir = tox.envdir(env)

      def requirements_updated():
        req_mtime = os.stat(os.path.join(repo, 'setup.py')).st_mtime
        if os.path.exists(os.path.join(repo, 'requirements.txt')):
          req_mtime = max(req_mtime, os.stat(os.path.join(repo, 'requirements.txt')).st_mtime)
        return req_mtime > os.stat(envdir).st_mtime

      if not os.path.exists(envdir) or requirements_updated():
        test([env], redevelop=True)
        continue

      if len(envs) > 1:
        print env

      for command in tox.commands(env):
        full_command = os.path.join(envdir, 'bin', command)

        command_path = full_command.split()[0]
        if os.path.exists(command_path):
          if 'py.test' in full_command:
            full_command = full_command.replace('{env:PYTESTARGS:}', pytest_args)
          activate = '. ' + os.path.join(envdir, 'bin', 'activate')
          run(activate + '; ' + full_command, shell=True, cwd=repo)
          if env != envs[-1]:
            print
        else:
          log.error('%s does not exist', command_path)

def strip_version_from_entry_scripts(repo):
  """ Strip out version spec "==1.2.3" from entry scripts as they require re-develop when version is changed in develop mode. """
  name = product_name(repo)
  script_bin = os.path.join(repo, '.tox', name, 'bin')

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




def show_installed_dependencies(repo):
  script_template = """
import os
import pkg_resources

cwd = os.getcwd()
workspace_dir = os.path.dirname(cwd)

libs = [r.key for r in pkg_resources.get_distribution('%s').requires()]
output = []

def strip_cwd(dir):
  if dir.startswith(cwd + '/'):
    dir = dir[len(cwd):].lstrip('/')
  elif dir.startswith(workspace_dir):
    dir = os.path.join('..', dir[len(workspace_dir):].lstrip('/'))
  return dir

for lib in sorted(libs):
  try:
    dist = pkg_resources.get_distribution(lib)
    output.append('%%-25s %%-10s  %%s' %% (lib, dist.version, strip_cwd(dist.location)))
  except pkg_resources.DistributionNotFound:
    print '%%s is not installed' %% lib
  except Exception as e:
    print e

print '\\n'.join(output)
"""

  name = product_name(repo)
  script = script_template % name

  python = os.path.join(repo, '.tox', name, 'bin', 'python')

  if not os.path.exists(python):
    log.error('Development environment is not setup. Please run develop without --dependencies to set it up first.')
    sys.exit(1)

  log.info('Product dependencies:')
  run([python, '-c', script])


def install_editable_dependencies(repo):
  if not config.test.editable_product_dependencies:
    return

  editable_dependencies = expand_product_groups(config.test.editable_product_dependencies.split())

  log.info('Installing %d product dependencies in editable mode', len(editable_dependencies))

  pip = os.path.join(repo, '.tox', name, 'bin', 'pip')

  for lib in editable_dependencies:
    with log_exception('An error occurred when installing %s in editable mode' % lib):
      run([pip, 'uninstall', lib, '-y'], raises=False, silent=not debug)

      checkout_path = product_checkout_path(lib, workspace_path)
      if not os.path.exists(checkout_path):
        log.info('Checking out %s', lib)
        checkout_product(lib, checkout_path)

      run([pip, 'install', '--editable', product_checkout_path(lib, workspace_path)], silent=not debug)
