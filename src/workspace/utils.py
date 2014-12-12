import argparse
from contextlib import contextmanager
import logging
import os
import subprocess
import sys


log = logging.getLogger(__name__)


def parent_path_with_dir(directory, path=None):
  if path == '/':
    return False

  if not path:
    path = os.getcwd()

  if os.path.isdir(os.path.join(path, directory)):
    return path

  return parent_path_with_dir(directory, os.path.dirname(path))


@contextmanager
def log_exception(title=None, exit=False, call=None, stack=False):
  """ A context generator that logs exceptions as error and optionally provides an additional error title, exits, or calls a method. """
  try:
    yield
  except Exception as e:
    if title:
      log.error(title)
    if stack:
      log.exception(e)
    else:
      log.error(e)
    if call:
      call()
    if exit:
      sys.exit(1)


class RunError(Exception):
  pass


def silent_run(*args, **kwargs):
  return run(*args, silent=True, **kwargs)


def run(cmd, cwd=None, silent=False, return_output=False, raises=True, **subprocess_args):
  """ Unlike the call counterpart, this runs the cmd to show or return output """

  if isinstance(cmd, basestring):
    cmd = cmd.split()

  cmd_str = ' '.join(cmd)

  if 'shell' in subprocess_args and subprocess_args['shell']:
    cmd = cmd_str

  log.debug('Running: %s', cmd_str)

  if silent or return_output:
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **subprocess_args)
    output, errors = p.communicate()
    exit_code = p.returncode

    if exit_code == 0:
      if return_output:
        return output
      else:
        return True

    elif raises:
      if output:
        print output.strip()
      if errors:
        print errors.strip()

  else:
    exit_code = subprocess.call(cmd, cwd=cwd, **subprocess_args)
    if exit_code == 0:
      return True

  # We only get here if exit code != 0
  if raises:
    raise RunError('Command "%s" returned non-zero exit status %d' % (cmd_str, exit_code))

  return False
