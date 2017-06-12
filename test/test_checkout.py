import os
import pytest

from test_stubs import temp_dir


def test_checkout_with_alias(run):
    with temp_dir():
        with pytest.raises(SystemExit):
            run('checkout foobazbar-no-such-repo')

        run('checkout mzheng-repos')
        assert os.path.exists('workspace-tools')

        run('checkout clicast')
        assert os.path.exists('clicast')


def test_checkout_with_http_git(run):
    with temp_dir():
        run('checkout https://github.com/maxzheng/clicast.git')
        assert os.path.exists('clicast/README.rst')


def test_checkout_with_git(run):
    with temp_dir():
        run('checkout git@github.com:maxzheng/clicast.git')
        assert os.path.exists('clicast/README.rst')


def test_checkout_with_multiple_repos(run):
    with temp_dir():
        run('checkout https://github.com/maxzheng/localconfig.git https://github.com/maxzheng/remoteconfig.git')
        assert os.path.exists('localconfig/README.rst')
        assert os.path.exists('remoteconfig/README.rst')
