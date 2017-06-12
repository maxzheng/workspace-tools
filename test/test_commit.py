from workspace.commands.commit import Commit


def test_branch_for_msg():
    assert 'fix' == Commit()._branch_for_msg('Fix a big bad bug', 1)
    assert 'fix-a-big' == Commit()._branch_for_msg('Fix a big bad bug', 2)
    assert 'fix-a-big-bad' == Commit()._branch_for_msg('Fix a big bad bug', 3)

    assert 'fix-a-big-bad-bug' == Commit()._branch_for_msg('Fix a big bad bug', 3, ['fix-a-big-bad'])

    assert 'fix-flake8-errors' == Commit()._branch_for_msg('Fix flake8 errors', 3)

    assert 'use-or-or-or-blah-23242-last' == Commit()._branch_for_msg('Use / or | or . or blah_23242_last ignored(&(&*2324', 3)

    assert 'remove-readme-rst' == Commit()._branch_for_msg('Remove README.rst symlink', 3)

    assert 'publish-version-0-4-2' == Commit()._branch_for_msg('Publish version 0.4.2', 3)

    assert 'fix-test' == Commit()._branch_for_msg('Fix test', 3)
    assert 'fix-test' == Commit()._branch_for_msg('Fix test to', 3)
    assert 'fix-test-to-work' == Commit()._branch_for_msg('Fix test to work', 3)
