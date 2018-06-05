from mock import Mock, call
from pathlib import Path
import pytest

from utils.process import run

from workspace.scm import commit_logs

from test_stubs import temp_git_repo


def test_publish(wst, monkeypatch):
    silent_run_mock = Mock()
    config_mock = Mock()
    monkeypatch.setattr('workspace.commands.publish.LocalConfig', config_mock)
    monkeypatch.setattr('workspace.commands.publish.silent_run', silent_run_mock)
    monkeypatch.setattr('workspace.commands.publish.run', silent_run_mock)

    config_mock().get.side_effect = ['repo', 'user', 'pass'] * 10

    with temp_git_repo() as cwd:
        wst('setup --product')

        # Patch release
        run('git commit --allow-empty -m change1')
        run('git commit --allow-empty -m change2')

        wst('publish')

        changes = open('docs/CHANGELOG.rst').read()
        assert changes == """\
Version 0.0.1
================================================================================

* change2
* change1
"""

        setup_py = open('setup.py').read().split('\n')
        assert setup_py[5] == "    version='0.0.2',"

        python = Path('~/.virtualenvs').expanduser() / Path(cwd).name / 'bin' / 'python'

        assert silent_run_mock.call_args_list == [
            call('rm -rf dist/*', cwd=str(cwd), shell=True),
            call(f'{python} setup.py sdist bdist_wheel', cwd=str(cwd)),
            call('twine upload -r "pypi" -u "user" -p "pass" dist/*', cwd=str(cwd), shell=True, silent=2)]

        # No changes
        with pytest.raises(SystemExit):
            wst('publish')

        # Minor release
        run('git commit --allow-empty -m feature1')

        wst('publish --minor')

        assert 'Bump minor version' in commit_logs()

        changes = open('docs/CHANGELOG.rst').read()
        print(changes)
        assert changes == """\
Version 0.1.0
================================================================================

* feature1

Version 0.0.1
================================================================================

* change2
* change1
"""
        setup_py = open('setup.py').read().split('\n')
        assert setup_py[5] == "    version='0.1.1',"

        # Major release
        run('git commit --allow-empty -m feature2')

        wst('publish --major')

        assert 'Bump major version' in commit_logs()

        changes = open('docs/CHANGELOG.rst').read()
        print(changes)
        assert changes == """\
Version 1.0.0
================================================================================

* feature2

Version 0.1.0
================================================================================

* feature1

Version 0.0.1
================================================================================

* change2
* change1
"""
        setup_py = open('setup.py').read().split('\n')
        assert setup_py[5] == "    version='1.0.1',"

        # Already published patch version will bump before publish
        run('git commit --allow-empty -m "Publish version 1.0.1"', shell=True)
        run('git commit --allow-empty -m bugfix1')

        wst('publish')

        changes = open('docs/CHANGELOG.rst').read()
        assert changes == """\
Version 1.0.2
================================================================================

* bugfix1

Version 1.0.0
--------------------------------------------------------------------------------

* feature2

Version 0.1.0
================================================================================

* feature1

Version 0.0.1
================================================================================

* change2
* change1
"""

        setup_py = open('setup.py').read().split('\n')
        assert setup_py[5] == "    version='1.0.3',"
