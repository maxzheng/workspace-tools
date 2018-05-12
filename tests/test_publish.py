from mock import Mock, call

from utils.process import run

from test_stubs import temp_git_repo


def test_publish(wst, monkeypatch):
    silent_run_mock = Mock()
    config_mock = Mock()
    monkeypatch.setattr('workspace.commands.publish.LocalConfig', config_mock)
    monkeypatch.setattr('workspace.commands.publish.silent_run', silent_run_mock)

    config_mock().get.side_effect = ['repo', 'user', 'pass']

    with temp_git_repo() as cwd:
        wst('setup --product')
        run('git commit --allow-empty -m dummy-commit')

        wst('publish')

    assert silent_run_mock.call_args_list == [
        call('rm -rf dist/*', cwd=str(cwd), shell=True),
        call('python setup.py sdist', cwd=str(cwd)),
        call('twine upload -r "pypi" -u "user" -p "pass" dist/*', cwd=str(cwd), shell=True)]
