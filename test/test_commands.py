import os
import pytest

from workspace.commands.bump import bump
from workspace.scm import local_commit, add_files, remove_branch, checkout_branch
from workspace.utils import run

from test_utils import temp_dir, temp_git_repo, temp_remote_git_repo

def test_bump():
  with temp_dir():
    with pytest.raises(SystemExit):
      bump()

  with temp_remote_git_repo():
    # No requirements.txt
    if os.path.exists('requirements.txt'):
      os.unlink('requirements.txt')
    with pytest.raises(SystemExit):
      bump()

    # All requirements are up to date
    with open('requirements.txt', 'w') as fp:
      fp.write('localconfig\nrequests')
    assert {} == bump()

    # All requirements are outdated
    with open('requirements.txt', 'w') as fp:
      fp.write('localconfig==0.0.1\nrequests<0.1')
    file, msg = bump().items()[0]
    assert 'requirements.txt' == file
    assert 'localconfig==' in msg
    assert 'requests<=' in msg

    # Exisitng bump branch
    with pytest.raises(SystemExit):
      bump()

    checkout_branch('master')
    remove_branch('bump')

    # Only one is outdated
    with open('requirements.txt', 'w') as fp:
      fp.write('localconfig==0.0.1\nrequests>0.1')
    file, msg = bump().items()[0]
    assert 'requirements.txt' == file
    assert 'localconfig==' in msg
    assert 'requests' not in msg

    checkout_branch('master')
    remove_branch('bump')

    # Bump to a specific version
    with open('requirements.txt', 'w') as fp:
      fp.write('localconfig==0.0.1\nrequests>0.1')
    req = 'requests>=1'
    file, msg = bump([req]).items()[0]
    assert 'requirements.txt' == file
    assert req in msg
    assert 'localconfig' not in msg

    checkout_branch('master')
    remove_branch('bump')

    # Bump to a bad version
    with open('requirements.txt', 'w') as fp:
      fp.write('localconfig==0.0.1\nrequests>0.1')
    req = 'requests>=100'
    with pytest.raises(SystemExit):
      bump([req])
