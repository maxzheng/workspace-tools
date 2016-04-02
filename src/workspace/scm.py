import logging
import os
import re
import shutil
import sys

import requests

from workspace.config import config
from workspace.utils import run, silent_run, parent_path_with_dir


log = logging.getLogger(__name__)

USER_REPO_REFERENCE_RE = re.compile('^[\w-]+/[\w-]+$')
SVN_COMMIT_HEADER_RE = re.compile('^(-+|r\d+\s.*\slines?|\s+)$')
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

  if is_git_repo(repo):
    cmd = ['git', 'log', '--decorate']
    if show_revision:
      cmd.extend(['-U', show_revision])
    if limit:
      cmd.append('-%d' % limit)
    if diff:
      cmd.append('-p')
    if extra_args:
      cmd.extend(extra_args)

  else:
    cmd = ['svn', 'log']
    if show_revision:
      cmd.extend(['-r', show_revision])
    if limit:
      cmd.extend(['-l', str(limit)])
    if diff:
      cmd.append('--diff')
    if extra_args:
      limit_re = re.compile('-\d')
      for i, arg in enumerate(extra_args):
        if limit_re.match(arg):
          extra_args[i] = '-l %s' % arg.lstrip('-')
      cmd.extend(extra_args)
    if to_pager and (show_revision or not limit or limit > 3):
      cmd.extend(['|', os.environ.get('PAGER') or 'less'])

  return run(cmd, return_output=not to_pager, shell=to_pager, cwd=repo)


def add_files(repo=None, files=None):
  if not repo:
    repo = git_repo_path()

  if files:
    files = ' '.join(files)
  else:
    files = '.'

  silent_run('git add --all ' + files, cwd=repo)


def repo_check():
  if not is_repo():
    log.error('This should be run from within a product checkout')
    sys.exit(1)


def git_repo_check(hint='This command only supports git repo.'):
  if not is_git_repo():
    log.error('Not a git repository. %s', hint)
    if is_svn_repo():
      log.info('Please consider using git-svn for your svn repo as git is AWESOME!! :)')
    sys.exit(1)


def extract_commit_msgs(output, is_git=True):
  """ Returns a list of commit msgs from the given output. """
  msgs = []

  if output:
    msg = []

    for line in output.split('\n'):
      if not line:
        continue

      if is_git:
        is_commit_msg = line.startswith(' ') or not line
      else:
        is_commit_msg = not(SVN_COMMIT_HEADER_RE.match(line))

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


def is_git_svn_repo(path=None):
  """ Checks if given or current path is a git svn repo """
  repo_path = git_repo_path(path)
  return repo_path and os.path.isfile(os.path.join(repo_path, '.git', 'svn', '.metadata'))


def is_repo(path=None):
  return repo_path(path)


def repo_path(path=None):
  # Last element is longest path, which is the current repo in a nested repo situation.
  return sorted([git_repo_path(path), svn_repo_path(path)])[-1]


def is_svn_repo(path=None):
  svn_repo = svn_repo_path(path)
  return svn_repo and svn_repo == repo_path(path)


def svn_repo_path(path=None):
  """ Checks if given or current path is a svn repo """
  return parent_path_with_dir('.svn', path)


def is_git_repo(path=None):
  git_repo = git_repo_path(path)
  return git_repo and git_repo == repo_path(path)


def git_repo_path(path=None):
  """ Checks if given or current path is a git repo """
  return parent_path_with_dir('.git', path)


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


def update_branch(repo=None):
  silent_run('git rebase master', cwd=repo)


def remove_branch(branch, raises=False):
  """ Removes branch """
  silent_run(['git', 'branch', '-D', branch], raises=raises)


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


def current_branch(repo=None):
  return all_branches(repo)[0]


def update_repo(path=None):
  """ Updates given or current repo to HEAD """

  if is_git_svn_repo(path):
    silent_run('git svn rebase', cwd=path)
  elif is_git_repo(path):
    silent_run('git pull --rebase', cwd=path)
  else:
    silent_run('svn update --ignore-externals', cwd=path)


def push_repo(path=None):
  if is_git_svn_repo(path):
    silent_run('git svn dcommit')
  else:
    silent_run('git push')


