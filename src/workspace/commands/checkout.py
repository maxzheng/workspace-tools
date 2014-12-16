import logging

from workspace.commands.helpers import expand_product_groups
from workspace.scm import checkout_product, checkout_branch, is_git_repo, all_branches, checkout_files, is_repo, product_checkout_path
from workspace.utils import log_exception

log = logging.getLogger(__name__)


def setup_checkout_parser(subparsers):
  checkout_parser = subparsers.add_parser('checkout', aliases=['co'], description=checkout.__doc__, help=checkout.__doc__)
  checkout_parser.add_argument('target', nargs='+', help='List of products or git/svn repository URLs to checkout. '
                               'When inside a git repo, checkout the branch or revert changes for file(s). When inside a '
                               'svn repo, revert changes for file(s)')
  checkout_parser.set_defaults(command=checkout)

  return checkout_parser


def checkout(target, dependencies=None, **kwargs):
  """ Checkout products """

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
