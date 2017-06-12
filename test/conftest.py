import shlex

import pytest

from workspace.controller import Commander


@pytest.fixture()
def run(monkeypatch):
    def _run(cmd):
        monkeypatch.setattr('sys.argv', shlex.split('wst ' + cmd))
        return Commander().run()
    return _run
