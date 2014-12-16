import logging
import os
import re
import sys

from workspace.commands.update import update
from workspace.commands.commit import commit
from workspace.scm import repo_path
from workspace.utils import log_exception, silent_run


log = logging.getLogger(__name__)
new_version = None  # Doesn't work if it is in bump_version

SETUP_FILE = 'setup.py'


def setup_publish_parser(subparsers):
  parser = subparsers.add_parser('publish', description=publish.__doc__, help=publish.__doc__)
  group = parser.add_mutually_exclusive_group()
  group.add_argument('--minor', action='store_true', help='Perform a minor publish by bumping the minor version')
  group.add_argument('--major', action='store_true', help='Perform a major publish by bumping the major version')
  parser.set_defaults(command=publish)

  return parser


def publish(minor=False, major=False, **kwargs):
  """ Bumps version in setup.py (defaults to patch), commits all changes, builds a source distribution, and uploads with twine. """

  silent_run('rm -rf dist/*', shell=True)

  with log_exception(exit=1):
    update(raises=True)

    new_version = bump_version(major, minor)
    commit(msg='Bump version to ' + new_version, push=True)

    log.info('Building source distribution')
    silent_run('python setup.py sdist')

    log.info('Uploading with twine')
    silent_run('twine upload dist/*', shell=True)


def bump_version(major=False, minor=False):
  """ Bumps the patch version unless major/minor is True """
  if not os.path.exists(SETUP_FILE):
    log.error(SETUP_FILE + 'does not exist.')
    sys.exit(1)

  def replace_version(match):
    global new_version

    version_parts = match.group(2).split('.')
    i = 0 if major else (1 if minor else 2)

    while len(version_parts) < i + 1:
      version_parts.append(0)

    for j in range(i+1, len(version_parts)):
      version_parts[j] = '0'

    version_parts[i] = str(int(version_parts[i]) + 1)
    new_version = '.'.join(version_parts)

    return 'version=' + match.group(1) + new_version + match.group(1)

  content = re.sub('version\s*=\s*([\'"])(.*)[\'"]', replace_version, open(SETUP_FILE).read())

  with open(SETUP_FILE, 'w') as fp:
    fp.write(content)

  if not new_version:
    log.error('Failed to find "version=" in setup.py to bump version')
    sys.exit(1)

  return new_version
