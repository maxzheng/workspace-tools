from workspace.commands.commit import branch_for_msg


def test_branch_for_msg():
  assert 'fix' == branch_for_msg('Fix a big bad bug', 1)
  assert 'fix-a-big' == branch_for_msg('Fix a big bad bug', 2)
  assert 'fix-a-big-bad' == branch_for_msg('Fix a big bad bug', 3)

  assert 'fix-a-big-bad-bug' == branch_for_msg('Fix a big bad bug', 3, ['fix-a-big-bad'])

  assert 'fix-flake8-errors' == branch_for_msg('Fix flake8 errors', 3)

  assert 'use-or-or-or-blah-23242-last' == branch_for_msg('Use / or | or . or blah_23242_last ignored(&(&*2324', 3)

  assert 'remove-readme-rst' == branch_for_msg('Remove README.rst symlink', 3)

  assert 'publish-version-0-4-2' == branch_for_msg('Publish version 0.4.2', 3)

  assert 'fix-test' == branch_for_msg('Fix test', 3)
  assert 'fix-test' == branch_for_msg('Fix test to', 3)
  assert 'fix-test-to-work' == branch_for_msg('Fix test to work', 3)
