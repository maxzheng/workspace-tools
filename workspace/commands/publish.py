from __future__ import absolute_import
import getpass
import logging
import os
import re
import sys

import click
from utils.process import run, silent_run

from localconfig import LocalConfig
from workspace.commands import AbstractCommand
from workspace.commands.helpers import ToxIni
from workspace.scm import repo_check, repo_path, commit_logs, extract_commit_msgs
from six.moves import range


log = logging.getLogger(__name__)
new_version = None  # Doesn't work if it is in bump_version
PUBLISH_VERSION_PREFIX = 'Publish version '
IGNORE_CHANGE_RE = re.compile(r'^(?:Update changelog|Fix tests?)\s*$', flags=re.IGNORECASE)
VERSION_RE = re.compile(r'version\s*=\s*([\'"])(.*)[\'"]')


class Publish(AbstractCommand):
    """
        Bumps version in setup.py (defaults to patch), writes out changelog, builds a source distribution,
        and uploads with twine.

        :param str repo: Repository to publish to
        :param bool minor: Perform a minor publish by bumping the minor version
        :param bool major: Perform a major publish by bumping the major version
    """
    @classmethod
    def arguments(cls):
        _, docs = cls.docs()
        return [
          cls.make_args('-r', '--repo', default='pypi', help=docs['repo']),
          cls.make_args('--minor', action='store_true', help=docs['minor']),
          cls.make_args('--major', action='store_true', help=docs['major'])
        ]

    def run(self):
        if self.minor and self.major:
            log.error('--minor and --major are mutually exclusive, please use only one.')
            return

        repo_check()

        pypirc = LocalConfig('~/.pypirc')
        repository = pypirc.get(self.repo, 'repository')
        username = pypirc.get(self.repo, 'username')
        password = pypirc.get(self.repo, 'password')
        repo_title = 'PyPI' if self.repo == 'pypi' else self.repo.title()

        if not repository:
            log.error('Please add repository / username to [%s] section in ~/.pypirc', self.repo)
            sys.exit(1)

        if not username:
            username = getpass.getuser('{} Username: '.format(repo_title))
            if not username:
                sys.exit()

        if not password:
            password = getpass.getpass('{} Password: '.format(repo_title))
            if not password:
                sys.exit()

        self.commander.run('update')

        published_version, changes = self.changes_since_last_publish()

        if not changes:
            click.echo('There are no changes since last publish')
            sys.exit(0)

        silent_run('rm -rf dist/*', shell=True, cwd=repo_path())

        if self.major or self.minor:
            new_version, setup_file = self.bump_version(major=self.major, minor=self.minor)
            major_minor = 'major' if self.major else 'minor'
            self.commander.run('commit', msg=f'Bump {major_minor} version', files=[setup_file], push=2,
                               skip_style_check=True)

        else:
            current_version, setup_file = self.get_version()

            # Previously, we publish the current version in setup.py, so need to bump it first before
            # we can publish a new version.
            if published_version == current_version:
                new_version, setup_file = self.bump_version()
            else:
                new_version = current_version

        changelog_file = self.update_changelog(new_version, changes, self.minor or self.major)

        tox = ToxIni()
        envs = [e for e in tox.envlist if e != 'style']

        if envs:
            env = envs[0]
            if len(envs) > 1:
                log.debug('Found multiple default envs in tox.ini, will use first one to build: %s', env)

        else:
            click.echo('Odd, there are no default envs in tox.ini, so we can not build.')
            sys.exit(1)

        envdir = tox.envdir(env)
        python = os.path.join(envdir, 'bin', 'python')

        click.echo('Building source/built distribution')

        silent_run(f'{python} setup.py sdist bdist_wheel', cwd=repo_path())

        click.echo('Uploading to ' + repo_title)

        try:
            run('twine upload -r "{repo}" -u "{username}" -p "{password}" dist/*'.format(
                repo=self.repo,
                username=username,
                password=password), shell=True, cwd=repo_path(), silent=2)

        except Exception:
            sys.exit(1)

        self.bump_version()
        self.commander.run('commit', msg=PUBLISH_VERSION_PREFIX + new_version, push=2, files=[setup_file, changelog_file],
                           skip_style_check=True)

    def changes_since_last_publish(self):
        commit_msgs = extract_commit_msgs(commit_logs(limit=100, repo=repo_path()), True)
        changes = []
        published_version = None

        for msg in commit_msgs:
            if msg.startswith(PUBLISH_VERSION_PREFIX):
                published_version = msg.split(PUBLISH_VERSION_PREFIX)[-1]
                break
            if len(msg) < 7 or IGNORE_CHANGE_RE.match(msg):
                continue
            changes.append(msg)

        return published_version, changes

    def update_changelog(self, new_version, changes, skip_title_change=False):
        """
        :param str new_version: New version
        :param list[str] changes: List of changes
        :param bool skip_title_change: Skip title change
        :returns: Path to changelog file
        """
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

        return changelog_file

    def get_version(self):
        """ Get current version and setup.py file """
        setup_file = os.path.join(repo_path(), 'setup.py')
        match = VERSION_RE.search(open(setup_file).read())

        if not match:
            log.error('Failed to find "version=" in setup.py to get version')
            sys.exit(1)

        return match.group(2), setup_file

    def bump_version(self, major=False, minor=False):
        """
        Bump the version (defaults to patch) in setup.py

        :param bool major: Bump major version only
        :param bool minor: Bump minor version only
        """
        setup_file = os.path.join(repo_path(), 'setup.py')

        if not os.path.exists(setup_file):
            log.error(setup_file + ' does not exist.')
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

        content = VERSION_RE.sub(replace_version, open(setup_file).read())

        with open(setup_file, 'w') as fp:
            fp.write(content)

        if not new_version:
            log.error('Failed to find "version=" in setup.py to bump version')
            sys.exit(1)

        return new_version, setup_file
