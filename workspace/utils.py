from contextlib import contextmanager
import logging
import os
import signal
import sys
import tempfile
from utils.process import run


log = logging.getLogger(__name__)


def shortest_id(name, names):
    """ Return shortest name that isn't a duplicate in names """
    if name in names:
        names.remove(name)

    for i, letter in enumerate(name):
        for other_name in names:
            if other_name[i:i+1] == letter:
                break
        else:
            break

    return name[0:i+1]


def prompt_with_editor(instruction):
    """ Prompt user with instruction in $EDITOR and return the response """

    with tempfile.NamedTemporaryFile(suffix='.tmp') as fh:
        fh.write('\n\n# ' + '\n# '.join(instruction.split('\n')))
        fh.flush()
        editor = os.environ.get('EDITOR', 'vim')
        run([editor, fh.name])
        return '\n'.join([line for line in open(fh.name).read().split('\n') if not line.startswith('#')]).strip()


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
