import logging
import sys

from bumper import BumperDriver

from workspace.commands.commit import commit
from workspace.commands.update import update
from workspace.commands.helpers import expand_product_groups
from workspace.config import config
from workspace.scm import checkout_branch, all_branches, repo_check, is_git_repo
from workspace.utils import split_doc


log = logging.getLogger(__name__)


def setup_bump_parser(subparsers):
  doc, docs = split_doc(bump.__doc__)

  bump_parser = subparsers.add_parser('bump', description=doc, help=doc)
  bump_parser.add_argument('names', nargs='*', help=docs['names'])
  bump_parser.add_argument('--add', '--require', action='store_true', help=docs['add'])
  bump_parser.add_argument('-a', '--append', action='store_true', help=docs['append'])
  bump_parser.add_argument('-m', '--msg', help=docs['msg'])
  bump_parser.add_argument('--file', help=docs['file'])
  bump_parser.add_argument('--force', action='store_true', help=docs['force'])
  bump_parser.add_argument('-n', '--dry-run', action='store_true', help=docs['dry_run'])
  bump_parser.set_defaults(command=bump)

  return bump_parser


def bump(names=None, add=False, append=False, msg=None, file=None, bumper_models=None, force=False, dry_run=False, **kwargs):
  """
    Bump dependency versions in requirements.txt, pinned.txt, or any specified file.

    :param str names: Only bump dependencies that match the name.
                      Name can be a product group name defined in workspace.cfg.
                      To bump to a specific version instead of latest, append version to name
                      (i.e. requests==1.2.3 or 'requests>=1.2.3'). When > or < is used, be sure to quote.
    :param bool add: Add the `names` to the requirements file if they don't exist.
    :param bool append: Append bump changes to current branch and update existing rb if any (from .git/config)
    :param str msg: Summary commit message
    :param str/list file: Requirement file to bump. Defaults to requirements.txt or pinned.txt
                          that are set by bump.requirement_files in workspace.cfg.
    :param dict bumper_models: List of classes that implements :class:`bumper.cars.AbstractBumper`
                               Defaults to :class:`bumper.cars.RequirementsBumper`
    :param bool force: Force a bump even when certain bump requirements are not met.
    :param bool dry_run: Performs a dry run by printing out the changes instead of committing/creating an rb
    :param dict kwargs: Additional args from argparse
    :return: A map of file to commit message
  """
  repo_check()

  if not append and is_git_repo():
    if not dry_run and 'bump' in all_branches():
      log.error('There is already a "bump" branch. Please commit or delete it first before doing another bump.')
      sys.exit(1)
    checkout_branch('master')

  if not names:
    names = []

  filter_requirements = expand_product_groups(names)

  if filter_requirements:
    log.info('Only bumping: %s', ' '.join(filter_requirements))

  if isinstance(file, list):
    requirement_files = file
  elif file:
    requirement_files = [file]
  else:
    requirement_files = config.bump.requirement_files.strip().split()

  update(raises=True)

  bumper = BumperDriver(requirement_files, bumper_models=bumper_models, full_throttle=force, detail=True, test_drive=dry_run)
  messages = bumper.bump(filter_requirements, required=add, show_summary=not is_git_repo(), **kwargs)
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

      if msg:
        commit_msg = msg + '\n\n' + commit_msg

      if not dry_run and is_git_repo():
        branch = None if append else 'bump'
        commit(msg=commit_msg, branch=branch)
  except Exception:
    bumper.reverse()
    raise

  return messages, commit_msg
