import pytest
import subprocess

from utils.process import run


@pytest.mark.parametrize("script", ['wst'])
def test_script_sanity(script):

    try:
        run([script, '-h'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(e.output)
        assert e.returncode == 0
