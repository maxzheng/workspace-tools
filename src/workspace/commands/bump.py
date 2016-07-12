import logging

from bumper import BumperDriver

from workspace.commands import AbstractCommand
from workspace.commands.helpers import expand_product_groups
from workspace.commands.review import Review
from workspace.config import config
from workspace.scm import repo_check, is_git_repo, product_name, current_branch


log = logging.getLogger(__name__)


class Bump(AbstractCommand):
  """
    Bump dependency versions in requirements.txt, pinned.txt, or any specified file.

    :param str names: Only bump dependencies that match the name.
                      Name can be a product group name defined in workspace.cfg.
                      To bump to a specific version instead of latest, append version to name
                      (i.e. requests==1.2.3 or 'requests>=1.2.3'). When > or < is used, be sure to quote.
    :param int test: Run tests. Results will be posted to ReviewBoard if --rb is used.
    :param bool rb: Create or update existing RB after commit. Existing RB is looked up in .git/config.
    :param bool push: Wait for 'Ship It' from RB (unless --skip-rb is used) and push the bump (git only)
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
        cls.make_args('-r', '--rb', action='store_true', help=docs['rb']),
        cls.make_args('-p', '--push', action='store_true', help=docs['push']),
      ])

  def run(self):
    """
      :return: Tuple with 3 elements: A map of file to bump message, commit message, and list of :class:`Bump`
    """
    repo_check()

    self.commander.run('update')

    if not self.msg:
      config.commit.auto_branch_from_commit_words = 1

    if not self.names:
      self.names = []

    filter_requirements = expand_product_groups(self.names)

    if self.show_filter and filter_requirements:
      log.info('Only bumping: %s', ' '.join(filter_requirements))

    if isinstance(self.file, list):
      requirement_files = self.file
    elif self.file:
      requirement_files = [self.file]
    else:
      requirement_files = config.bump.requirement_files.strip().split()

    bumper = BumperDriver(requirement_files, bumper_models=self.bumper_models, full_throttle=self.force, detail=True, test_drive=self.dry_run)
    messages, bumps = bumper.bump(filter_requirements, required=self.add, show_summary=not is_git_repo())
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

        if not self.dry_run and is_git_repo():
          self.commander.run('commit', msg=commit_msg, files=messages.keys())

    except Exception:
      bumper.reverse()
      raise

    if bumps:
      tests = {}

      if self.test:
        log.info('Running tests')
        tests[product_name()] = self.commander.run('test', return_output=self.rb, test_dependents=self.test > 1)

      if not self.dry_run:
        if self.rb and commit_msg and self.commander.command('review') != Review:
          reviewer_groups = set()
          reviewers = set()

          for lib in bumps.keys():
            g, r = self.commander.command('review').reviewers_for_product(lib)
            if g:
              reviewer_groups.update(g)
            if r:
              reviewers.update(r)
            log.debug('Reviewers for %s: %s %s', lib, g, r)

          self.commander.run('review', publish=self.push, files=messages.keys(), description=commit_msg, test=tests,
                             skip_prereview=True, reviewer_groups=reviewer_groups, reviewers=reviewers)

        if self.push and is_git_repo():
          branch = current_branch()
          if self.rb:
            self.commander.run('wait', review=True, in_background=True)
          self.commander.run('push', branch=branch)

    return messages, commit_msg, bumps
