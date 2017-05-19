from __future__ import absolute_import
import logging
import re
import sys

from workspace.commands import AbstractCommand
from workspace.config import config
from workspace.scm import local_commit, add_files, checkout_branch,\
    create_branch, all_branches, diff_branch, current_branch, remove_branch, hard_reset, \
    commit_logs, master_branch, parent_branch
from workspace.utils import prompt_with_editor

log = logging.getLogger(__name__)


class Commit(AbstractCommand):
  """
    Commit all changes locally, including new files.

    :param str msg: Commit message. The first few words are used to create the branch name if branch isn't provided.
                    That behavior can be configured with [commit] auto_branch_from_commit_words
    :param str branch: Use specified branch for commit instead of auto-computing the branch from commit msg.
    :param bool amend: Amend last commit with any new changes made
    :param bool test: Run tests. Repeat twice (-tt) to test dependents too.
    :param bool push: Push the current branch after commit
    :param int discard: Discard last commit, or branch (child only) if there are no more commits.
                        Use multiple times to discard multiple commits.
                        Other options are ignored. Any local changes may be discarded (hard reset)
    :param str move: Move last commit to branch. Other options are ignored.
    :param callable test_command: Alternative test command to run
    :param bool skip_auto_branch: Skip automatic branch creation from commit msg
    :param list files: List of files to add instead of all files.
  """
  alias = 'ci'

  @classmethod
  def arguments(cls):
    _, docs = cls.docs()
    return ([
        cls.make_args('msg', nargs='?', help=docs['msg']),
        cls.make_args('-a', '--amend', action='store_true', help=docs['amend']),
        cls.make_args('-d', '--discard', action='count', help=docs['discard']),
        cls.make_args('--move', metavar='branch', nargs=1, help=docs['move']),
        cls.make_args('-b', '--branch', help=docs['branch'])
      ], [
        cls.make_args('-t', '--test', action='count', help=docs['test']),
        cls.make_args('-r', '--rb', action='store_true',
                      help='Create or update existing RB after commit. Existing RB is looked up in .git/config. '
                           'Use -rt to run / post the test results. Repeat twice to test dependents too (-rtt)'),
        cls.make_args('-p', '--push', action='store_true', help=docs['push'])
      ])

  def run(self):
    if self.discard or self.move:
      if not self.branch:
        if self.discard:
          self.branch = current_branch()
        else:
          self.branch = self.move[0]

      is_child_branch = base_branch = parent_branch(self.branch)

      if self.discard:
        changes = commit_logs(self.discard) if not is_child_branch else diff_branch(self.branch, left_branch=base_branch)
      else:
        changes = commit_logs(1)
      changes = [_f for _f in changes.split('commit ') if _f]

      if self.discard and len(changes) <= self.discard and is_child_branch:
        checkout_branch(base_branch)
        remove_branch(self.branch, raises=True, force=True)
        log.info('Deleted branch %s', self.branch)

      else:
        match = re.match('([a-f0-9]+)(?: \(.*\))\n', changes[0])

        if match:
          last_commit = match.group(1)

          if self.move:
            cur_branch = current_branch()
            create_branch(self.branch)
            checkout_branch(cur_branch)
            log.info('Moved %s to %s', last_commit[:7], self.branch)
            hard_reset(last_commit + '~1')

          else:
            checkout_branch(self.branch)
            hard_reset(last_commit + '~' + str(self.discard))

        else:
          log.error('Odd. No commit hash found in: %s', changes[0])

    else:
      test_output = None

      if not (self.msg or self.amend):
        self.msg = prompt_with_editor('Please provide a commit message. Empty message will cancel the commit.')
        if not self.msg:
          sys.exit()

      if not self.amend and self.test:
        if self.commander.command('test').supports_style_check():
          log.info('Running style check')
          self.commander.run('test', env_or_file=['style'], silent=2)

        log.info('Running tests')
        test_output = self.commander.run('test', return_output=self.rb, test_dependents=self.test > 1)

        if self.rb:
          success, _ = self.commander.command('test').summarize(test_output)

          if not success:
            sys.exit(1)

      branches = all_branches()
      cur_branch = branches and branches[0]

      if (not (not self.rb and self.push or self.amend) and config.commit.commit_branch_indicator not in cur_branch and not self.branch and self.msg and
         config.commit.auto_branch_from_commit_words):
        self.branch = '{}@{}'.format(
            self._branch_for_msg(self.msg, words=config.commit.auto_branch_from_commit_words,
                                 branches=branches),
            cur_branch)

      if self.branch:
        if branches:
          if self.branch in branches:
            if self.branch != cur_branch:
              checkout_branch(self.branch)

          else:
            create_branch(self.branch, cur_branch)

        else:  # Empty repo without a commit has no branches
          create_branch(self.branch)

      add_files(files=self.files)
      local_commit(self.msg, self.amend)

      if self.amend and self.test:
        if self.commander.command('test').supports_style_check():
          log.info('Running style check')
          self.commander.run('test', env_or_file=['style'], silent=2)

        log.info('Running tests')
        test_output = self.commander.run('test', return_output=self.rb, test_dependents=self.test > 1)

        if self.rb:
          success, _ = self.commander.command('test').summarize(test_output)

          if not success:
            sys.exit(1)

      if self.rb:
        publish = self.push and (self.amend or test_output)
        self.commander.run('review', publish=publish, test=test_output, skip_prereview=self.test)

        if self.push:
          if not publish:
            log.info("Review was not published as there is no testing done. Please update testing done and then publish")
          self.branch = current_branch()  # Ensure branch is set for push as it could change while waiting
          self.commander.run('wait', review=True, in_background=True)

      if self.push:
        self.commander.run('push', branch=self.branch, skip_precommit=self.rb, force=self.amend)

      return test_output

  @classmethod
  def _branch_for_msg(cls, msg, words=3, branches=None):
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

    has_ignored_or_short_name = branch_name[-1] in ignored_words or not ignored_num_re.match(word) and len(branch_name[-1]) <= ignored_word_length
    no_name_conflict = not branches or '-'.join(branch_name[:-1]) not in branches
    if has_ignored_or_short_name and no_name_conflict:
      branch_name = branch_name[:-1]

    branch_name = '-'.join(branch_name)

    if branches and branch_name in branches:
      raise Exception('Branch "%s" already exist.\n\tPlease use a more unique commit message or specify branch with -b. Or '
                      'to amend an existing commit, use -a' % branch_name)

    return branch_name
