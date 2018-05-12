from contextlib import contextmanager
import os
from pathlib import Path
import shutil
from tempfile import mkdtemp

from utils.process import run


@contextmanager
def temp_dir():
    try:
        cwd = os.getcwd()
        dtemp = mkdtemp()
        os.chdir(dtemp)

        yield Path(dtemp)

    finally:
        os.chdir(cwd)
        shutil.rmtree(dtemp)


@contextmanager
def temp_git_repo(name=None):
    with temp_dir() as tmpdir:
        if name:
            os.makedirs(name)
            os.chdir(name)

        run('git init')

        yield (tmpdir / name) if name else tmpdir


@contextmanager
def temp_remote_git_repo():
    with temp_dir() as tmpdir:
        run('git clone https://github.com/maxzheng/remoteconfig.git')
        repo_dir = tmpdir / 'remoteconfig'
        os.chdir(repo_dir)
        yield repo_dir
