import logging
import os
import subprocess

from workspace.config import product_groups

log = logging.getLogger(__name__)


class ProductPager(object):
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

  for group, names in product_groups().items():
    if group in unique_names:
      unique_names.remove(group)
      unique_names.update(expand_product_groups(names))

  return sorted(list(unique_names))
