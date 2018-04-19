from __future__ import absolute_import
import logging
import os

from workspace.commands import AbstractCommand
from workspace.commands.helpers import ProductPager
from workspace.scm import diff_repo, repos, product_name, current_branch, parent_branch
from workspace.utils import log_exception

log = logging.getLogger(__name__)


class Diff(AbstractCommand):
    """
      Show diff on current product or all products in workspace

      :param str context: Show diff for context (i.e. branch or file)
      :param bool parent: Diff against the parent branch. If there is not parent, defaults to master.
      :param bool name_only: List file names only. Git only.
    """
    alias = 'di'

    @classmethod
    def arguments(cls):
        _, docs = cls.docs()
        return [
          cls.make_args('context', nargs='?', help=docs['context']),
          cls.make_args('-p', '--parent', action='store_true', help=docs['parent']),
          cls.make_args('-l', '--name-only', action='store_true', help=docs['name_only'])
        ]

    def run(self):
        if self.context:
            scm_repos = [os.getcwd()]
        else:
            scm_repos = repos()

        optional = len(scm_repos) == 1
        pager = ProductPager(optional=optional)

        for repo in scm_repos:
            with log_exception():
                cur_branch = current_branch(repo)
                branch = (parent_branch(cur_branch) or 'master') if self.parent else None
                color = not pager.pager or 'less' in pager.pager.args
                output = diff_repo(repo, branch=branch, context=self.context, return_output=True,
                                   name_only=self.name_only, color=color)
                if output:
                    pager.write(product_name(repo), output, cur_branch)

        pager.close_and_wait()
