from __future__ import absolute_import
import getpass
import logging
import os
import re
import sys

from localconfig import LocalConfig
from workspace.commands import AbstractCommand
from workspace.scm import repo_check, repo_path, commit_logs, extract_commit_msgs
from workspace.utils import silent_run
from six.moves import range


log = logging.getLogger(__name__)
new_version = None  # Doesn't work if it is in bump_version
PUBLISH_VERSION_PREFIX = 'Publish version '
IGNORE_CHANGE_RE = re.compile('^(?:Update changelog|Fix tests?)\s*$', flags=re.IGNORECASE)


class Publish(AbstractCommand):
    """
      Bumps version in setup.py (defaults to patch), writes out changelog, builds a source distribution, and uploads with twine.

      :param bool minor: Perform a minor publish by bumping the minor version
      :param bool major: Perform a major publish by bumping the major version
    """
    @classmethod
    def arguments(cls):
        _, docs = cls.docs()
        return [
          cls.make_args('--minor', action='store_true', help=docs['minor']),
          cls.make_args('--major', action='store_true', help=docs['major'])
        ]

    def run(self):
        if self.minor and self.major:
            log.error('--minor and --major are mutually exclusive, please use only one.')
            return

        repo_check()

        pypirc = LocalConfig('~/.pypirc')
        if not pypirc.pypi or not pypirc.pypi.repository:
            log.error('Please add repository / username to [pypi] section in ~/.pypirc')
            sys.exit(1)

        if not pypirc.pypi.username:
            pypirc.pypi.username = getpass.getuser('PyPI Username: ')
            if not pypirc.pypi.username:
                sys.exit()

        if not pypirc.pypi.password:
            pypirc.pypi.password = getpass.getpass('PyPI Password: ')
            if not pypirc.pypi.password:
                sys.exit()

        self.commander.run('update')

        changes = self.changes_since_last_publish()

        if not changes:
            log.info('There are no changes since last publish')
            sys.exit(0)

        silent_run('rm -rf dist/*', shell=True, cwd=repo_path())

        new_version = self.bump_version()
        self.update_changelog(new_version, changes, self.minor or self.major)

        self.commander.run('commit', msg=PUBLISH_VERSION_PREFIX + new_version, push=True)

        log.info('Building source distribution')
        silent_run('python setup.py sdist', cwd=repo_path())

        log.info('Uploading')

        silent_run('twine upload -u "{username}" -p "{password}" dist/*'.format(**dict(list(pypirc.pypi))), shell=True, cwd=repo_path())

    def changes_since_last_publish(self):
        commit_msgs = extract_commit_msgs(commit_logs(limit=100, repo=repo_path()), True)
        changes = []

        for msg in commit_msgs:
            if msg.startswith(PUBLISH_VERSION_PREFIX):
                break
            if len(msg) < 7 or IGNORE_CHANGE_RE.match(msg):
                continue
            changes.append(msg)

        return changes

    def update_changelog(self, new_version, changes, skip_title_change=False):
        docs_dir = os.path.join(repo_path(), 'docs')
        if not os.path.isdir(docs_dir):
            os.makedirs(docs_dir)

        changelog_file = os.path.join(docs_dir, 'CHANGELOG.rst')
        existing_changes = os.path.exists(changelog_file) and open(changelog_file).read()
        major_title = '=' * 80
        minor_title = '-' * 80

        with open(changelog_file, 'w') as fp:
            fp.write('Version %s' % new_version + '\n')
            fp.write(major_title + '\n\n')

            for change in changes:
                fp.write('* %s\n' % (change.replace('\n', '\n  ')))

            if existing_changes:
                fp.write('\n')
                if not skip_title_change:
                    existing_changes = existing_changes.replace(major_title, minor_title, 1)
                fp.write(existing_changes)

    def bump_version(self):
        """
          Bump the version (defaults to patch) in setup.py
        """
        setup_file = os.path.join(repo_path(), 'setup.py')

        if not os.path.exists(setup_file):
            log.error(setup_file + ' does not exist.')
            sys.exit(1)

        def replace_version(match):
            global new_version

            version_parts = match.group(2).split('.')
            i = 0 if self.major else (1 if self.minor else 2)

            while len(version_parts) < i + 1:
                version_parts.append(0)

            for j in range(i+1, len(version_parts)):
                version_parts[j] = '0'

            version_parts[i] = str(int(version_parts[i]) + 1)
            new_version = '.'.join(version_parts)

            return 'version=' + match.group(1) + new_version + match.group(1)

        content = re.sub('version\s*=\s*([\'"])(.*)[\'"]', replace_version, open(setup_file).read())

        with open(setup_file, 'w') as fp:
            fp.write(content)

        if not new_version:
            log.error('Failed to find "version=" in setup.py to bump version')
            sys.exit(1)

        return new_version
