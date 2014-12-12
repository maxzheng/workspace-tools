import logging

from workspace.commands.helpers import ProductPager
from workspace.scm import stat_repo, repos, product_name_for_repo, all_branches, is_git_repo

log = logging.getLogger(__name__)


def setup_status_parser(subparsers):
  status_parser = subparsers.add_parser('status', aliases=['st'], description=status.__doc__, help=status.__doc__)
  status_parser.set_defaults(command=status)

  return status_parser


def status(**kwargs):
  """ Show status on current product or all products in workspace """

  try:
    optional = len(repos()) == 1
    pager = ProductPager(optional=optional)
    for repo in repos():
      output = stat_repo(repo, True)
      nothing_to_commit = 'nothing to commit' in output and 'Your branch is ahead of' not in output

      branches = all_branches(repo) if is_git_repo(repo) else []

      if len(branches) > 1:
        if nothing_to_commit:
          output = '# Branches: %s' % ' '.join(branches)
          nothing_to_commit = False
        elif len(branches) > 1:
          output = '# Branches: %s\n#\n%s' % (' '.join(branches), output)

      if output and not nothing_to_commit:
          pager.write(product_name_for_repo(repo), output)
  except Exception as e:
    log.error(e)
  finally:
    pager.close_and_wait()
