import logging

from workspace.scm import checkout_branch, remove_branch, git_repo_check, current_branch, update_repo,\
    push_repo, merge_branch, local_commit, diff_branch, extract_commit_msgs
from workspace.utils import log_exception

log = logging.getLogger(__name__)

MIN_COMMIT_MSG_LEN = 10


def setup_push_parser(subparsers):
  push_parser = subparsers.add_parser('push', description=push.__doc__, help=push.__doc__)
  push_parser.add_argument('branch', nargs='?', help='The branch to push. Defaults to current branch.')
  push_parser.set_defaults(command=push)

  return push_parser


def push(branch=None, **kwargs):
  """ Push changes for branch """

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
