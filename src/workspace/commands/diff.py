import logging
import os

from workspace.commands.helpers import ProductPager
from workspace.scm import diff_repo, repos, product_name, current_branch, is_git_repo
from workspace.utils import log_exception, split_doc

log = logging.getLogger(__name__)


def setup_diff_parser(subparsers):
  doc, docs = split_doc(diff.__doc__)
  diff_parser = subparsers.add_parser('diff', aliases=['di'], description=doc, help=doc)
  diff_parser.add_argument('file', nargs='?', help=docs['file'])
  diff_parser.add_argument('-m', '--master', action='store_true', help=docs['master'])
  diff_parser.set_defaults(command=diff)

  return subparsers


def diff(file=None, master=False, **kwargs):
  """ Show diff on current product or all products in workspace

  :param str file: Show diff for file only
  :param bool master: Diff against the master branch
  """
  if file:
    scm_repos = [os.getcwd()]
  else:
    scm_repos = repos()

  optional = len(scm_repos) == 1
  pager = ProductPager(optional=optional)

  for repo in scm_repos:
    with log_exception():
      branch = 'master' if master else None
      output = diff_repo(repo, branch=branch, file=file, return_output=True)
      if output:
        branch = current_branch(repo) if is_git_repo(repo) else None
        pager.write(product_name(repo), output, branch)

  pager.close_and_wait()
