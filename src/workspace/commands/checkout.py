import logging

from workspace.commands.helpers import expand_product_groups
from workspace.scm import checkout_product, checkout_branch, is_git_repo, all_branches, checkout_files, is_repo, product_checkout_path
from workspace.utils import split_doc
log = logging.getLogger(__name__)


def setup_checkout_parser(subparsers):
  doc, docs = split_doc(checkout.__doc__)
  checkout_parser = subparsers.add_parser('checkout', aliases=['co'], description=doc, help=doc)
  checkout_parser.add_argument('target', nargs='+', help=docs['target'])
  checkout_parser.set_defaults(command=checkout)

  return checkout_parser


def checkout(target, **kwargs):
  """
  Checkout products (repo urls) or branch, or revert files.

  :param list target: List of products (git/svn repository URLs) to checkout. When inside a git repo,
                      checkout the branch or revert changes for file(s). When inside a svn repo, revert
                      changes for file(s)
  """

  if is_repo():
    if is_git_repo() and len(target) == 1 and target[0] in all_branches():
      checkout_branch(target[0])
      log.info('Switched to branch %s', target[0])
    else:
      checkout_files(target)
    return

  product_urls = expand_product_groups(target)

  for product_url in product_urls:
    product_url = product_url.strip('/')

    log.info('Checking out %s', product_url)

    product_path = product_checkout_path(product_url)
    checkout_product(product_url, product_path)
