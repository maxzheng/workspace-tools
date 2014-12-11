import logging

from workspace.commands.helpers import expand_product_groups
from workspace.config import get_pref
from workspace.scm import checkout_product, checkout_branch, is_git_repo, all_branches, checkout_files, is_repo, product_checkout_path
from workspace.utils import log_exception

log = logging.getLogger(__name__)


def checkout(target, dependencies=None, **kwargs):

  if is_repo():
    with log_exception():
      if is_git_repo() and len(target) == 1 and target[0] in all_branches():
        checkout_branch(target[0])
        log.info('Switched to branch %s', target[0])
      else:
        checkout_files(target)
    return

  product_urls = expand_product_groups(target)

  for product_url in product_urls:
      log.info('Checking out %s', product_url)
      product_path = product_checkout_path(product_url)

      with log_exception():
        checkout_product(product_url, product_path)
