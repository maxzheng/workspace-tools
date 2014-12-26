from glob import glob
import logging
import os
import sys

from workspace.scm import repo_check, product_name, repo_path
from workspace.utils import silent_run, run, split_doc

log = logging.getLogger(__name__)


def setup_develop_parser(subparsers):
  # XXX: Remove from help now as it doesn't work that well
  doc, docs = split_doc(develop.__doc__)
  develop_parser = subparsers.add_parser('develop', aliases=['de'], description=doc)  # , help=doc)

  develop_parser.add_argument('-r', '--recreate', action='store_true', help=docs['recreate'])
  develop_parser.add_argument('-s', '--show', action='store_true', help=docs['show'])

  develop_parser.set_defaults(command=develop)

  return develop_parser


def develop(recreate=False, show=False, **kwargs):
  """ !! BETA !! Sets up development environment for product.

  :param bool recreate: Completely recreate the development environment by removing the existing first
  :param bool show: Show where product dependencies are installed from and their versions
  """
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

  name = product_name(repo_path())
  script = script_template % name

  python = os.path.join('.tox', name, 'bin', 'python')

  if not os.path.exists(python):
    log.error('Development environment is not setup. Please run develop without --show to set it up first.')
    sys.exit()

  log.info('Product dependencies:')
  run([python, '-c', script])
