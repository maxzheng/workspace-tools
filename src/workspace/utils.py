from contextlib import contextmanager
import logging
import os
import subprocess
import sys


log = logging.getLogger(__name__)


def parent_path_with_dir(directory, path=None):
  """
  Find parent that contains the given directory.

  :param str directory: Directory to look for
  :param str path: Initial path to look from. Defaults to current working directory.
  :return: Parent path that contains the directory
  :rtype: str on success or False on failure
  """
  if path == '/':
    return False

  if not path:
    path = os.getcwd()

  if os.path.isdir(os.path.join(path, directory)):
    return path

  return parent_path_with_dir(directory, os.path.dirname(path))


@contextmanager
def log_exception(title=None, exit=False, call=None, stack=False):
  """
  Context generator that logs exceptions as error

  :param str title: Title to log before the exception
  :param bool exit: Do sys.exit when exception occurs
  :param callable call: Call to make before exit
  :param bool stack: Log stacktrace
  """
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
  """ Same as run with slient=True """
  return run(*args, silent=True, **kwargs)


def run(cmd, cwd=None, silent=False, return_output=False, raises=True, **subprocess_args):
  """
  Runs a CLI command.

  :param list/str cmd: Command with args to run.
  :param str cwd: Change directory to cwd before running
  :param bool silent: Suppress stdout/stderr
  :param bool return_output: Return the command output
  :param bool raises: Raise an exception if command exits with an error code.
  :param dict subprocess_args: Additional args to pass to subprocess
  :return: Output or None depending on option selected
  :raise RunError: if the command exits with an error code and raises=True
  """

  if isinstance(cmd, basestring):
    cmd = cmd.split()

  cmd_str = ' '.join(cmd)

  if 'shell' in subprocess_args and subprocess_args['shell']:
    cmd = cmd_str

  log.debug('Running: %s', cmd_str)

  try:
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

  except Exception as e:
    if raises:
      raise RunError('Command "%s" could not be run because %s' % (cmd_str, e))

  # We only get here if exit code != 0
  if raises:
    raise RunError('Command "%s" returned non-zero exit status %d' % (cmd_str, exit_code))

  return False


def split_doc(docstring):
  """
  Split the param description from the docstring

  :param str docstring: Docstring to split
  :return: Tuple of (doc, param_docs) where doc is the part before :param, and param_docs is a dict of param -> param doc.
  :rtype: tuple(str, dict(str, str))
  """
  doc_parts = docstring.split(':param ')
  doc = doc_parts[0].rstrip()
  params = {}

  for doc_part in doc_parts[1:]:
    type_param, param_doc = doc_part.split(':', 1)
    param = type_param.split()[-1]
    params[param] = param_doc.strip()

  return doc, params


def parallel_call(call, args, workers=10):
  """
  Call a callable in parallel for each arg

  :param callable call: Callable to call
  :param list(tuple) args: List of tuple args to call. Each tuple represents the full args list per call.
  :param int workers: Number of workers to use.
  """

  from multiprocessing import Pool
  import signal

  pool = Pool(workers, lambda: signal.signal(signal.SIGINT, signal.SIG_IGN))
  try:
    pool.map_async(call, args).get(9999999)
  except KeyboardInterrupt:
    pool.terminate()
    pool.join()
