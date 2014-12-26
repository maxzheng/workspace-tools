import logging
import re

from workspace.scm import local_commit, add_files, git_repo_check, checkout_branch,\
    create_branch, update_repo, all_branches, diff_branch, current_branch, remove_branch, hard_reset, commit_logs
from workspace.commands.push import push as push_branch
from workspace.utils import split_doc

log = logging.getLogger(__name__)


def setup_commit_parser(subparsers):
  doc, docs = split_doc(commit.__doc__)
  commit_parser = subparsers.add_parser('commit', aliases=['ci'], description=doc, help=doc)
  commit_parser.add_argument('msg', nargs='?', help=docs['msg'])
  commit_parser.add_argument('-b', '--branch', help=docs['branch'])
  commit_parser.add_argument('-a', '--amend', action='store_true', help=docs['amend'])
  commit_parser.add_argument('-p', '--push', action='store_true', help=docs['push'])
  commit_parser.add_argument('-d', '--dummy', action='store_true', help=docs['dummy'])
  commit_parser.add_argument('--discard', metavar='branch', nargs='?', const=True, help=docs['branch'])
  commit_parser.add_argument('--move', metavar='branch', nargs=1, help=docs['move'])
  commit_parser.set_defaults(command=commit)

  return commit_parser


def commit(msg=None, branch=None, amend=False, push=False, dummy=False, discard=False, move=None, **kwargs):
  """
  Commit all changes locally, including new files.

  :param str msg: Commit message
  :param str branch: Create or use existing branch for commit. When creating, it always creates from master branch.
  :param bool amend: Amend last commit with any new changes made
  :param bool push: Push the current branch after commit
  :param bool dummy: Perform a dummy commit without any changes on master branch. This implies --push.
                     Other options are ignored.
  :param bool discard: Discard last commit and branch if no more commits left. Defaults to existing branch.
                       Other options are ignored.
  :param bool move: Move last commit to branch. Other options are ignored.
  """

  git_repo_check()

  if dummy:
    checkout_branch('master')
    update_repo()  # Needs to be updated otherwise empty commit below gets erased in push_branch when update is called
    local_commit('Empty commit to trigger build', empty=True)
    push_branch(skip_precommit=True)

  elif discard or move:
    if not branch:
      if discard:
        branch = discard if isinstance(discard, str) else current_branch()
      else:
        branch = move[0]

    if discard and branch == 'master':
      log.error('Discard can not be used on master branch')
      return

    if discard:
      changes = diff_branch(branch)
    else:
      changes = commit_logs(1)
    changes = filter(None, changes.split('commit '))

    if discard and len(changes) <= 1:
      checkout_branch('master')
      remove_branch(branch, raises=True)
      log.info('Deleted branch %s', branch)

    else:
      match = re.match('([a-f0-9]+)\n', changes[0])

      if match:
        last_commit = match.group(1)

        if move:
          cur_branch = current_branch()
          create_branch(branch)
          checkout_branch(cur_branch)
          log.info('Moved %s to %s', last_commit[:7], branch)
        else:
          checkout_branch(branch)

        hard_reset(last_commit + '~1')

      else:
        log.error('Odd. No commit hash found in: %s', changes[0])

  else:
    if branch:
      if branch in all_branches():
        checkout_branch(branch)
      else:
        create_branch(branch, 'master')

    add_files()
    local_commit(msg, amend)

    if push:
      push_branch()
