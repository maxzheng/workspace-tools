from __future__ import absolute_import
from __future__ import print_function
from contextlib import contextmanager
import logging
import os
import re
import signal
import subprocess
import sys
import tempfile

import psutil
from setproctitle import setproctitle
import six


log = logging.getLogger(__name__)


def prompt_with_editor(instruction):
    """ Prompt user with instruction in $EDITOR and return the response """

    with tempfile.NamedTemporaryFile(suffix='.tmp') as fh:
        fh.write('\n\n# ' + '\n# '.join(instruction.split('\n')))
        fh.flush()
        editor = os.environ.get('EDITOR', 'vim')
        run([editor, fh.name])
        return '\n'.join([l for l in open(fh.name).read().split('\n') if not l.startswith('#')]).strip()


def parent_path_with_dir(directory, path=None):
    """
    Find parent that contains the given directory.

    :param str directory: Directory to look for
    :param str path: Initial path to look from. Defaults to current working directory.
    :return: Parent path that contains the directory
    :rtype: str on success or False on failure
    """
    return parent_path_with(lambda p: os.path.isdir(os.path.join(p, directory)), path=path)


def parent_path_with_file(name, path=None):
    """
    Find parent that contains the given directory.

    :param str name: File name to look for
    :param str path: Initial path to look from. Defaults to current working directory.
    :return: Parent path that contains the file name
    :rtype: str on success or False on failure
    """
    return parent_path_with(lambda p: os.path.isfile(os.path.join(p, name)), path=path)


def parent_path_with(check, path=None):
    """
    Find parent that satisfies check with content.

    :param str check: Callable that accepts current path returns True if path should be returned
    :param str path: Initial path to look from. Defaults to current working directory.
    :return: Parent path that contains the directory
    :rtype: str on success or False on failure
    """
    if path == '/':
        return False

    if not path:
        path = os.getcwd()

    if check(path):
        return path

    return parent_path_with(check, os.path.dirname(path))


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
    except (Exception, KeyboardInterrupt) as e:
        if title:
            log.error(title)
        if stack:
            log.exception(e)
        elif str(e):
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
    :param bool/int silent: Suppress stdout/stderr.
                            If True, completely silent.
                            If 2, print cmd output on error.
    :param bool return_output: Return the command output. Defaults silent=True. Set silent=False to see output.
                               If True, always return output.
                               If set to 2, return a tuple of (output, success) where output is the output of the command
                               and success is exit code 0.
                               When used, it is guaranteed to always return output / other options are ignored (like raises).
    :param bool raises: Raise an exception if command exits with an error code.
    :param dict subprocess_args: Additional args to pass to subprocess
    :return: Output or boolean of success depending on option selected
    :raise RunError: if the command exits with an error code and raises=True
    """

    if isinstance(cmd, six.string_types):
        cmd = cmd.split()

    cmd_str = ' '.join(cmd)

    if 'shell' in subprocess_args and subprocess_args['shell']:
        cmd = cmd_str

    log.debug('Running: %s %s', cmd_str, '[%s]' % cwd if cwd else '')

    if return_output and silent is None:
        silent = True

    try:
        if silent or return_output:
            p = subprocess.Popen(cmd, cwd=cwd, bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **subprocess_args)
            exit_code = -1

            if silent:
                output, _ = p.communicate()
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

            output = output.decode('utf-8')

            if return_output is True:
                return output
            elif return_output == 2:
                return output, exit_code == 0

            if exit_code == 0:
                if return_output:
                    return output
                else:
                    return True

            elif raises or silent == 2:
                if output and silent:
                    print(output.strip())

        else:
            exit_code = subprocess.call(cmd, cwd=cwd, **subprocess_args)
            if exit_code == 0:
                return True

    except Exception as e:
        if raises:
            log.debug(e, exc_info=True)
            raise RunError('Command "%s" could not be run because %s' % (cmd_str, e))

    # We only get here if exit code != 0
    if raises:
        raise RunError('Command "%s" returned non-zero exit status %d' % (cmd_str, exit_code))

    return False


def parallel_call(call, args, callback=None, workers=10, show_progress=None, progress_title='Progress'):
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

    def to_tuple(a):
        return a if isinstance(a, (list, tuple, set)) else [a]

    try:
        async_results = [(arg, pool.apply_async(call, to_tuple(arg), callback=callback)) for arg in args]

        results = {}
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
                    progress = show_progress(list(results.keys()), args)
                else:
                    progress = '%.2f%% completed' % (len(results) * 100.0 / len(async_results))
                show_status('%s: %s' % (progress_title, progress))

        pool.close()
        pool.join()

        return results

    except KeyboardInterrupt:
        os.killpg(os.getpid(), signal.SIGTERM)  # Kills any child processes from subprocesses.
        pool.terminate()
        pool.join()
        sys.exit()


def show_status(message):
    """
      :param str message: Status message to show. If not, then status bar will be cleared.
    """
    enabled = (sys.stdout.isatty() and 'TERM' in os.environ) or os.environ.get('PYCHARM_HOSTED')
    if not enabled:
        return

    sys.stdout.write('%s\r' % message)
    sys.stdout.flush()


def background_processes():
    """
      List of background processes from `run_in_background`
    """
    prog_prefix = os.path.basename(sys.argv[0]) + ' ['
    processes = []

    for process in psutil.process_iter():
        try:
            if process.cmdline()[0].startswith(prog_prefix):
                cmdline = ' '.join(process.cmdline())[len(prog_prefix)-1:]
                repo, task = cmdline.lstrip('[').split(']', 1)
                processes.append((repo, task, process.pid))
        except Exception:
            pass

    return processes


def run_in_background(title, repo=None, info_suffix='[To check, run: {prog} wait]', log_file=None):
    """
      Run any code after this point in the background. This call is idempotent as subsequent calls
      won't do anything except change the title.

      :param str title: Title to set the running process. This should be informative to the user on
                        what is being run in the background and will happen.
      :param str repo: Name of repo the task is being acted on. Defaults to os.getcwd()
      :param str info_suffix: Informational suffix to append when showing the title before forking.
                              {prog} will be replaced by the running program's name.
      :param str log_file: Full path to log file to save output/error. Saves to temp dir by default.
                           Set to "/dev/null" to discard output.
    """
    prog = os.path.basename(sys.argv[0])
    setproctitle('%s [%s] %s' % (prog, os.path.basename(repo or os.getcwd()), title))

    if hasattr(run_in_background, 'forked'):
        return
    else:
        run_in_background.forked = True

    if not log_file:
        def rs(s):  # Remove special characters
            return re.sub('[^a-zA-Z0-9]', '_', s)
        log_file = os.path.join(tempfile.gettempdir(), 'wait-{0}-{1}.out'.format(rs(os.path.basename(repo or os.getcwd())), rs(title)))

    log.info('%s %s' % (title, info_suffix.format(prog=prog)))
    log.debug('Log file: %s', log_file)

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        log.error(e)
        sys.exit(1)

    if repo:
        os.chdir(repo)
    os.setsid()
    os.umask(0)

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        log.error(e)
        sys.exit(1)

    sys.stdout.flush()
    sys.stderr.flush()
    so = open(log_file, 'w+')
    se = open(log_file, 'w+', 0)
    si = open(log_file, 'r')
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

    print('[%s] %s' % (os.path.basename(repo or os.getcwd()), title))
    sys.stdout.flush()
