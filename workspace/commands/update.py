from __future__ import absolute_import
import logging
import sys

from workspace.commands import AbstractCommand
from workspace.commands.helpers import expand_product_groups
from workspace.scm import checkout_branch, update_repo, repos, product_name, current_branch,\
    update_branch, parent_branch
from workspace.utils import parallel_call

log = logging.getLogger(__name__)


class Update(AbstractCommand):
    """
    Update current product or all products in workspace

    :param list products: When updating all products, filter by these products or product groups
    """
    alias = 'up'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('raises', True)
        super(Update, self).__init__(*args, **kwargs)

    @classmethod
    def arguments(cls):
        _, docs = cls.docs()
        return [cls.make_args('products', nargs='*', help=docs['products'])]

    def run(self):

        if self.products:
            self.products = expand_product_groups(self.products)

        select_repos = [repo for repo in repos() if not self.products or self.products and product_name(repo) in self.products]

        if not select_repos:
            log.info('No product found')

        elif len(select_repos) == 1:
            _update_repo(select_repos[0], raises=self.raises, quiet=self.quiet)

        else:
            if not all(parallel_call(_update_repo, select_repos).values()):
                sys.exit(1)


def _update_repo(repo, raises=False, quiet=False):
    name = product_name(repo)

    if not quiet:
        log.info('Updating %s', name)

    try:
        branch = current_branch(repo)
        parent = parent_branch(branch)
        if parent:
            checkout_branch(parent, repo)

        update_repo(repo)

        if parent:
            log.info('Rebasing %s', branch)
            checkout_branch(branch, repo_path=repo)
            update_branch(repo=repo, parent=parent)

        return True
    except Exception as e:
        if raises:
            raise
        else:
            log.error('%s: %s', name, e)
            return False
