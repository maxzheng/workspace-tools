from __future__ import absolute_import
import os
import logging

from workspace.commands import AbstractCommand
from workspace.commands.helpers import ProductPager
from workspace.scm import stat_repo, repos, product_name, all_branches, is_repo, all_remotes

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
                output = stat_repo(stat_path, return_output=True, with_color=True)
                nothing_to_commit = ('nothing to commit' in output
                                     and 'Your branch is ahead of' not in output
                                     and 'Your branch is behind' not in output)

                branches = all_branches(repo, verbose=True)
                child_branches = [b for b in branches if '@' in b]

                if len(child_branches) >= 1 or len(scm_repos) == 1:
                    show_branches = branches if len(scm_repos) == 1 else child_branches
                    remotes = all_remotes() if len(scm_repos) == 1 else []
                    remotes = '\n# Remotes: {}'.format(' '.join(remotes)) if len(remotes) > 1 else ''

                    if nothing_to_commit:
                        output = '# Branches: {}{}'.format(' '.join(show_branches), remotes)
                        nothing_to_commit = False
                    elif len(show_branches) > 1:
                        output = '# Branches: {}{}\n#\n{}'.format(' '.join(show_branches), remotes, output)

                if output and not nothing_to_commit:
                    pager.write(product_name(repo), output)
        finally:
            pager.close_and_wait()
