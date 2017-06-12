from __future__ import absolute_import
from __future__ import print_function
from glob import glob
import logging
import os
import re
import subprocess

from localconfig import LocalConfig

from workspace.config import product_groups
from workspace.scm import project_path

log = logging.getLogger(__name__)


class ToxIni(LocalConfig):
    """ Represents tox.ini """

    VAR_RE = re.compile('{\[(.+)](.+)}')

    def __init__(self, path=None, tox_ini=None):
        """
        :param str path: The path to load tox*.ini from.
        :param str tox_ini: Path to tox ini file. Defaults to tox.ini in path root.
        """
        self.path = path
        self.tox_ini = tox_ini or self.find_tox_ini(self.path)

        super(ToxIni, self).__init__(self.tox_ini)

    @classmethod
    def find_tox_ini(cls, path):
        """
        Find tox.ini in path or its parent paths.

        :param str path: Path to get tox.ini for or its parent paths.
        :return: Path to tox.ini
        :raise IOError: if there is no tox.ini found
        """

        tox_ini  = project_path(path=path)

        if not tox_ini:
            raise IOError('No tox.ini found in %s. Please run "wst setup --product" first to setup tox.' % path)

        return os.path.join(tox_ini, 'tox.ini')

    @property
    def envlist(self):
        return [e.strip() for e in self.tox.envlist.split(',') if e]

    def envsection(self, env=None):
        return 'testenv:%s' % env if env else 'testenv'

    @property
    def workdir(self):
        return os.path.join(self.path, self.get('tox', 'toxworkdir', '.tox'))

    def envdir(self, env):
        default_envdir = os.path.join(self.path, '.tox', env)
        return self.expand_vars(self.get(self.envsection(env), 'envdir', self.get(self.envsection(), 'envdir', default_envdir)).replace('{toxworkdir}', self.workdir))

    def bindir(self, env, script=None):
        dir = os.path.join(self.envdir(env), 'bin')
        if script:
            dir = os.path.join(dir, script)
        return dir

    def commands(self, env):
        envsection = self.envsection(env)
        commands = self.get(envsection, 'commands', self.get('testenv', 'commands', 'py.test {env:PYTESTARGS:}'))
        return [_f for _f in self.expand_vars(commands).split('\n') if _f]

    def expand_vars(self, value):
        if '{' in value:
            value = self.VAR_RE.sub(lambda m: self.get(m.group(1), m.group(2)), value)
        return value


class ProductPager(object):
    """ Pager to show contents from multiple products (paths) """
    MAX_TERMINAL_ROWS = 25

    def __init__(self, optional=False):
        """ If optional is True, then pager is only used if the # of lines of the first write exceeds `self.MAX_TERMINAL_ROWS` lines. """
        self.pager = None
        self.optional = optional

    def write(self, product, output, branch=None):
        if not self.pager:
            if not self.optional or len(output.split('\n')) > self.MAX_TERMINAL_ROWS:
                self.pager = create_pager('^\[.*]')

        if self.pager:
            self.pager.stdin.write('[ {} ]\n'.format(product).encode())
            if branch and branch != 'master':
                self.pager.stdin.write('# On branch {}\n'.format(branch).encode())
            self.pager.stdin.write('{}\n\n'.format(output.strip()).encode())
        else:
            if branch and branch != 'master':
                print('# On branch %s' % branch)
            print(output)

    def close_and_wait(self):
        if self.pager:
            self.pager.stdin.close()
            self.pager.wait()


def create_pager(highlight_text=None):
    """ Returns a pipe to PAGER or "less" """
    pager_cmd = os.environ.get('PAGER')

    if not pager_cmd:
        pager_cmd = ['less']
        if highlight_text:
            pager_cmd.extend(['-p', highlight_text])

    pager = subprocess.Popen(pager_cmd, stdin=subprocess.PIPE)

    return pager


def expand_product_groups(names):
    """ Expand product groups found in the given list of names to produce a sorted list of unique names. """
    unique_names = set(names)
    exclude_names = set()

    for name in list(unique_names):
        if name.startswith('-'):
            unique_names.remove(name)
            exclude_names.update(expand_product_groups([name.lstrip('-')]))

    for group, names in list(product_groups().items()):
        if group in unique_names:
            unique_names.remove(group)
            unique_names.update(expand_product_groups(names))

    return sorted(list(unique_names - exclude_names))
