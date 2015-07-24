import logging

from workspace.commands import AbstractCommand
from workspace.scm import (checkout_branch, remove_branch, git_repo_check, current_branch, update_repo,
                           push_repo, merge_branch, update_branch)


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

    git_repo_check()

    if not self.branch:
      self.branch = current_branch()

    log.info('Pushing %s', self.branch)

    checkout_branch('master')

    update_repo()

    if self.branch != 'master':
      checkout_branch(self.branch)
      update_branch()  # Failed rebase can be continued easily than failed merge

      checkout_branch('master')
      merge_branch(self.branch)

    push_repo()

    if self.branch != 'master':
      remove_branch(self.branch)
