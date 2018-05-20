import shlex

from mock import Mock
import pytest

from workspace.controller import Commander


@pytest.fixture()
def wst(monkeypatch):
    def _run(cmd):
        monkeypatch.setattr('sys.argv', shlex.split('wst --debug ' + cmd))
        return Commander().run()
    return _run


@pytest.fixture()
def mock_run(monkeypatch):
    r = Mock()
    monkeypatch.setattr('utils.process.run', r)
    monkeypatch.setattr('workspace.utils.run', r)
    monkeypatch.setattr('workspace.scm.run', r)
    monkeypatch.setattr('workspace.commands.test.run', r)
    return r
