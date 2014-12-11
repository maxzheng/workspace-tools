import os
import pytest
import subprocess32 as subprocess

BLACKLIST = []


def get_list_of_scripts():
  test_dir = os.path.abspath(os.path.dirname(__file__))
  bin_dir = os.path.abspath(os.path.join(test_dir, '../bin/'))

  result = []

  for filename in os.listdir(bin_dir):
    if filename in BLACKLIST:
      print "Skipping %s, it's blacklisted" % filename
      continue

    path_to_file = os.path.join(bin_dir, filename)

    if os.path.isfile(path_to_file) and os.access(path_to_file, os.X_OK):
      result.append(path_to_file)

  return result


@pytest.mark.parametrize("script", get_list_of_scripts())
def test_script_sanity(script):

  try:
    subprocess.check_output([script, '-h'], stderr=subprocess.STDOUT)
  except subprocess.CalledProcessError as e:
    print e.output
    assert e.returncode == 0
