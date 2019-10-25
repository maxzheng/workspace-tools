import shlex

from mock import Mock
import pytest

from workspace.config import config
from workspace.controller import Commander

config._last_source = None  # Don't read from user config for tests


@pytest.fixture()
def wst(monkeypatch):
    def _run(cmd):
        monkeypatch.setattr('sys.argv', shlex.split('wst --debug ' + cmd))
        return Commander().run()
    return _run


@pytest.fixture()
def mock_run(monkeypatch):
    r = Mock()
    monkeypatch.setattr('utils_core.process.run', r)
    monkeypatch.setattr('workspace.utils.run', r)
    monkeypatch.setattr('workspace.scm.run', r)
    monkeypatch.setattr('workspace.commands.test.run', r)
    return r
