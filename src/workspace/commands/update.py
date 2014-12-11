import logging

from workspace.scm import is_git_repo, checkout_branch, update_repo, repos, product_name_for_repo, current_branch,\
    update_branch

log = logging.getLogger(__name__)


def update(**kwargs):
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
      log.error(e)
