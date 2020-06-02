from __future__ import absolute_import
import logging
import os
import re
import sys

import click
import requests
from utils.process import run, silent_run

from workspace.config import config
from workspace.utils import parent_path_with_dir, parent_path_with_file, shortest_id


log = logging.getLogger(__name__)

REMOTE_BRANCH_RE = re.compile(r'^(\*)? *(\((?:HEAD detached at|no branch, rebasing) )?([^ )]+)\)? +\w+ +(?:\[(.+)/([^:\] ]+).*])?')
DEFAULT_REMOTE = 'origin'
UPSTREAM_REMOTE = 'upstream'
USER_REPO_REFERENCE_RE = re.compile(r'^[\w-]+/[\w-]+$')


class SCMError(Exception):
    """ SCM command failed """


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
        silent_run('git add --all ' + files)

    else:
        files = '.'
        silent_run('git add --all ' + files, cwd=repo_path())


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
    """
    Checks out the branch in the given or current repo. Raises on error.

    :param str branch: Branch to checkout. It can be a branch name or remote/branch combo.
                       if remote is provided, it will always set upstream to :meth:`upstream_remote`
                       regardless of the downstream remote, as we always want to track downstream changes to the
                       upstream remote.
    :param str repo_path: Path to repo to run checkout in. Defaults to current.
    """
    name = branch.split('/')[-1] if '/' in branch else None

    cmd = ['git', 'checkout', branch]
    if name:
        cmd.extend(['-B', name])

    silent_run(cmd, cwd=repo_path)

    if name:
        upstream_branch = '{}/{}'.format(upstream_remote(), name)
        if 'remotes/{}'.format(upstream_branch) in all_branches(remotes=True):
            silent_run('git branch --set-upstream-to {}'.format(upstream_branch))
        else:
            click.echo('FYI Can not change upstream tracking branch to {} as it does not exist'.format(upstream_branch))


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


def merge_branch(branch, squash=False, strategy=None):
    cmd = ['git', 'merge', branch]
    if squash:
        cmd.append('--squash')
    if strategy:
        cmd.append('--strategy=' + strategy)

        current = current_branch()
        message = f"Merge branch {branch} into {current} (using strategy {strategy})"
        cmd.append('-m ' + message)

    silent_run(cmd)


def diff_branch(right_branch, left_branch='master', path=None):
    cmd = 'git log %s..%s' % (left_branch, right_branch)

    return run(cmd, cwd=path, return_output=True)


def all_remotes(repo=None):
    """ Return all remotes with default remote as the 1st """
    remotes = _all_remotes(repo=repo)
    if len(remotes) > 1:
        default = default_remote(repo=repo, remotes=remotes)
        return [default] + sorted(set(remotes) - set([default]))
    else:
        return remotes


def _all_remotes(repo=None):
    """ Returns all remotes. """
    remotes_output = silent_run('git remote', cwd=repo, return_output=True)
    remotes = []

    if remotes_output:
        for remote in remotes_output.split('\n'):
            if remote:
                remote = remote.strip()
                remotes.append(remote)

    required_remotes = {
        DEFAULT_REMOTE: 'Your fork of the upstream repo',
        'upstream': 'The upstream repo'
    }
    if len(remotes) >= 2 and not set(required_remotes).issubset(set(remotes)):
        click.echo('Current remotes: {}'.format(' '.join(remotes)))
        click.echo('Only the following remotes are required -- please set them up accordingly:')
        for remote in required_remotes:
            click.echo('  {}: {}'.format(remote, required_remotes[remote]))
        exit(1)

    return remotes


def default_remote(repo=None, remotes=None):
    """ Default remote to take action against, such as push """
    remotes = remotes or all_remotes(repo=repo)
    if len(remotes) > 1:
        return DEFAULT_REMOTE
    else:
        return remotes[0]


def upstream_remote(repo=None, remotes=None):
    """ Upstream remote to track against """
    remotes = remotes or all_remotes(repo=repo)
    if remotes:
        if len(remotes) > 1:
            return UPSTREAM_REMOTE
        else:
            return remotes[0]


def remote_tracking_branch(repo=None):
    remote_output = silent_run('git rev-parse --abbrev-ref --symbolic-full-name @{u}', cwd=repo, return_output=True)

    if 'no upstream' in remote_output:
        return None
    else:
        return remote_output


