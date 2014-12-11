import logging

from workspace.commands.helpers import product_checkout_path, expand_product_groups
from workspace.config import get_pref
from workspace.scm import checkout_product, checkout_branch, is_git_repo, all_branches, checkout_files, is_repo
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

  products = expand_product_groups(target)

  for product in products:
      log.info('Checking out %s', product)
      product_path = product_checkout_path(product)
      clone_svn_commits = get_pref('checkout.use_gitsvn_to_clone_svn_commits')

      with log_exception():
        checkout_product(product, product_path, clone_svn_commits)
