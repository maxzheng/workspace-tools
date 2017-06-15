from __future__ import absolute_import
import logging
import os
import shutil
from time import time

import click

from workspace.commands import AbstractCommand
from workspace.commands.helpers import expand_product_groups
from workspace.config import config
from workspace.scm import workspace_path, product_name, repos, stat_repo, all_branches, repo_path
from workspace.utils import silent_run

log = logging.getLogger(__name__)


class Clean(AbstractCommand):
    """ Clean workspace by removing build, dist, and .pyc files """

    def run(self):

        repo = repo_path()
        if repo:
            click.echo('Removing build/dist folders')
            silent_run("rm -rf build dist docs/_build */activate", cwd=repo, shell=True)

            click.echo('Removing *.pyc files')
            silent_run("find . -type d \( -path '*/.tox' -o -path '*/mppy-*' \) -prune -o -name *.pyc -exec rm {} \;", cwd=repo, shell=True)

        else:
            path = workspace_path()
            click.echo('Cleaning {}'.format(path))

            if config.clean.remove_products_older_than_days or config.clean.remove_all_products_except:
                keep_time = 0
                keep_products = []

                if config.clean.remove_all_products_except:
                    click.echo('Removing all products except: %s' % config.clean.remove_all_products_except)
                    keep_products = expand_product_groups(config.clean.remove_all_products_except.split())

                if config.clean.remove_products_older_than_days:
                    click.echo('Removing products older than %s days' % config.clean.remove_products_older_than_days)
                    keep_time = time() - config.clean.remove_products_older_than_days * 86400

                removed_products = []

                for repo in repos(path):
                    name = product_name(repo)
                    modified_time = os.stat(repo).st_mtime
                    if name not in keep_products or keep_time and modified_time < keep_time:
                        status = stat_repo(repo, return_output=True)
                        if not status or 'nothing to commit' in status and 'working directory clean' in status and len(all_branches(repo)) <= 1:
                            shutil.rmtree(repo)
                            removed_products.append(name)
                        else:
                            click.echo('  - Skipping "%s" as it has changes that may not be committed' % name)

                if removed_products:
                    click.echo('Removed ' + ', '.join(removed_products))
