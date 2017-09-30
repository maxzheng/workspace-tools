from __future__ import absolute_import
import os
import logging

from workspace.commands import AbstractCommand
from workspace.commands.helpers import ProductPager
from workspace.scm import stat_repo, repos, product_name, all_branches, is_repo

log = logging.getLogger(__name__)


class Status(AbstractCommand):
    """ Show status on current product or all products in workspace """
    alias = 'st'

    def run(self):

        try:
            scm_repos = repos()
            in_repo = is_repo(os.getcwd())
            optional = len(scm_repos) == 1
            pager = ProductPager(optional=optional)

            for repo in scm_repos:
                stat_path = os.getcwd() if in_repo else repo
                output = stat_repo(stat_path, True)
                nothing_to_commit = 'nothing to commit' in output and 'Your branch is ahead of' not in output

                branches = all_branches(repo)
                child_branches = [b for b in branches if '@' in b]

                if len(child_branches) >= 1 or len(scm_repos) == 1:
                    show_branches = branches if len(scm_repos) == 1 else child_branches
                    if nothing_to_commit:
                        output = '# Branches: %s' % ' '.join(show_branches)
                        nothing_to_commit = False
                    elif len(show_branches) > 1:
                        output = '# Branches: %s\n#\n%s' % (' '.join(show_branches), output)

                if output and not nothing_to_commit:
                    pager.write(product_name(repo), output)
        finally:
            pager.close_and_wait()
