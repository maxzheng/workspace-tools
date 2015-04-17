import os
import pytest

from workspace.commands.checkout import checkout
from test_stubs import temp_dir


def test_checkout_with_alias():
  with temp_dir():
    with pytest.raises(SystemExit):
      checkout(['foobazbar-no-such-repo'])

    checkout(['mzheng-repos'])
    checkout(['clicast'])


def test_checkout_with_http_git():
  with temp_dir():
    checkout(['https://github.com/maxzheng/clicast.git'])
    assert os.path.exists('clicast/README.rst')


def test_checkout_with_git():
  with temp_dir():
    checkout(['git@github.com:maxzheng/clicast.git'])
    assert os.path.exists('clicast/README.rst')


def test_checkout_with_svn():
  with temp_dir():
    checkout(['https://github.com/maxzheng/localconfig/trunk'])
    assert os.path.exists('localconfig/README.rst')


def test_checkout_with_multiple_repos():
  with temp_dir():
    checkout(['https://github.com/maxzheng/localconfig.git', 'https://github.com/maxzheng/remoteconfig.git'])
    assert os.path.exists('localconfig/README.rst')
    assert os.path.exists('remoteconfig/README.rst')


