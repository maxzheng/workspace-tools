from glob import glob
import logging
import os
import sys

from workspace.scm import repo_check, product_name, repo_path
from workspace.utils import silent_run, log_exception, run

log = logging.getLogger(__name__)


def setup_develop_parser(subparsers):
  # XXX: Remove for now as it doesn't work that well
  develop_parser = subparsers.add_parser('develop', aliases=['de'], description=develop.__doc__)  # , help=develop.__doc__)

  develop_parser.add_argument('-r', '--recreate', action='store_true', help='Completely recreate the development environment by removing the existing first')
  develop_parser.add_argument('-s', '--show', action='store_true', help='Show where product dependencies are installed from and their versions')

  develop_parser.set_defaults(command=develop)

  return develop_parser


def develop(recreate=False, show=False, **kwargs):
  """ !! BETA !! Sets up development environment for product. """
  repo_check()

  if show:
    show_installed_dependencies()
    sys.exit(0)

  tox_inis = glob('tox*.ini')
  if not tox_inis:
    log.error('No tox.ini found. Please setup tox.')
  elif len(tox_inis) > 1:
    log.warn('More than one ini files found - will use first one: %s', ', '.join(tox_inis))

  cmd = ['tox', '-c', tox_inis[0]]

  if recreate:
    cmd.append('-r')
    log.info('Recreating development environment')
  else:
    log.info('Setting up development environment')

  with log_exception():
    silent_run(cmd)


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

  with log_exception():
    name = product_name(repo_path())
    script = script_template % name

    python = os.path.join('.tox', name, 'bin', 'python')

    if not os.path.exists(python):
      log.error('Development environment is not setup. Please run develop without --show to set it up first.')
      sys.exit()

    log.info('Product dependencies:')
    run([python, '-c', script])
