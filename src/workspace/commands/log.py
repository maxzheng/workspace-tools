import logging
import signal
import sys

from workspace.scm import commit_logs, repo_check
from workspace.utils import split_doc

log = logging.getLogger(__name__)


def setup_log_parser(subparsers):
  doc, docs = split_doc(show_log.__doc__)
  log_parser = subparsers.add_parser('log', description=doc, help=doc)
  log_parser.add_argument('file', nargs='?', help=docs['file'])
  log_parser.add_argument('-p', '--patch', action='store_true', help=docs['patch'])
  log_parser.add_argument('-n', '--number', type=int, help=docs['number'])
  log_parser.set_defaults(command=show_log)

  return log_parser


def show_log(file=None, patch=False, number=None, *args, **kwargs):
  """
  Show commit logs

  :param str file: File to show logs for
  :param bool patch: Generate patch / show diff
  :param int number: Limit number number of log entries
  """

  repo_check()

  # Interrupt for git log results in bad tty
  signal.signal(signal.SIGINT, signal.SIG_IGN)

  try:
    commit_logs(number, patch=patch, show=True, file=file)
  except Exception as e:
    # Oddly, git log returns non-zero exit whenever user exits while it is still printing
    log.debug(e)
