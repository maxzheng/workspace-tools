import logging
import os

from workspace.commands import AbstractCommand
from workspace.commands.helpers import ProductPager
from workspace.scm import diff_repo, repos, product_name, current_branch, is_git_repo
from workspace.utils import log_exception

log = logging.getLogger(__name__)


class Diff(AbstractCommand):
  """
    Show diff on current product or all products in workspace

    :param str file: Show diff for file only
    :param bool master: Diff against the master branch
    :param bool name_only: List file names only. Git only.
  """
  alias = 'di'

  @classmethod
  def arguments(cls):
    _, docs = cls.docs()
    return [
      cls.make_args('file', nargs='?', help=docs['file']),
      cls.make_args('-m', '--master', action='store_true', help=docs['master']),
      cls.make_args('-l', '--name-only', action='store_true', help=docs['name_only'])
    ]

  def run(self):
    if self.file:
      scm_repos = [os.getcwd()]
    else:
      scm_repos = repos()

    optional = len(scm_repos) == 1
    pager = ProductPager(optional=optional)

    for repo in scm_repos:
      with log_exception():
        branch = 'master' if self.master else None
        output = diff_repo(repo, branch=branch, file=self.file, return_output=True, name_only=self.name_only)
        if output:
          branch = current_branch(repo) if is_git_repo(repo) else None
          pager.write(product_name(repo), output, branch)

    pager.close_and_wait()
