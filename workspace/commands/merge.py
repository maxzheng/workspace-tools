from __future__ import absolute_import
import logging
import sys

from workspace.config import config
from workspace.commands import AbstractCommand
from workspace.scm import checkout_branch, current_branch, merge_branch


log = logging.getLogger(__name__)


class Merge(AbstractCommand):
    """
      Merge changes from branch to current branch

      :param str branch: The branch to merge from.
      :param bool all: Merge current branch to all branches defined in config merge.branches
                       that are on the right side of the current branch value and pushes them to all remotes.
                       Branches on the left side are ignored and not merged.
    """
    @classmethod
    def arguments(cls):
        _, docs = cls.docs()
        return [
          cls.make_args('branch', nargs='?', help=docs['branch']),
          cls.make_args('-a', '--all', action='store_true', help=docs['all'])
        ]

    def run(self):

        current = current_branch()

        if self.branch and self.all:
            log.error('Branch and --all are mutually exclusive. Please use one or the other.')
            sys.exit(1)

        if self.branch:
            log.info('Merging %s into %s', self.branch, current)
            self.commander.run('update', quiet=True)
            merge_branch(self.branch)

        if self.all:
            if not config.merge.branches:
                log.error('Config merge.branches must be configured with a list of branches to merge to')
                sys.exit(1)

            branches = config.merge.branches.split()

            if current not in branches:
                log.error('Current branch %s not found in config merge.branches (%s)', current, config.merge.branches)
                sys.exit(1)

            last = current
            for branch in branches[branches.index(last)+1:]:
                log.info('Merging %s into %s', last, branch)
                checkout_branch(branch)
                self.commander.run('update', quiet=True)
                merge_branch(last)
                self.commander.run('push', all_remotes=True)
                last = branch
