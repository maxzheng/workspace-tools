from contextlib import contextmanager
import os
import shutil
from tempfile import mkdtemp

from workspace.utils import run


@contextmanager
def temp_dir():
    try:
        cwd = os.getcwd()
        dtemp = mkdtemp()
        os.chdir(dtemp)

        yield dtemp

    finally:
        os.chdir(cwd)
        shutil.rmtree(dtemp)


@contextmanager
def temp_git_repo():
    with temp_dir() as dir:
        run('git init')
        yield dir


@contextmanager
def temp_remote_git_repo():
    with temp_dir() as dir:
        run('git clone https://github.com/maxzheng/remoteconfig.git')
        repo_dir = os.path.join(dir, 'remoteconfig')
        os.chdir(repo_dir)
        yield repo_dir
