import re

from utils.process import run

from test_stubs import temp_git_repo


def test_status(wst, capsys):
    with temp_git_repo():
        wst('status')
        out, _ = capsys.readouterr()
        assert out == '# Branches: \n'

        run('git commit --allow-empty -m Dummy')
        wst('status')
        out, _ = capsys.readouterr()
        assert out == '# Branches: master\n'

        run('git checkout -b feature')
        wst('status')
        out, _ = capsys.readouterr()
        assert out == '# Branches: feature master\n'

        run('git checkout HEAD^0')
        wst('status')
        out, _ = capsys.readouterr()
        assert re.fullmatch('# Branches: \w+\* feature master\n', out)
