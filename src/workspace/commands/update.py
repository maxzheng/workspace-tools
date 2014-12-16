import logging

from workspace.scm import is_git_repo, checkout_branch, update_repo, repos, product_name_for_repo, current_branch,\
    update_branch

log = logging.getLogger(__name__)


def setup_update_parser(subparsers):
  update_parser = subparsers.add_parser('update', aliases=['up'], description=update.__doc__, help=update.__doc__)
  update_parser.set_defaults(command=update)

  return update_parser


def update(raises=False, **kwargs):
  """ Update current product or all products in workspace """

  for repo in repos():
    log.info('Updating %s', product_name_for_repo(repo))
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
        log.error(e)
