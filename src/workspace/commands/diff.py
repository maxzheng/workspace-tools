import logging

from workspace.commands.helpers import ProductPager
from workspace.scm import diff_repo, repos, product_name_for_repo, current_branch, is_git_repo
from workspace.utils import log_exception

log = logging.getLogger(__name__)


def setup_diff_parser(subparsers):
  diff_parser = subparsers.add_parser('diff', aliases=['di'], description=diff.__doc__, help=diff.__doc__)
  diff_parser.add_argument('file', nargs='?', help='Show diff for file only')
  diff_parser.add_argument('-m', '--master', action='store_true', help='Diff against the master branch')
  diff_parser.set_defaults(command=diff)

  return subparsers


def diff(file=None, master=False, **kwargs):
  """ Show diff on current product or all products in workspace """

  optional = len(repos()) == 1
  pager = ProductPager(optional=optional)

  for repo in repos():
    with log_exception():
      branch = 'master' if master else None
      output = diff_repo(repo, branch=branch, file=file, return_output=True)
      if output:
        branch = current_branch(repo) if is_git_repo(repo) else None
        pager.write(product_name_for_repo(repo), output, branch)

  pager.close_and_wait()
