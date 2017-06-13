from __future__ import absolute_import
import logging
import os
import re
import sys

import requests

from workspace.config import config
from workspace.utils import run, silent_run, parent_path_with_dir, parent_path_with_file


log = logging.getLogger(__name__)

USER_REPO_REFERENCE_RE = re.compile('^[\w-]+/[\w-]+$')
GITIGNORE_FILE = '.gitignore'
GITIGNORE = """\
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]

# C extensions
*.so

# Distribution / packaging
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
*/.coverage.*
.cache
nosetests.xml
coverage.xml

# Translations
*.mo
*.pot

# Django stuff:
*.log

# Sphinx documentation
docs/_build/

# PyBuilder
target/
"""


def workspace_path():
    """ Guess the workspace path based on if we are in a repo or not. """
    repo_path = is_repo()
    if repo_path:
        return os.path.dirname(repo_path)
    else:
        return os.getcwd()


def commit_logs(limit=None, repo=None, diff=False, show_revision=None, extra_args=None, to_pager=False):
    if show_revision:
        diff = True
        if not limit:
            limit = 1

    cmd = ['git', 'log', '--decorate']
    if show_revision:
        cmd.extend(['-U', show_revision])
    if limit:
        cmd.append('-%d' % limit)
    if diff:
        cmd.append('-c')
    if extra_args:
        cmd.extend(extra_args)

    return run(cmd, return_output=not to_pager, shell=to_pager, cwd=repo)


def add_files(files=None):
    if files:
        files = ' '.join(files)
    else:
        files = '.'

    silent_run('git add --all ' + files)


def repo_check():
    if not is_repo():
        log.error('This should be run from within a product checkout')
        sys.exit(1)


def extract_commit_msgs(output, is_git=True):
    """ Returns a list of commit msgs from the given output. """
    msgs = []

    if output:
        msg = []

        for line in output.split('\n'):
            if not line:
                continue

            is_commit_msg = line.startswith(' ') or not line

            if is_commit_msg:
                if is_git and line.startswith('    '):
                    line = line[4:]
                msg.append(line)
            elif msg:
                msgs.append('\n'.join(msg))
                msg = []

        if msg:
            msgs.append('\n'.join(msg))

    return msgs


def is_repo(path=None):
    """ Check if we are inside of a git repo. """
    return repo_path(path=path)


def repo_path(path=None):
    """ Return the git repo path with .git by looking at current dir and its parent dirs. """
    return parent_path_with_dir('.git', path=path)


def is_project(path=None):
    """ Check if we are inside of a project. """
    return project_path(path=path)


def project_path(path=None):
    """ Return the project path with tox.ini by looking at the current dir and its parent dirs. """
    return parent_path_with_file('tox.ini', path=path)


def product_repos():
    """ Product repos for the current workspace. """
    return repos(workspace_path())


def repos(dir=None):
    """ Returns a list of repos either for the given directory or current directory or in sub-directories. """
    repos = []
    cwd = dir or os.getcwd()

    if is_repo(cwd):
        repos.append(repo_path(cwd))
        return repos

    for dir in os.listdir(cwd):
        path = os.path.join(cwd, dir)
        if os.path.isdir(path) and is_repo(path):
            repos.append(path)

    return repos


def checkout_branch(branch, repo_path=None):
    """ Checks out the branch in the given or current repo. Raises on error. """
    silent_run(['git', 'checkout', branch], cwd=repo_path)


def create_branch(branch, from_branch=None):
    """ Creates a branch from the current branch. Raises on error """
    cmd = ['git', 'checkout', '-b', branch]
    if from_branch:
        cmd.append(from_branch)
    silent_run(cmd)


def update_branch(repo=None, parent='master'):
    silent_run('git rebase {}'.format(parent), cwd=repo)


def remove_branch(branch, raises=False, remote=False, force=False):
    """ Removes branch """
    run(['git', 'branch', '-D' if force else '-d', branch], raises=raises)

    if remote:
        silent_run(['git', 'push', default_remote(), '--delete', branch], raises=raises)


def rename_branch(branch, new_branch):
    silent_run(['git', 'branch', '-m', branch, new_branch])


def merge_branch(branch, squash=False):
    cmd = ['git', 'merge', branch]
    if squash:
        cmd.append('--squash')
    silent_run(cmd)


def diff_branch(right_branch, left_branch='master', path=None):
    cmd = 'git log %s..%s' % (left_branch, right_branch)

    return run(cmd, cwd=path, return_output=True)


def all_remotes(repo=None):
    """ Returns all remotes. """
    remotes_output = silent_run('git remote', cwd=repo, return_output=True)
    remotes = []

    if remotes_output:
        for remote in remotes_output.split('\n'):
            if remote:
                remote = remote.strip()
                remotes.append(remote)

    return remotes


def default_remote(repo=None):
    return all_remotes(repo=repo)[0]


