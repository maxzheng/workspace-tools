import logging

from workspace.commands.helpers import expand_product_groups
from workspace.scm import is_git_repo, checkout_branch, update_repo, repos, product_name, current_branch,\
    update_branch
from workspace.utils import split_doc, parallel_call

log = logging.getLogger(__name__)


def setup_update_parser(subparsers):
  doc, docs = split_doc(update.__doc__)
  update_parser = subparsers.add_parser('update', aliases=['up'], description=doc, help=doc)
  update_parser.add_argument('products', nargs='*', help=docs['products'])
  update_parser.set_defaults(command=update)

  return update_parser


def update(products=None, raises=False, **kwargs):
  """
  Update current product or all products in workspace

  :param list products: When updating all products, filter by these products or product groups
  """

  if products:
    products = expand_product_groups(products)

  select_repos = [repo for repo in repos() if not products or products and product_name(repo) in products]

  if not select_repos:
    log.info('No product found')

  elif len(select_repos) == 1:
    _update_repo(select_repos[0], raises)

  else:
    parallel_call(_update_repo, select_repos)


def _update_repo(repo, raises=False):
  name = product_name(repo)

  log.info('Updating %s', name)

  try:
    branch = None
    if is_git_repo(repo):
      branch = current_branch(repo)
      if branch != 'master':
        checkout_branch('master', repo)

    update_repo(repo)

    if branch and branch != 'master':
      log.info('Rebasing %s', branch)
      checkout_branch(branch, repo)
      update_branch(repo)
  except Exception as e:
    if raises:
      raise
    else:
      log.error('%s for %s', e, name)
