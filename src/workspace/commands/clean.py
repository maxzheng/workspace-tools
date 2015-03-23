import logging
import os
import shutil
from time import time

from workspace.config import config
from workspace.scm import workspace_path, product_name, repos, stat_repo
from workspace.utils import silent_run

log = logging.getLogger(__name__)


def setup_clean_parser(subparsers):
  clean_parser = subparsers.add_parser('clean', description=clean.__doc__, help=clean.__doc__)
  clean_parser.set_defaults(command=clean)

  return clean_parser


def clean(**kwargs):
  """ Clean workspace by removing build, dist, and .pyc files """

  path = workspace_path()
  log.info('Cleaning %s', path)

  log.info('Removing build/dist folders')
  silent_run("rm -rf */build */dist */docs/_build", cwd=path, shell=True)

  log.info('Removing *.pyc files')
  silent_run("find . -type d \( -path '*/.tox' -o -path '*/mppy-*' \) -prune -o -name *.pyc -exec rm {} \;", cwd=path, shell=True)

  if config.clean.remove_products_older_than_days:
    log.info('Removing products older than %s days', config.clean.remove_products_older_than_days)

    removed_products = []

    for repo in repos(path):
      modified_time = os.stat(repo).st_mtime
      if modified_time < (time() - config.clean.remove_products_older_than_days * 86400):
        status = stat_repo(repo, return_output=True)
        if not status or 'nothing to commit' in status and 'working directory clean' in status:
          shutil.rmtree(repo)
          removed_products.append(product_name(repo))
        else:
          log.info('  - Skipping "%s" as it has changes that may not be committed', product_name(repo))

    if removed_products:
      log.info('Removed %s', ', '.join(removed_products))
