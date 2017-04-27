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
  """
  @classmethod
  def arguments(cls):
    _, docs = cls.docs()
    return [cls.make_args('branch', nargs='?', help=docs['push'])]

  def run(self):

    current = current_branch()

    if not self.branch:
      self.branch = current

    log.info('Pushing %s', self.branch)

    parent = parent_branch(self.branch)

    checkout_branch(parent)

    update_repo()

    if self.branch != parent:
      checkout_branch(self.branch)
      update_branch(parent=parent)  # Failed rebase can be continued easily than failed merge

      checkout_branch(parent)
      merge_branch(self.branch)

    push_repo()

    if self.branch != parent:
      remove_branch(self.branch)
