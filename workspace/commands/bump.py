from __future__ import absolute_import
import logging

import click

from bumper import BumperDriver

from workspace.commands import AbstractCommand
from workspace.commands.helpers import expand_product_groups
from workspace.config import config
from workspace.scm import repo_check, current_branch


log = logging.getLogger(__name__)


class Bump(AbstractCommand):
    """
      Bump dependency versions in requirements.txt, pinned.txt, or any specified file.

      :param str names: Only bump dependencies that match the name.
                        Name can be a product group name defined in workspace.cfg.
                        To bump to a specific version instead of latest, append version to name
                        (e.g. requests==1.2.3 or 'requests>=1.2.3'). When > or < is used, be sure to quote.
      :param int test: Run tests.
      :param bool push: Push the change. Use with --test to test before pushing.
      :param bool add: Add the `names` to the requirements file if they don't exist.
      :param str msg: Summary commit message
      :param str/list file: Requirement file to bump. Defaults to requirements.txt or pinned.txt
                            that are set by bump.requirement_files in workspace.cfg.
      :param dict bumper_models: List of classes that implements :class:`bumper.cars.AbstractBumper`
                                 Defaults to :class:`bumper.cars.RequirementsBumper`
      :param bool force: Force a bump even when certain bump requirements are not met.
      :param bool dry_run: Perform a dry run by printing out the changes only without making changes.
      :param dict kwargs: Additional args from argparse
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('show_filter', True)
        super(Bump, self).__init__(*args, **kwargs)

    @classmethod
    def arguments(cls):
        _, docs = cls.docs()
        return ([
            cls.make_args('names', nargs='*', help=docs['names']),
            cls.make_args('--add', action='store_true', help=docs['add']),
            cls.make_args('--force', action='store_true', help=docs['force']),
            cls.make_args('-m', '--msg', help=docs['msg']),
            cls.make_args('--file', help=docs['file']),
            cls.make_args('-n', '--dry-run', action='store_true', help=docs['dry_run'])
          ], [
            cls.make_args('-t', '--test', action='count', help=docs['test']),
            cls.make_args('-p', '--push', action='store_true', help=docs['push']),
          ])

    def run(self):
        """
          :return: Tuple with 3 elements: A map of file to bump message, commit message, and list of :class:`Bump`
        """
        repo_check()

        self.commander.run('update')

        if not self.names:
            self.names = []

        filter_requirements = expand_product_groups(self.names)

        if self.show_filter and filter_requirements:
            click.echo('Only bumping: {}'.format(' '.join(filter_requirements)))

        if isinstance(self.file, list):
            requirement_files = self.file
        elif self.file:
            requirement_files = [self.file]
        else:
            requirement_files = config.bump.requirement_files.strip().split()

        bumper = BumperDriver(requirement_files, bumper_models=self.bumper_models, full_throttle=self.force, detail=True,
                              test_drive=self.dry_run)
        messages, bumps = bumper.bump(filter_requirements, required=self.add, show_summary=False)
        commit_msg = None

        try:
            if messages:
                summary_msgs = []
                detail_msgs = []
                for m in sorted(messages.values()):
                    splits = m.split('\n', 1)
                    summary_msgs.append(splits[0])
                    if len(splits) == 2:
                        detail_msgs.append(splits[1])

                commit_msg = '\n\n'.join(summary_msgs + detail_msgs)

                if self.msg:
                    commit_msg = self.msg + '\n\n' + commit_msg
                else:
                    config.commit.auto_branch_from_commit_words = 1

                if not self.dry_run:
                    self.commander.run('commit', msg=commit_msg, files=list(messages.keys()))
                    config.commit.auto_branch_from_commit_words = 2  # Restore it for unit tests

        except Exception:
            bumper.reverse()
            raise

        if bumps:
            if self.test:
                click.echo('Running tests')
                self.commander.run('test', return_output=False, test_dependents=self.test > 1)

            if not self.dry_run:
                if self.push:
                    branch = current_branch()
                    self.commander.run('push', branch=branch)

        return messages, commit_msg, bumps
