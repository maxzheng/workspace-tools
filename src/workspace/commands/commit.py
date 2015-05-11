import logging
import re

from workspace.config import config

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
  commit_parser.add_argument('-D', '--discard', action='count', help=docs['discard'])
  commit_parser.add_argument('--move', metavar='branch', nargs=1, help=docs['move'])
  commit_parser.set_defaults(command=commit)

  return commit_parser


def commit(msg=None, branch=None, amend=False, push=False, dummy=False, discard=False, move=None, skip_auto_branch=False, files=None, **kwargs):
  """
  Commit all changes locally, including new files.

  :param str msg: Commit message. The first few words are used to create the branch name if branch isn't provided.
                  That behavior can be configured with [commit] auto_branch_from_commit_words
  :param str branch: Create or use existing branch for commit. When creating, it always creates from master branch.
  :param bool amend: Amend last commit with any new changes made
  :param bool push: Push the current branch after commit
  :param bool dummy: Perform a dummy commit without any changes on master branch. This implies --push.
                     Other options are ignored.
  :param int discard: Discard last commit, or branch if there are no more commits. Use multiple times to discard multiple commits.
                      Other options are ignored.
  :param str move: Move last commit to branch. Other options are ignored.
  :param bool skip_auto_branch: Skip automatic branch creation from commit msg
  :param list files: List of files to add instead of all files.
  """

  git_repo_check()

  if dummy:
    checkout_branch('master')
    update_repo()  # Needs to be updated otherwise empty commit below gets erased in push_branch when update is called
    if not msg:
      msg = 'Empty commit to trigger build'
    local_commit(msg, empty=True)
    push_branch(skip_precommit=True)

  elif discard or move:
    if not branch:
      if discard:
        branch = current_branch()
      else:
        branch = move[0]

    if discard:
      changes = commit_logs(discard) if branch == 'master' else diff_branch(branch)
    else:
      changes = commit_logs(1)
    changes = filter(None, changes.split('commit '))

    if discard and len(changes) <= discard and branch != 'master':
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
          hard_reset(last_commit + '~1')

        else:
          checkout_branch(branch)
          hard_reset(last_commit + '~' + str(discard))

      else:
        log.error('Odd. No commit hash found in: %s', changes[0])

  else:
    branches = all_branches()
    cur_branch = branches and branches[0]

    if not (skip_auto_branch or push or amend) and cur_branch == 'master' and not branch and msg and config.commit.auto_branch_from_commit_words:
      branch = branch_for_msg(msg, config.commit.auto_branch_from_commit_words, branches)

    if branch:
      if branches:
        if branch in branches:
          if branch != cur_branch:
            checkout_branch(branch)

        else:
          create_branch(branch, 'master')

      else:  # Empty repo without a commit has no branches
        create_branch(branch)

    add_files(files=files)
    local_commit(msg, amend)

    if push:
      push_branch()


def branch_for_msg(msg, words=3, branches=None):
  ignored_num_re = re.compile('^\d+$')
  ignored_words = ['and', 'but', 'for', 'from']
  ignored_word_length = 2
  branch_name = []
  word_count = 0

  if msg.startswith('DRAFT: '):
    msg = msg.replace('DRAFT: ', '', 1)

  for word in re.split('[\W\_]+', msg):
    if not word:
      continue

    branch_name.append(word.lower())

    if word not in ignored_words and not ignored_num_re.match(word) and len(word) > ignored_word_length:
      word_count += 1

    if word_count >= words and (not branches or '-'.join(branch_name) not in branches):
      break

  if not branch_name:
    raise Exception('No words found in commit msg to create branch name')

  if ((branch_name[-1] in ignored_words or not ignored_num_re.match(word) and len(branch_name[-1]) <= ignored_word_length)
     and (not branches or '-'.join(branch_name[:-1]) not in branches)):
    branch_name = branch_name[:-1]

  branch_name = '-'.join(branch_name)

  if branches and branch_name in branches:
    raise Exception('Branch "%s" already exist.\n\tPlease use a more unique commit message or specify branch with -b. Or '
                    'to amend an existing commit, use -a' % branch_name)

  return branch_name
