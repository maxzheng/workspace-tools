from __future__ import absolute_import
import logging

import click

from workspace.commands import AbstractCommand
from workspace.scm import (checkout_branch, remove_branch, current_branch, all_remotes,
                           push_repo, merge_branch, update_branch, parent_branch, default_remote)


log = logging.getLogger(__name__)


class Push(AbstractCommand):
    """
      Push changes for branch

      :param str branch: The branch to push. Defaults to current branch.
      :param bool all_remotes: Push changes to all remotes
      :param bool merge: Merge the branch into its parent branch before push
      :param bool force: Force the push
    """
    @classmethod
    def arguments(cls):
        _, docs = cls.docs()
        return [
          cls.make_args('branch', nargs='?', help=docs['branch']),
          cls.make_args('-a', '--all-remotes', action='store_true', help=docs['all_remotes']),
          cls.make_args('-m', '--merge', action='store_true', help=docs['merge']),
          cls.make_args('-f', '--force', action='store_true', help=docs['force'])
        ]

    def run(self):

        current = current_branch()

        if not self.branch:
            self.branch = current
        elif self.branch != current:
            checkout_branch(self.branch)

        click.echo('Pushing ' + self.branch)

        if self.merge:
            parent = parent_branch(self.branch)
            if parent:
                checkout_branch(parent)
            else:
                self.merge = False
                click.echo('Ignoring merge request as there is no parent branch')

        if not self.force:
            self.commander.run('update', quiet=True)

        if self.merge:
            checkout_branch(self.branch)
            update_branch(parent=parent)  # Failed rebase can be continued easily than failed merge

            checkout_branch(parent)
            merge_branch(self.branch)

        remotes = all_remotes() if self.all_remotes else [default_remote()]
        for remote in remotes:
            push_repo(force=self.force, remote=remote, branch=current_branch())

        if self.merge:
            remove_branch(self.branch, remote=True)
