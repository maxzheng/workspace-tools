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


def run(cmd, cwd=None, silent=None, return_output=False, raises=True, **subprocess_args):
  """
  Runs a CLI command.

  :param list/str cmd: Command with args to run.
  :param str cwd: Change directory to cwd before running
  :param bool/int silent: Suppress stdout/stderr. If True/1, completely silent. If 2, print cmd output on error.
  :param bool return_output: Return the command output. When True, silent defaults to True. Set silent=False to see output.
                             If 2, always return output regardless of error.
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

  log.debug('Running: %s %s', cmd_str, '[%s]' % cwd if cwd else '')

  if return_output and silent is None:
      silent = True

  try:
    if silent or return_output:
      p = subprocess.Popen(cmd, cwd=cwd, bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **subprocess_args)
      exit_code = -1

      if silent:
        output, error = p.communicate()
        output += error
        exit_code = p.returncode
      else:
        output = ''
        ch = True
        while ch:
          ch = p.stdout.read(1)
          sys.stdout.write(ch)
          sys.stdout.flush()
          output += ch
          if p.poll() is not None and exit_code == -1:
            exit_code = p.returncode

      if return_output == 2:
        return output

      if exit_code == 0:
        if return_output:
          return output
        else:
          return True

      elif raises or silent == 2:
        if output and silent:
          print output.strip()

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


def parallel_call(call, args, callback=None, workers=10):
  """
  Call a callable in parallel for each arg

  :param callable call: Callable to call
  :param list(iterable|non-iterable) args: List of args to call. One call per args.
  :param callable callback: Callable to call for each result.
  :param int workers: Number of workers to use.
  :return dict: Map of args to their results on completion
  """

  from multiprocessing import Pool
  import signal

  signal.signal(signal.SIGTERM, lambda *args: sys.exit(1))
  pool = Pool(workers, lambda: signal.signal(signal.SIGINT, signal.SIG_IGN))

  try:
    to_tuple = lambda a: a if isinstance(a, (list, tuple, set)) else [a]
    async_results = [(arg, pool.apply_async(call, to_tuple(arg), callback=callback)) for arg in args]

    # This allows processes to be interrupted by CTRL+C
    results = dict((arg, result.get(9999999)) for arg, result in async_results)

    pool.close()
    pool.join()

    return results

  except KeyboardInterrupt:
    os.killpg(os.getpid(), signal.SIGTERM)  # Kills any child processes from subprocesses.
    pool.terminate()
    pool.join()
    sys.exit()