def remote_tracking_branch(repo=None):
    remote_output = silent_run('git rev-parse --abbrev-ref --symbolic-full-name @{u}', cwd=repo, return_output=True)

    if 'no upstream' in remote_output:
        return None
    else:
        return remote_output


def all_branches(repo=None):
    """ Returns all branches. The first element is the current branch. """
    branch_output = silent_run('git branch', cwd=repo, return_output=True)
    branches = []

    if branch_output:
        for branch in branch_output.split('\n'):
            branch = branch.strip()
            if branch.startswith('*'):
                branches.insert(0, branch.strip('*').strip())
            elif branch:
                branches.append(branch)

    return branches


def master_branch(repo=None):
    if 'trunk' in all_branches(repo=repo):
        return 'trunk'
    else:
        return 'master'


def current_branch(repo=None):
    return all_branches(repo)[0]


def parent_branch(branch):
    """ Returns the parent branch if available, otherwise None """
    if config.commit.commit_branch_indicator in branch:
        _, parent = branch.rsplit(config.commit.commit_branch_indicator, 1)
        return parent


def update_repo(path=None):
    """ Updates given or current repo to HEAD """
    if not remote_tracking_branch(repo=path):
        return

    branch = current_branch(repo=path)

    for remote in all_remotes(repo=path):
        silent_run('git pull {} {}'.format(remote, branch), cwd=path)


def push_repo(path=None, force=False, remote=None, branch=None):
    push_opts = []

    if force:
        push_opts.append('--force')

    if not remote_tracking_branch(repo=path):
        push_opts.append('--set-upstream ' + remote)
    elif remote:
        push_opts.append(remote)

    if branch:
        push_opts.append(branch)

    silent_run('git push ' + ' '.join(push_opts), cwd=path)


def stat_repo(path=None, return_output=False):
    cmd = 'git status'
    return run(cmd, cwd=path, return_output=return_output)


def diff_repo(path=None, branch=None, context=None, return_output=False, name_only=False):
    cmd = ['git', 'diff']
    if branch:
        cmd.append(branch)
    if context:
        cmd.append(context)
    if name_only:
        cmd.append('--name-only')

    return run(cmd, cwd=path, return_output=return_output)


def commit_changes(msg):
    """ Commits any modified or new files with given message. Raises on error """
    silent_run(['git', 'commit', '-am', msg])
    log.info('Committed change.')


def local_commit(msg=None, amend=False, empty=False):
    cmd = ['git', 'commit']
    if amend:
        cmd.append('--amend')
    if empty:
        cmd.append('--allow-empty')
    if msg:
        cmd.extend(['-m', msg])
    run(cmd)


def checkout_product(product_url, checkout_path):
    """ Checks out the product from url. Raises on error """
    product_url = product_url.strip('/')

    prod_name = product_name(product_url)

    if os.path.exists(checkout_path):
        log.debug('%s is already checked out. Updating...', prod_name)
        checkout_branch('master', checkout_path)
        return update_repo(checkout_path)

    if re.match('[\w-]+$', product_url):
        try:
            logging.getLogger('requests').setLevel(logging.WARN)
            response = requests.get(config.checkout.search_api_url, params={'q': product_url}, timeout=10)
            response.raise_for_status()
            results = response.json()['items']
            if not results:
                log.error('No repo matching "%s" found.', product_url)
                sys.exit(1)
            product_url = results[0]['ssh_url']
            log.info('Using repo url %s', product_url)
        except Exception as e:
            log.error('Could not find repo for %s using %s due to error: ', product_url,
                      config.checkout.search_api_url, e)
            sys.exit(1)

    elif USER_REPO_REFERENCE_RE.match(product_url):
        product_url = config.checkout.user_repo_url % product_url

    silent_run(['git', 'clone', product_url, checkout_path])


def checkout_files(files, repo_path=None):
    """ Checks out the given list of files. Raises on error. """
    silent_run(['git', 'checkout'] + files, cwd=repo_path)


def hard_reset(to_commit):
    run(['git', 'reset', '--hard', to_commit])


def product_name(product_url=None):
    if not product_url:
        product_url = repo_path()

    product_url = product_url.strip('/')

    if product_url.endswith('.git'):
        name = product_url[:-4]
    elif product_url.endswith('_trunk') or product_url.endswith('/trunk'):
        name = product_url[:-6]
    else:
        name = product_url

    return os.path.basename(name)


def product_checkout_path(product_url, workspace_dir=None):
    return product_path(product_name(product_url), workspace_dir)


def product_path(name, workspace_dir=None):
    if not workspace_dir:
        workspace_dir = workspace_path()

    return os.path.join(workspace_dir, name)


def repo_url(path=None, name='origin', action='push'):
    """
      :param str path: Local repo path
      :param str source: Remote name
      :param str action: Action for the corresponding URL
      :return: Remote url for repo or None if not found
    """
    cmd = 'git remote -v'

    output = run(cmd, cwd=path, return_output=True)

    for line in output.split('\n'):
        if line:
            remote_name, remote_url, remote_action = line.split()
            if remote_name == name and action in remote_action:
                return remote_url
