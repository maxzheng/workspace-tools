from workspace.commands.helpers import expand_product_groups


def test_expand_product_groups(monkeypatch):
    monkeypatch.setattr('workspace.commands.helpers.product_groups',
                        lambda: {'ws': ['workspace-tools', 'clicast', 'localconfig', 'remoteconfig'],
                                 'config': ['localconfig', 'remoteconfig']})

    assert expand_product_groups(['name1', 'name2']) == ['name1', 'name2']
    assert expand_product_groups(['ws', 'name2']) == sorted(['workspace-tools', 'clicast', 'localconfig', 'remoteconfig', 'name2'])
    assert expand_product_groups(['ws', '-localconfig']) == sorted(['workspace-tools', 'clicast', 'remoteconfig'])
    assert expand_product_groups(['ws', '-config']) == sorted(['workspace-tools', 'clicast'])
