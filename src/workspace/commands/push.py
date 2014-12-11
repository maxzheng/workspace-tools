import logging

from workspace.config import get_pref
from workspace.scm import checkout_branch, remove_branch, git_repo_check, current_branch, update_repo,\
    push_repo, merge_branch, local_commit, diff_branch, extract_commit_msgs
from workspace.utils import log_exception, silent_run

log = logging.getLogger(__name__)

MIN_COMMIT_MSG_LEN = 10


def push(branch=None, **kwargs):
  git_repo_check()

  if not branch:
    branch = current_branch()

  log.info('Pushing %s', branch)

  with log_exception(exit=1):
    if branch != 'master':
      checkout_branch('master')

    update_repo()

    if branch != 'master':
      merge_branch(branch)
      msgs = filter(lambda m: len(m) > MIN_COMMIT_MSG_LEN, extract_commit_msgs(diff_branch(branch)))
      local_commit('\n\n'.join(msgs))

    push_repo()

    if branch != 'master':
      remove_branch(branch)
