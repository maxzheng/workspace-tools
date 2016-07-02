from glob import glob
import logging
import os
import re
import subprocess

from localconfig import LocalConfig

from workspace.config import product_groups

log = logging.getLogger(__name__)


class ToxIni(LocalConfig):
  """ Represents tox.ini """

  VAR_RE = re.compile('{\[(.+)](.+)}')

  def __init__(self, repo=None, tox_ini=None):
    """
    :param str repo: The repo to load tox*.ini from.
    :param str tox_ini: Path to tox ini file. Defaults to tox*.ini in repo root.
    """
    self.repo = repo
    self.path = tox_ini or self.path_for(repo)
    super(ToxIni, self).__init__(self.path)

  @classmethod
  def path_for(cls, repo):
    """
    :param str repo: Repo to get tox*.ini for
    :return: Path to tox*.ini
    :raise IOError: if there is no tox*.ini found
    """

    tox_inis = glob(os.path.join(repo, 'tox*.ini'))

    if not tox_inis:
      raise IOError('No tox.ini found in %s. Please run "wst setup --product" first to setup tox.' % repo)

    elif len(tox_inis) > 1:
      log.warn('More than one ini files found - will use first one: %s', ', '.join(tox_inis))

    return tox_inis[0]

  @property
  def envlist(self):
    return [e.strip() for e in self.tox.envlist.split(',') if e]

  def envsection(self, env):
    return 'testenv:%s' % env

  @property
  def workdir(self):
    return os.path.join(self.repo, self.get('tox', 'toxworkdir', '.tox'))

  def envdir(self, env):
    envsection = self.envsection(env)
    if envsection not in self:
      log.debug('Using default envdir and commands as %s section is not defined in %s', envsection, self.path)

    return self.expand_vars(self.get(envsection, 'envdir', os.path.join(self.repo, '.tox', env)).replace('{toxworkdir}', self.workdir))

  def bindir(self, env, script=None):
    dir = os.path.join(self.envdir(env), 'bin')
    if script:
      dir = os.path.join(dir, script)
    return dir

  def commands(self, env):
    envsection = self.envsection(env)
    commands = self.get(envsection, 'commands', self.get('testenv', 'commands', 'py.test {env:PYTESTARGS:}'))
    return filter(None, self.expand_vars(commands).split('\n'))

  def expand_vars(self, value):
    if '{' in value:
      value = self.VAR_RE.sub(lambda m: self.get(m.group(1), m.group(2)), value)
    return value


class ProductPager(object):
  """ Pager to show contents from multiple products (repos) """
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
      self.pager.stdin.write('[ ' + product + ' ]\n')
      if branch and branch != 'master':
        self.pager.stdin.write('# On branch %s\n' % branch)
      self.pager.stdin.write(output.strip() + '\n\n')
    else:
      if branch and branch != 'master':
        print '# On branch %s' % branch
      print output

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

  for group, names in product_groups().items():
    if group in unique_names:
      unique_names.remove(group)
      unique_names.update(expand_product_groups(names))

  return sorted(list(unique_names - exclude_names))
