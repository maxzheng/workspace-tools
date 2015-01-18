import argparse
from glob import glob
import logging
import os
import re
import sys

from localconfig import LocalConfig
from workspace.scm import repo_check, product_name, repo_path
from workspace.utils import run, split_doc

log = logging.getLogger(__name__)


def setup_test_parser(subparsers):
  doc, docs = split_doc(test.__doc__)
  test_parser = subparsers.add_parser('test', description=doc, help=doc)
  test_parser.add_argument('env_or_file', nargs='*', help=docs['env_or_file'])
  group = test_parser.add_mutually_exclusive_group()
  group.add_argument('-s', '--show', action='store_true', help=docs['show'])
  group.add_argument('-r', '--redevelop', action='store_true', help=docs['redevelop'])
  group.add_argument('-R', '--recreate', action='store_true', help=docs['recreate'])

  test_parser.set_defaults(command=test)

  return test_parser


def test(env_or_file=None, show=False, redevelop=False, recreate=False, debug=False, **kwargs):
  """
  Runs tests and manages test environments for product.

  :param str env_or_file: The tox environment to act upon, or a file to pass to py.test (only used
                          if file exists, we don't need to redevelop, and py.test is used as a command
                          for the default environements). Defaults to the envlist in tox.
  :param bool show: Show where product dependencies are installed from and their versions
  :param bool redevelop: Redevelop the test environments by running installing on top of existing one.
  :param bool recreate: Completely recreate the test environments by removing the existing ones first
  """
  repo_check()

  if show:
    show_installed_dependencies()
    sys.exit(0)

  tox_inis = glob(os.path.join(repo_path(), 'tox*.ini'))

  if not tox_inis:
    log.error('No tox.ini found. Please run "wst setup --product" first to setup tox.')
    sys.exit(1)

  elif len(tox_inis) > 1:
    log.warn('More than one ini files found - will use first one: %s', ', '.join(tox_inis))

  tox_ini = tox_inis[0]

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
        files.append(ef)
      else:
        envs.append(ef)

  if redevelop or recreate:
    cmd = ['tox', '-c', tox_ini]

    if envs:
      cmd.extend(['-e', ','.join(envs)])

    if recreate:
      cmd.append('-r')

    run(cmd, cwd=repo_path())
    strip_version_from_entry_scripts(repo_path())

  else:
    tox = LocalConfig(tox_ini)

    if not envs:
      envs = filter(None, tox.tox.envlist.split(','))

    for env in envs:
      env_section = 'testenv:%s' % env

      if env_section not in tox:
        log.debug('Using default envdir and commands as %s section is not defined in %s', env_section, tox_ini)

      envdir = tox.get(env_section, 'envdir', os.path.join('.tox', env)).replace('{toxworkdir}', '.tox')
      commands = tox.get(env_section, 'commands', 'py.test')

      if not os.path.exists(envdir):
        run(['tox', '-c', tox_ini, '-e', env])
        continue

      if len(envs) > 1:
        print env

      for command in filter(None, commands.split('\n')):
        full_command = os.path.join(envdir, 'bin', command)

        command_path = full_command.split()[0]
        if os.path.exists(command_path):
          if files and 'py.test' in command_path:
            full_command += ' ' + ' '.join(files)
          run(full_command)
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




def show_installed_dependencies():
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

  name = product_name(repo_path())
  script = script_template % name

  python = os.path.join(repo_path(), '.tox', name, 'bin', 'python')

  if not os.path.exists(python):
    log.error('Development environment is not setup. Please run develop without --show to set it up first.')
    sys.exit(1)

  log.info('Product dependencies:')
  run([python, '-c', script])
