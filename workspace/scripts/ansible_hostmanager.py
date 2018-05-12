from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
import click
import sys

from tabulate import tabulate
from utils.process import run

from workspace.config import config


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def main():
    pass


@main.command()
@click.argument('partial_name', required=False)
def list(partial_name):
    """ List all hosts where name contains optional partial name """
    inventory = _get_inventory()

    hosts = []
    pattern = f'*{partial_name}*' if partial_name else 'all'
    for host in inventory.list_hosts(pattern):
        hosts.append([host.name, host.vars.get('ansible_host'), host.groups])

    if hosts:
        click.echo(tabulate(sorted(hosts), tablefmt='plain'))
    else:
        click.echo('Host Inventory: ' + config.ansible.hosts_file)


@main.command()
@click.argument('host')
def ssh(host):
    """ Run ssh for the given host """
    inventory = _get_inventory()

    hosts = inventory.list_hosts(f'*{host}*')

    if hosts:
        if len(hosts) > 1:
            click.echo('Found multiple matches and will use first one: ' + ', '.join(h.name for h in hosts))
        run(['ssh', hosts[0].vars.get('ansible_host', hosts[0].name)])


@main.command('set-hosts')
@click.argument('hosts_file')
def set_hosts(hosts_file):
    """ Set hosts file """
    if 'ansible' not in config:
        config.add_section('ansible')

    config.ansible.hosts_file = hosts_file
    config.save()


def _get_inventory():
    if 'ansible' not in config or not config.ansible.hosts_file:
        click.echo('Please set path to Ansible hosts file by running: ah set-hosts <PATH>')
        sys.exit(1)

    return InventoryManager(loader=DataLoader(), sources=config.ansible.hosts_file)
