from workspace.scripts.ansible_hostmanager import main
from workspace.config import config


def test_hostmanager(cli_runner, tmpdir, mock_run):
    if 'ansible' in config:
        config._parser.remove_section('ansible')
        config._dot_keys.pop(config._to_dot_key('ansible'))

    result = cli_runner.invoke_and_assert_exit(1, main, ['list'])
    assert result.output == 'Please set path to Ansible hosts file by running: ah set-hosts <PATH>\n'

    hosts_file = tmpdir.join('hosts')
    config.save = lambda: False
    result = cli_runner.invoke_and_assert_exit(0, main, ['set-hosts', str(hosts_file)])

    hosts_file.write('[app_server]\napp1 ansible_host=1.2.3.4\napp2')
    result = cli_runner.invoke_and_assert_exit(0, main, ['list'])
    assert result.output == 'app1  1.2.3.4  [app_server, all]\napp2           [app_server, all]\n'

    result = cli_runner.invoke_and_assert_exit(0, main, ['ssh', 'app1'])
    mock_run.assert_called_with(['ssh', '1.2.3.4'])

    result = cli_runner.invoke_and_assert_exit(0, main, ['ssh', 'app2'])
    mock_run.assert_called_with(['ssh', 'app2'])

    result = cli_runner.invoke_and_assert_exit(0, main, ['ssh', 'app'])
    mock_run.assert_called_with(['ssh', '1.2.3.4'])
