import logging

from workspace.scm import checkout_branch, remove_branch, git_repo_check, current_branch, update_repo,\
    push_repo, merge_branch, local_commit, diff_branch, extract_commit_msgs, update_branch
from workspace.utils import split_doc


log = logging.getLogger(__name__)

MIN_COMMIT_MSG_LEN = 10


def setup_push_parser(subparsers):
  doc, docs = split_doc(push.__doc__)
  push_parser = subparsers.add_parser('push', description=doc, help=doc)
  push_parser.add_argument('branch', nargs='?', help=docs['push'])
  push_parser.set_defaults(command=push)

  return push_parser


def push(branch=None, **kwargs):
  """
  Push changes for branch

  :param bool push: The branch to push. Defaults to current branch.
  """

  git_repo_check()

  if not branch:
    branch = current_branch()

  log.info('Pushing %s', branch)

  checkout_branch('master')

  update_repo()

  if branch != 'master':
    checkout_branch(branch)
    update_branch()  # Failed rebase can be continued easily than failed merge

    checkout_branch('master')
    merge_branch(branch)

    msgs = filter(lambda m: len(m) > MIN_COMMIT_MSG_LEN, extract_commit_msgs(diff_branch(branch)))
    local_commit('\n\n'.join(msgs))

  push_repo()

  if branch != 'master':
    remove_branch(branch)
