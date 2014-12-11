import logging

from workspace.commands.helpers import ProductPager
from workspace.scm import diff_repo, repos, product_name_for_repo, current_branch, is_git_repo
from workspace.utils import log_exception

log = logging.getLogger(__name__)


def diff(master=False, **kwargs):
  optional = len(repos()) == 1
  pager = ProductPager(optional=optional)

  for repo in repos():
    with log_exception():
      branch = 'master' if master else None
      output = diff_repo(repo, branch=branch, return_output=True)
      if output:
        branch = current_branch(repo) if is_git_repo(repo) else None
        pager.write(product_name_for_repo(repo), output, branch)

  pager.close_and_wait()