def all_branches(repo=None, remotes=False, verbose=False):
    """ Returns all branches. The first element is the current branch. """
    cmd = ['git', 'branch']
    if remotes:
        cmd.append('--all')
    if verbose:
        cmd.append('-vv')

    branch_output = silent_run(cmd, cwd=repo, return_output=True)
    branches = []
    remotes = all_remotes(repo=repo)
    up_remote = remotes and upstream_remote(repo=repo, remotes=remotes)
    def_remote = remotes and default_remote(repo=repo, remotes=remotes)

    if branch_output:
        for branch in branch_output.split('\n'):
            branch = branch.strip()
            if branch:
                if verbose:
                    star, detached, local_branch, remote, branch = REMOTE_BRANCH_RE.search(branch).groups()
                    if remote and remotes:
                        # Rightful/tracking remote differs based on parent vs child branch:
                        #   Parent branch = upstream remote
                        #   Child branch = origin remote
                        rightful_remote = (remote == up_remote and '@' not in local_branch
                                           or remote == def_remote and '@' in local_branch)
                        branch = local_branch if rightful_remote else '{}^{}'.format(local_branch, shortest_id(remote, remotes))

                    elif detached:
                        branch = local_branch + '*'

                    else:
                        branch = local_branch

                    if star:
                        branches.insert(0, branch)
                    else:
                        branches.append(branch)

                else:
                    if branch.startswith('*'):
                        branches.insert(0, branch.strip('* '))
                    else:
                        branches.append(branch)

    return branches


def master_branch(repo=None):
    if 'trunk' in all_branches(repo=repo):
        return 'trunk'
    else:
        return 'master'


def current_branch(repo=None):
    branches = all_branches(repo)
    return branches[0] if branches else None


def parent_branch(branch):
    """ Returns the parent branch if available, otherwise None """
    if config.commit.commit_branch_indicator in branch:
        _, parent = branch.rsplit(config.commit.commit_branch_indicator, 1)
        return parent


def update_repo(path=None, quiet=False):
    """ Updates given or current repo to HEAD """
    if not remote_tracking_branch(repo=path):
        if not quiet:
            click.echo('Did not update as remote tracking is not setup for branch')
        return

    branch = current_branch(repo=path)

    if not quiet:
        click.echo('Updating ' + branch)

    remotes = all_remotes(repo=path)
    failed_remotes = []

    for remote in remotes:
        if len(remotes) > 1 and not quiet:
            click.echo('    ... from ' + remote)
        output, success = silent_run('git pull --ff-only --tags {} {}'.format(remote, branch), cwd=path, return_output=2)
        if not success:
            error_match = re.search(r'(?:fatal|ERROR): (.+)', output)
            error = error_match.group(1) if error_match else output
            click.echo('    ...   ' + error.strip(' .'))
            failed_remotes.append(remote)

    if failed_remotes:
        raise SCMError('Failed to pull from remote(s): {}'.format(', '.join(failed_remotes)))


def update_tags(remote, path=None):
    silent_run('git fetch --tags {}'.format(remote), cwd=path)


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


def stat_repo(path=None, return_output=False, with_color=False):
    if with_color:
        cmd = 'git -c color.status=always status'
    else:
        cmd = 'git status'
    return run(cmd, cwd=path, return_output=return_output)


def diff_repo(path=None, branch=None, context=None, return_output=False, name_only=False, color=False):
    cmd = ['git', 'diff']
    if name_only:
        cmd.append('--name-only')
    if color:
        cmd.append('--color')
    if branch:
        cmd.append(branch)
    if context:
        cmd.append(context)

    return run(cmd, cwd=path, return_output=return_output)


def commit_changes(msg):
    """ Commits any modified or new files with given message. Raises on error """
    silent_run(['git', 'commit', '-am', msg])
    click.echo('Committed change.')


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
        log.debug('%s is already checked out.', prod_name)
        checkout_branch('master', checkout_path)
        return update_repo(checkout_path)

    if re.match(r'[\w-]+$', product_url):
        try:
            logging.getLogger('requests').setLevel(logging.WARN)
            response = requests.get(config.checkout.search_api_url, params={'q': product_url}, timeout=10)
            response.raise_for_status()
            results = response.json()['items']
            if not results:
                log.error('No repo matching "%s" found.', product_url)
                sys.exit(1)
            product_url = results[0]['ssh_url']
            click.echo('Using repo url ' + product_url)

        except Exception as e:
            log.error('Could not find repo for %s using %s due to error: ', product_url,
                      config.checkout.search_api_url, e)
            sys.exit(1)

    elif USER_REPO_REFERENCE_RE.match(product_url):
        product_url = config.checkout.user_repo_url % product_url

    is_origin = not config.checkout.origin_user or config.checkout.origin_user + '/' in product_url
    remote_name = DEFAULT_REMOTE if is_origin else UPSTREAM_REMOTE

    silent_run(['git', 'clone', product_url, checkout_path, '--origin', remote_name])

    if not is_origin:
        origin_url = re.sub(r'(\.com[:/])(\w+)(/)', r'\1{}\3'.format(config.checkout.origin_user), product_url)
        silent_run(['git', 'remote', 'add', DEFAULT_REMOTE, origin_url], cwd=checkout_path)


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
