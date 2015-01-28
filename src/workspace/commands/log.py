import logging
import signal

from workspace.scm import commit_logs, repo_check
from workspace.utils import split_doc

log = logging.getLogger(__name__)


def setup_log_parser(subparsers):
  doc, docs = split_doc(show_log.__doc__)
  log_parser = subparsers.add_parser('log', description=doc, help=doc.split('\n')[1])
  log_parser.add_argument('-p', '--diff', action='store_true', help=docs['diff'])
  log_parser.add_argument('-r', '--show', help=docs['show'])
  log_parser.add_argument('-n', '--limit', metavar='NUM', type=int, help=docs['limit'])
  log_parser.set_defaults(command=show_log)

  return log_parser


def show_log(diff=False, show=None, limit=None, extra_args=None, debug=False, *args, **kwargs):
  """
  Show commit logs.

  Extra arguments are passed to the underlying SCM's log command.

  :param bool diff: Generate patch / show diff
  :param str show: Show specific revision. This implies --diff and limit of 1
  :param int limit: Limit number of log entries
  :param list extra_args: Extra args to pass to the underlying SCM's log command
  """

  repo_check()

  # Interrupt for git log results in bad tty
  signal.signal(signal.SIGINT, signal.SIG_IGN)

  try:
    commit_logs(limit, diff=diff, show_revision=show, extra_args=extra_args, to_pager=True)
  except Exception as e:
    # Oddly, git log returns non-zero exit whenever user exits while it is still printing
    if debug:
      log.exception(e)
