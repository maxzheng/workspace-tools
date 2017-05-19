from __future__ import absolute_import
import logging

from workspace.commands import AbstractCommand
from workspace.config import config
from workspace.scm import (checkout_branch, remove_branch, current_branch, update_repo,
                           push_repo, merge_branch, update_branch, parent_branch)
from workspace.utils import run


log = logging.getLogger(__name__)


class Push(AbstractCommand):
  """
    Push changes for branch

    :param bool push: The branch to push. Defaults to current branch.
    :param bool merge: Merge the branch into its parent branch before push
    :param bool force: Force the push
  """
  @classmethod
  def arguments(cls):
    _, docs = cls.docs()
    return [cls.make_args('branch', nargs='?', help=docs['push']),
            cls.make_args('-m', '--merge', action='store_true', help=docs['merge']),
            cls.make_args('-f', '--force', action='store_true', help=docs['force'])
    ]

  def run(self):

    current = current_branch()

    if not self.branch:
      self.branch = current

    log.info('Pushing %s', self.branch)

    if self.merge:
      parent = parent_branch(self.branch)
      if parent:
        checkout_branch(parent)
      else:
        self.merge = False
        log.info('Ignoring merge request as there is no parent branch')

    self.commander.run('update', quiet=True)

    if self.merge:
      checkout_branch(self.branch)
      update_branch(parent=parent)  # Failed rebase can be continued easily than failed merge

      checkout_branch(parent)
      merge_branch(self.branch)

    push_repo(force=self.force)

    if self.merge:
      remove_branch(self.branch, remote=True)
