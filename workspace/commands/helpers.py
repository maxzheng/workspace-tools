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

    VAR_RE = re.compile(r'{(\w+)}')

    def __init__(self, path=None, tox_ini=None):
        """
        :param str path: The path to load tox*.ini from.
        :param str tox_ini: Path to tox ini file. Defaults to tox.ini in path root.
        """
        if not tox_ini:
            tox_ini = self.find_tox_ini(path)

        super().__init__(tox_ini)

        # These must be set after super() otherwise there will be recursion error
        self.tox_ini = tox_ini
        self.path = path or os.path.dirname(tox_ini)

    @classmethod
    def find_tox_ini(cls, path):
        """
        Find tox.ini in path or its parent paths.

        :param str path: Path to get tox.ini for or its parent paths.
        :return: Path to tox.ini
        :raise IOError: if there is no tox.ini found
        """

        repo_path = project_path(path=path)

        if not repo_path:
            raise IOError('No tox.ini found in %s. Please run "wst setup --product" first to setup tox.' % path)

        tox_ini = os.path.join(repo_path, 'tox.ini')

        log.debug('Using %s', tox_ini)

        return tox_ini

    @property
    def envlist(self):
        return [e.strip() for e in self.tox.envlist.split(',') if e]

    def envsection(self, env=None):
        return 'testenv:%s' % env if env else 'testenv'

    @property
    def inidir(self):
        return self.path

    @property
    def workdir(self):
        toxworkdir = self.get('tox', 'toxworkdir', '{toxinidir}/.tox')
        return self.expand_vars(toxworkdir)

    @property
    def homedir(self):
        return os.path.expanduser('~')

    def envdir(self, env):
        default_envdir = os.path.join('{toxworkdir}', env)
        default_envsection = self.envsection()
        default_envdir = self.get(default_envsection, 'envdir', default_envdir)
        envsection = self.envsection(env)
        envdir = self.get(envsection, 'envdir', default_envdir)
        return self.expand_vars(envdir, {'envname': env})

    def bindir(self, env, script=None):
        dir = os.path.join(self.envdir(env), 'bin')
        if script:
            dir = os.path.join(dir, script)
        return dir

    def commands(self, env):
        envsection = self.envsection(env)
        commands = self.get(envsection, 'commands', self.get('testenv', 'commands', 'pytest {env:PYTESTARGS:}'))
        commands = commands.replace('\\\n', '')
        return [_f for _f in self.expand_vars(commands).split('\n') if _f]

    def expand_vars(self, value, extra_vars={}):
        if '{' in value:
            value = self.VAR_RE.sub(lambda m: extra_vars.get(
                m.group(1), getattr(self, m.group(1), m.group(0)) or getattr(self, m.group(1)[3:], m.group(0))), value)
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
                self.pager = create_pager(r'^\[.*]')

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
        pager_cmd = ['less', '-r']
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
