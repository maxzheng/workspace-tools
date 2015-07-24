import os
import pytest

from mock import patch, Mock

from bumper.utils import PyPI

from workspace.scm import stat_repo, all_branches, commit_logs

from test_stubs import temp_dir, temp_git_repo, temp_remote_git_repo


@pytest.mark.parametrize('command,exception', [('diff', None), ('log', SystemExit), ('status', None)])
def test_sanity(run, command, exception):
  with temp_dir():
    if exception:
      with pytest.raises(exception):
        run(command)
    else:
      run(command)

  with temp_git_repo():
    run(command)


def test_bump(run, monkeypatch):
  monkeypatch.setattr('workspace.commands.review.Review.reviewers_for_product', Mock(return_value=(None, None)))
  monkeypatch.setattr('workspace.commands.review.Review.id_for_branch', Mock(return_value=None))
  monkeypatch.setattr('workspace.commands.review.Review.create', Mock())

  with temp_dir():
    with pytest.raises(SystemExit):
      run('bump')

  with temp_remote_git_repo():
    # No requirements.txt
    if os.path.exists('requirements.txt'):
      os.unlink('requirements.txt')
    with pytest.raises(SystemExit):
      run('bump')

    # All requirements are up to date
    with open('requirements.txt', 'w') as fp:
      fp.write('localconfig\nrequests')
    assert ({}, None, []) == run('bump')

    # All requirements are outdated
    with open('requirements.txt', 'w') as fp:
      fp.write('# Comment for localconfig\nlocalconfig==0.0.1\n# Comment for requests\nrequests<0.1')
    msgs, commit_msg, bumps = run('bump')
    file, msg = msgs.items()[0]
    version = PyPI.latest_package_version('localconfig')
    assert 'requirements.txt' == file

    expected_msg = 'Require localconfig==%s' % version
    assert expected_msg == msg[:len(expected_msg)]
    assert expected_msg == commit_msg[:len(expected_msg)]

    with open('requirements.txt') as fp:
      requirements = fp.read()
      assert '# Comment for localconfig\nlocalconfig==%s\n# Comment for requests\nrequests<0.1\n' % version == requirements


def test_cleanrun(run):
  with temp_dir():
    run('clean')


def test_commit(run):
  with temp_dir():
    with pytest.raises(SystemExit):
      run('commit')

  with temp_git_repo():
    with pytest.raises(SystemExit):
      run('commit "no files to commit"')

    with open('new_file', 'w') as fp:
      fp.write('Hello World')
    assert 'new_file' in stat_repo(return_output=True)

    run('commit "Add new file" --branch master')

    assert 'working directory clean' in stat_repo(return_output=True)
    assert 'Hello World' == open('new_file').read()

    with open('new_file', 'w') as fp:
      fp.write('New World')

    run('commit "Update file" --branch updated')

    assert ['updated', 'master'] == all_branches()

    run('commit --move moved')

    assert ['updated', 'master', 'moved'] == all_branches()

    run('commit --discard')

    assert ['master', 'moved'] == all_branches()

    logs = commit_logs()
    assert 'new file' in logs
    assert 1 == len(filter(None, logs.split('commit')))


def test_test(run):
  with temp_dir():
    with pytest.raises(SystemExit):
      run('test')

  if 'PYTESTARGS' in os.environ:
    del os.environ['PYTESTARGS']

  with temp_git_repo():
    with pytest.raises(SystemExit):
      run('test')
    run('setup --product')

    pass_test = 'def test_pass():\n  assert True'
    fail_test = 'def test_fail():\n  assert False'

    with open('test/test_pass.py', 'w') as fp:
      fp.write(pass_test)
    commands = run('test')
    assert 'py27' in commands
    assert 'tox' in commands['py27']

    with open('test/test_fail.py', 'w') as fp:
      fp.write(fail_test + '\n' + pass_test)
    with pytest.raises(SystemExit):
      run('test')

    commands = run('test test/test_pass.py')
    assert 'py27' in commands
    assert 'py.test' in commands['py27']

    os.utime('requirements.txt', None)
    commands = run('test -k test_pass')
    assert 'py27' in commands
    assert 'tox' in commands['py27']

    with pytest.raises(SystemExit):
      run('test style')
    with open('test/test_fail.py', 'w') as fp:
      fp.write(fail_test + '\n\n\n' + pass_test)
    assert 'style' in run('test style')

    os.unlink('test/test_fail.py')
    assert 'coverage' in run('test coverage')
    assert os.path.exists('coverage.xml')
    assert os.path.exists('htmlcov/index.html')


@patch('workspace.commands.push.push_repo')
def test_push(push_repo, run):
  with temp_dir():
    with pytest.raises(SystemExit):
      run('push')

  with temp_remote_git_repo():
    run('push')

    with open('new_file', 'w') as fp:
      fp.write('Hello World')
    assert 'new_file' in stat_repo(return_output=True)

    run('commit "Add new file" --branch=new_file')

    run('push')

    assert ['master'] == all_branches()
    assert "ahead of 'origin/master' by 1 commit." in stat_repo(return_output=True)