def stat_repo(path=None, return_output=False):
  if is_git_repo(path):
    cmd = 'git status'
  else:
    cmd = 'svn status'

  return run(cmd, cwd=path, return_output=return_output)


def diff_repo(path=None, branch=None, file=None, return_output=False, name_only=False):
  if is_git_repo(path):
    cmd = ['git', 'diff']
    if branch:
      cmd.append(branch)
    if file:
      cmd.append(file)
    if name_only:
      cmd.append('--name-only')

  else:
    cmd = ['svn', 'diff']
    if file:
      cmd.append(file)

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


def svn_revision_range(repo=None, num_commmits=1):
  cmd = ['svn', 'log', '-l', str(num_commmits)]

  if repo and (repo.startswith('http://') or repo.startswith('https://') or repo.startswith('svn+ssh://')):
    cmd.append(repo)
    repo = None

  output = silent_run(cmd, cwd=repo, return_output=True, raises=False)

  if output:
    try:
      output = output.split('\n')
      svn_revision_re = re.compile('r(\d+) ')
      head_revision = svn_revision_re.match(output[1]).group(1)
      for i in range(len(output) - 1, -1, -1):
        match = svn_revision_re.match(output[i])
        if match:
          from_revision = match.group(1)
          break
      return int(from_revision), int(head_revision)
    except Exception:
      return None, None


def clone_svn_repo(product_url, checkout_path, clone_svn_commits):
  prod_name = product_name(product_url)

  log.info('Cloning last %d commit(s) for svn repo using git-svn.', clone_svn_commits)
  if clone_svn_commits > 1:
    log.info('This might take some time...')

  from_revision, head_revision = svn_revision_range(product_url, clone_svn_commits)

  if not head_revision:
    raise Exception('Unable to get latest revision from %s' % product_url)

  workspace_path = os.path.dirname(checkout_path)
  revision_range = '-r%d:%s' % (from_revision, head_revision)

  clone_cmd = ['git', 'svn', 'clone', revision_range]
  if product_url.endswith('/trunk'):
    clone_cmd.extend(['-T', 'trunk', product_url[:-6], checkout_path])
  else:
    clone_cmd.extend([product_url, checkout_path])

  silent_run(clone_cmd, cwd=workspace_path)

  gitignore_file = os.path.join(workspace_path, prod_name, GITIGNORE_FILE)
  if not os.path.exists(gitignore_file):
    with open(gitignore_file, 'w') as fp:
      fp.write(GITIGNORE)
    log.info('Created %s/%s. Please check that in so git ignores build/temp files.', prod_name, os.path.basename(gitignore_file))


def checkout_product(product_url, checkout_path):
  """ Checks out the product from url. Raises on error """
  product_url = product_url.strip('/')

  clone_svn_commits = config.checkout.use_gitsvn_to_clone_svn_commits
  prod_name = product_name(product_url)

  if os.path.exists(checkout_path):
    log.debug('%s is already checked out. Updating...', prod_name)
    if is_git_repo(checkout_path):
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
      log.error('Could not find repo for %s using %s due to error: ', product_url, config.checkout.search_api_url, e)
      sys.exit(1)

  elif USER_REPO_REFERENCE_RE.match(product_url):
    product_url = config.checkout.user_repo_url % product_url

  if clone_svn_commits and not product_url.endswith('.git'):
    try:
      return clone_svn_repo(product_url, checkout_path, clone_svn_commits)
    except Exception as e:
      log.exception('Falling back to svn as git-svn clone failed: %s', e)
      if os.path.exists(checkout_path):
        shutil.rmtree(checkout_path)

  if product_url.endswith('.git'):
    silent_run(['git', 'clone', product_url, checkout_path])
  else:
    silent_run(['svn', 'checkout', product_url, checkout_path])


def checkout_files(files, repo_path=None):
  """ Checks out the given list of files. Raises on error. """
  if is_git_repo(repo_path):
    silent_run(['git', 'checkout'] + files, cwd=repo_path)
  else:
    silent_run(['svn', 'revert'] + files, cwd=repo_path)


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
