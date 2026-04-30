import os
import pytest
import subprocess
import sys

from utils.process import run


@pytest.mark.parametrize("script", ['wst'])
def test_script_sanity(script):
    # Get script path from the virtualenv bin directory
    venv_bin = os.path.dirname(sys.executable)
    script_path = os.path.join(venv_bin, script)

    try:
        run([script_path, '-h'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(e.output)
        assert e.returncode == 0
