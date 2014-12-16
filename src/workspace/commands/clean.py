import logging

from workspace.scm import workspace_path
from workspace.utils import silent_run

log = logging.getLogger(__name__)


def setup_clean_parser(subparsers):
  clean_parser = subparsers.add_parser('clean', description=clean.__doc__, help=clean.__doc__)
  clean_parser.set_defaults(command=clean)

  return clean_parser


def clean(**kwargs):
  """ Clean workspace by removing build, dist, and .pyc files """

  path = workspace_path()
  log.info('Cleaning workspace %s', path)

  log.info('Removing build/dist folders')
  silent_run("rm -rf */build */dist", cwd=path, shell=True)

  log.info('Removing *.pyc files')
  silent_run("find . -path /*/.tox -prune -o -path /*/mppy-* -prune -o -name *.pyc -delete", cwd=path)
