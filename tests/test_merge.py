from utils.process import run

from workspace.config import config

from test_stubs import temp_git_repo


def test_merge_downstream(wst, capsys):
    config.merge.branches = '1.0.x 2.0.x 3.0.x master'

    with temp_git_repo():
        run('git commit --allow-empty -m dummy-commit')
        run('git branch 3.0.x')
        run('git checkout -b 2.0.x')

        run('git commit --allow-empty -m new-commit')

        wst('merge --downstream')

        branches = run('git branch', return_output=True)
        changes = run('git log --oneline', return_output=True)

    out, _ = capsys.readouterr()

    assert out == """\
Merging 2.0.x into 3.0.x
Pushing 3.0.x
Merging 3.0.x into master
Pushing master
"""

    assert '* master' in branches
    assert 'new-commit' in changes


def test_merge_branch(wst, capsys):
    config.merge.branches = '1.0.x 2.0.x 3.0.x master'

    with temp_git_repo():
        run('git commit --allow-empty -m dummy-commit')

        run('git checkout -b 3.0.x')
        run('git commit --allow-empty -m new-commit')

        run('git checkout master')

        wst('merge 3.0.x')

        changes = run('git log --oneline', return_output=True)

    out, _ = capsys.readouterr()

    assert out == 'Merging 3.0.x into master\n'

    assert 'new-commit' in changes
