import logging

from workspace.scm import workspace_path
from workspace.utils import silent_run

log = logging.getLogger(__name__)


def clean(**kwargs):
  path = workspace_path()
  log.info('Cleaning workspace %s', path)

  silent_run("find . -path */.tox -prune -o -path */mppy-* -prune -o -name *.pyc -delete", cwd=path)
