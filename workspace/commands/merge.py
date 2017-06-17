from __future__ import absolute_import
import logging
import sys

import click
import git

from workspace.config import config
from workspace.commands import AbstractCommand
from workspace.scm import checkout_branch, current_branch, merge_branch, diff_repo


log = logging.getLogger(__name__)


class Merge(AbstractCommand):
    """
      Merge changes from branch to current branch

      :param str branch: The branch to merge from.
      :param bool downstreams: Merge current branch to downstream branches defined in config merge.branches
                       that are on the right side of the current branch value and pushes them to all remotes.
                       Branches on the left side are ignored and not merged.
    """
    @classmethod
    def arguments(cls):
        _, docs = cls.docs()
        return [
          cls.make_args('branch', nargs='?', help=docs['branch']),
          cls.make_args('-d', '--downstreams', action='store_true', help=docs['downstreams'])
        ]

    def run(self):
        current = current_branch()

        if self.branch and self.downstreams:
            log.error('Branch and --downstreams are mutually exclusive. Please use one or the other.')
            sys.exit(1)

        if git.Repo().is_dirty(untracked_files=True):
            log.error('Your repo has untracked or modified files in working dir or in staging index. Please cleanup before doing merge')
            sys.exit(1)

        self.commander.run('update', quiet=True)

        if self.branch:
            click.echo('Merging {} into {}'.format(self.branch, current))
            merge_branch(self.branch)

        elif self.downstreams:
            if not config.merge.branches:
                log.error('Config merge.branches must be configured with a list of branches to merge to')
                sys.exit(1)

            branches = config.merge.branches.split()
            if current not in branches:
                log.error('Current branch %s not found in config merge.branches (%s)', current, config.merge.branches)
                sys.exit(1)

            last = current
            downstream_branches = branches[branches.index(last)+1:]

            if not downstream_branches:
                click.echo('You are currently on the last branch, so no downstream branches to merge.')
                click.echo('Switch to the branch that you want to merge from first, and then re-run')
                sys.exit(0)

            if len(downstream_branches) > 1:
                click.echo('Merging to downstream branches: ' + ', '.join(downstream_branches))

            for branch in downstream_branches:
                click.echo('Merging {} into {}'.format(last, branch))
                checkout_branch(branch)
                self.commander.run('update', quiet=True)
                merge_branch(last)
                self.commander.run('push', all_remotes=True)
                last = branch

        else:
            log.error('Please specify either a branch to merge from or --downstreams to merge to all downstream branches')
            sys.exit(1)

