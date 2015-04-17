from contextlib import contextmanager
import logging
import os
import re
import signal
import subprocess
import sys
import time


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


def parallel_call(call, args, callback=None, workers=10, show_progress=None, progress_title='Progress:'):
  """
  Call a callable in parallel for each arg

  :param callable call: Callable to call
  :param list(iterable|non-iterable) args: List of args to call. One call per args.
  :param callable callback: Callable to call for each result.
  :param int workers: Number of workers to use.
  :param bool/str/callable: Show progress.
                            If callable, it should accept two lists: completed args and all args and return progress string.
  :return dict: Map of args to their results on completion
  """

  from multiprocessing import Pool, TimeoutError

  signal.signal(signal.SIGTERM, lambda *args: sys.exit(1))
  pool = Pool(workers, lambda: signal.signal(signal.SIGINT, signal.SIG_IGN))

  try:
    to_tuple = lambda a: a if isinstance(a, (list, tuple, set)) else [a]
    async_results = [(arg, pool.apply_async(call, to_tuple(arg), callback=callback)) for arg in args]

    results = {}
    with ProgressLogger(progress_title):
      while len(results) != len(async_results):
        for arg, result in async_results:
          if arg not in results:
            try:
              # This allows processes to be interrupted by CTRL+C
              results[arg] = result.get(1)
            except TimeoutError:
              pass
            except Exception as e:
              results[arg] = str(e)

        if show_progress:
          if callable(show_progress):
            progress = show_progress(results.keys(), args)
          else:
            progress = '%.2f%% completed' % (len(results) * 100.0 / len(async_results))
          ProgressLogger.progress(progress)

    pool.close()
    pool.join()

    return results

  except KeyboardInterrupt:
    os.killpg(os.getpid(), signal.SIGTERM)  # Kills any child processes from subprocesses.
    pool.terminate()
    pool.join()
    sys.exit()


class ProgressLogger(object):
  """
    Everything is wrapped up in one class, so you simply import this one class rather than several functions
    Creator returns
  """

  #: Set to False to disable any progress output, by default will only show progress when ran interactively or in debugger
  enabled = (sys.stdout.isatty() and 'TERM' in os.environ) or os.environ.get('PYCHARM_HOSTED')

  #: Should timing of progress be shown? Set this to True before you start any progress logging
  benchmark = False

  #: Should we try and detect terminal resizing?
  detect_terminal_resize = True

  _prefix = ''
  _sections = []
  _terminal_width = None
  _message_format = None
  _last_output_time = None
  _last_message = None
  _minimum_time = 0.0005

  DEFAULT_WIDTH = 80

  def __new__(cls, message, *args):
    """
      Returns a context manager starting/stopping a section of progress output prefixed with 'message' (and formatted with 'args')
      Handier than a call to push() + pop()
      All functions are classmethod, this is a pure singleton
      Allows to state a simple 'with' section:

      with ProgressLogger('my section'):
        ...

      :param str message: Message to show
      :param list args: Optional args to format 'message' with
      :return ProgressLogger: Context manager
    """
    cls.push(message, *args)
    return cls

  @classmethod
  def __enter__(cls):
    pass

  @classmethod
  def __exit__(cls, *args, **kwargs):
    cls.pop()

  @classmethod
  def push(cls, message, *args):
    """
      :param str message: Start a long lasting section of progress with 'message' (lasts until pop()-ed, formatted with 'args')
      :param list args: Optional args to format 'message' with
    """
    if not cls.enabled and not cls.benchmark:
      return

    if cls.benchmark and not cls._last_output_time:
      cls._last_output_time = time.time()

    if args:
      message = message % args

    cls._sections.append(message)
    cls._prefix = message
    cls._output(cls._prefix)

  @classmethod
  def _show_elapsed_time(cls, message):
    """
      :param str message: Start a long lasting section of progress with 'message' (lasts until pop()-ed, formatted with 'args')
    """
    # Remove any percentages (as those are more interesting to just aggregate)
    clean_message = re.sub(r'[0-9]+%', '--', message)

    if not cls._last_message:
      cls._last_message = clean_message

    elif clean_message != cls._last_message:
      elapsed = time.time() - cls._last_output_time

      if elapsed > cls._minimum_time and cls._last_message:
        # Only show non trivial progresses
        cls._ensure_width()
        print '%.3fs %s' % (elapsed, cls.formatted(cls._last_message, width=cls._terminal_width - 6))

      cls._last_message = clean_message
      cls._last_output_time = time.time()

  @classmethod
  def progress(cls, message, *args):
    """
      :param str message: Small unit of progress, appears after last push()-ed section
      :param list args: Optional args to format 'message' with
    """
    if not cls.enabled and not cls.benchmark:
      return

    if args:
      message = message % args

    message = '%s %s' % (cls._prefix, message)

    if cls._last_output_time:
      cls._show_elapsed_time(message)

    cls._output(message)

  @classmethod
  def add(cls, message, *args):
    """
      :param str message: Extra info to add to current section
      :param list args: Optional args to format 'message' with
    """
    if not cls.enabled and not cls.benchmark:
      return

    if args:
      message = message % args

    cls._prefix += ' %s' % message
    cls._output(cls._prefix)

  @classmethod
  def pop(cls):
    """
      Pop last long lasting message
    """
    if not cls.enabled and not cls.benchmark:
      return

    cls._sections.pop()

    if cls._sections:
      cls._prefix = cls._sections[-1]

    else:
      cls._prefix = ''

      if cls._last_output_time:
        cls._show_elapsed_time('')

    cls._output(cls._prefix)

  @classmethod
  def formatted(cls, message, width=None):
    """
      :param str message: Message formatted for current terminal
      :param int, None width: Width to use (use None to pick internally determined width)
      :return str: Formatted message
    """
    if width is None:
      cls._ensure_width()
      return cls._message_format % message[:cls._terminal_width]

    else:
      message_format = '%%-%ds\r' % width
      return message_format % message[:width]

  @classmethod
  def clear(cls):
    """
      Clear current output
    """
    cls._output('')

  @classmethod
  def _output(cls, message):
    """
      :param str message: 'message' to output, make sure to clear rest of line on terminal
    """
    if not cls.enabled:
      return

    message = cls.formatted(message)

    sys.stdout.write(message)
    sys.stdout.flush()

  @classmethod
  def _ensure_width(cls):
    """
      Ensure cls._terminal_width is set
    """
    if not cls._terminal_width:
      cls._handle_resize()

      if cls.detect_terminal_resize:
        # Respond to SIGWINCH event to detect resizing
        signal.signal(signal.SIGWINCH, cls._handle_resize)

  @classmethod
  def _handle_resize(cls, signum=None, frame=None):
    """
      Catch resize signals from the terminal.
    """
    cls._terminal_width = int(os.environ.get('COLUMNS', cls.DEFAULT_WIDTH)) - 1
    cls._message_format = '%%-%ds\r' % cls._terminal_width
