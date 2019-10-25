import os
import pytest

from test_stubs import temp_dir


def test_checkout_with_alias(wst, mock_run):
    with temp_dir() as tmpdir:
        with pytest.raises(SystemExit):
            wst('checkout foobazbar-no-such-repo')

        wst('checkout mzheng-repos')
        assert mock_run.call_count == 4
        mock_run.assert_called_with(
            ['git', 'clone', 'https://github.com/maxzheng/workspace-tools.git', str(tmpdir / 'workspace-tools'), '--origin', 'origin'],
            silent=True)

        wst('checkout clicast')
        mock_run.assert_called_with(
            ['git', 'clone', 'git@github.com:maxzheng/clicast.git', str(tmpdir / 'clicast'), '--origin', 'origin'], silent=True)


def test_checkout_with_http_git(wst):
    with temp_dir():
        wst('checkout https://github.com/maxzheng/clicast.git')
        assert os.path.exists('clicast/README.rst')


def test_checkout_with_git(wst):
    with temp_dir():
        wst('checkout https://github.com/maxzheng/clicast.git')
        assert os.path.exists('clicast/README.rst')


def test_checkout_with_multiple_repos(wst):
    with temp_dir():
        wst('checkout https://github.com/maxzheng/localconfig.git https://github.com/maxzheng/remoteconfig.git')
        assert os.path.exists('localconfig/README.rst')
        assert os.path.exists('remoteconfig/README.rst')
