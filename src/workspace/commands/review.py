import logging
import sys

from workspace.commands import AbstractCommand
from workspace.scm import is_git_repo, repo_check

log = logging.getLogger(__name__)


class Review(AbstractCommand):
  """
    Create or update a ReviewBoard.

    Note: This is an abtract command, though may change in the future.
    To use review command, please implement all the abstract methods using the arguments.

    :param str files: [svn only] List of files to use for RB.
    :param int rb_id: RB id to update. For git, this is auto looked up in .git/config
    :param str description: [svn only] Description for RB
    :param bool push: Wait for "Ship It" for RB and push the change. This implies --publish.
    :param int test: Update testing done section with results from tests. Repeat twice to test dependents too (-tt)
  """
  alias = 'rb'

  @classmethod
  def arguments(cls):
    _, docs = cls.docs()
    return ([
        cls.make_args('files', nargs='*', help=docs['files']),
        cls.make_args('-r', '--rb-id', type=int, help=docs['rb_id']),
        cls.make_args('-m', '--description', help=docs['description']),
        cls.make_args('-P', '--publish', action='store_true', help='Publish the RB'),
      ], [
        cls.make_args('-t', '--test', action='count', help=docs['test']),
        cls.make_args('-p', '--push', action='store_true', help=docs['push'])
      ])

  def run(self):

    repo_check()

    if not self.skip_prereview:
      self.prereview_test()

    tests = None

    if self.test:

      if isinstance(self.test, int):
        log.info('Running tests')
        tests = self.commander.run('test', return_output=True, test_dependents=self.test > 1)
      else:
        tests = self.test

      success, tests = self.commander.command('test').summarize(tests)

      if not success:
        sys.exit(1)

      if not isinstance(tests, list):
        tests = [tests]

      self.tests = '\n'.join(filter(lambda t: 'No tests' not in t, tests))

    if not self.rb_id and is_git_repo():
      self.rb_id = self.id_for_branch()

    if self.rb_id:
      self.update()

    else:
      if not self.reviewer_groups:
        self.reviewer_groups = set()
      if not self.reviewers:
        self.reviewers = set()
      g, r = self.reviewers_for_product()
      if g:
        self.reviewer_groups.update(g)
      if r:
        self.reviewers.update(r)
      self.create()

    if self.push:
      if is_git_repo():
        self.commander.run('wait', push=True, rb_id=self.rb_id, in_background=True)
      else:
        log.error('--push is not supported for svn yet.')

  def prereview_test(self):
    """
      Run local tests before creating the RB, such as doing a style check.
      It should run with silent=2 (silent but show output on error).
    """
    if self.commander.command('test').supports_style_check():
      log.info('Running style check')
      self.commander.run('test', env_or_file=['style'], silent=2)

  @classmethod
  def id_for_branch(cls, branch=None):
    """ Returns the RB ID for the current or given branch. """
    raise NotImplementedError('Not implemented. Please implement Review.id_for_branch() in a subclass')

  @classmethod
  def reviewers_for_product(cls, product=None):
    """ Tuple of set(reviewer_groups), set(reviewers) for the current or given product. """
    raise NotImplementedError('Not implemented. Please implement Review.reviewers_for_product() in a subclass')

  def update(self):
    """ Updates the given self.rb_id based on args. Raises on error """
    raise NotImplementedError('Not implemented. Please implement Review.update() in a subclass')

  def create(self):
    """ Creates a RB based on args. Raises on error """
    raise NotImplementedError('Not implemented. Please implement Review.create() in a subclass')
