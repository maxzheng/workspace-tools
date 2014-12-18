import os
import pytest
import subprocess


@pytest.mark.parametrize("script", ['wst'])
def test_script_sanity(script):

  try:
    subprocess.check_output([script, '-h'], stderr=subprocess.STDOUT)
  except subprocess.CalledProcessError as e:
    print e.output
    assert e.returncode == 0
