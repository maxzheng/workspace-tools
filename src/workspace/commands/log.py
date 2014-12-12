import logging
import signal
import sys

from workspace.scm import commit_logs, repo_check

log = logging.getLogger(__name__)


def setup_log_parser(subparsers):
  log_parser = subparsers.add_parser('log', description=show_log.__doc__, help=show_log.__doc__)
  log_parser.add_argument('file', nargs='?', help='File to show logs for')
  log_parser.add_argument('-p', '--patch', action='store_true', help='Generate patch / show diff')
  log_parser.add_argument('-n', '--number', type=int, help='Limit number number of log entrie')
  log_parser.set_defaults(command=show_log)

  return log_parser


def show_log(file=None, patch=False, number=None, *args, **kwargs):
  """ Show commit logs """

  repo_check()

  # Interrupt for git log results in bad tty
  signal.signal(signal.SIGINT, signal.SIG_IGN)

  try:
    commit_logs(number, patch=patch, show=True, file=file)
  except Exception as e:
    msg = str(e)
    if ' -p' not in msg:  # Oddly, git log -p returns non-zero exit whenever user exits while it is still printing
      log.error(msg)
      sys.exit(1)
