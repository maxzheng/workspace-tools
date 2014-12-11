import logging
import signal
import sys

from workspace.scm import commit_logs, repo_check

log = logging.getLogger(__name__)


def show_log(file=None, patch=False, number=None, *args, **kwargs):
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
