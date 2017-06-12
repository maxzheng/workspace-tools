from __future__ import absolute_import
import logging
import signal

from workspace.commands import AbstractCommand
from workspace.scm import commit_logs, repo_check

log = logging.getLogger(__name__)


class Log(AbstractCommand):
    """
      Show commit logs.

      Extra arguments are passed to the underlying SCM's log command.

      :param bool diff: Generate patch / show diff
      :param str show: Show specific revision. This implies --diff and limit of 1
      :param int limit: Limit number of log entries
      :param list extra_args: Extra args to pass to the underlying SCM's log command
    """

    @classmethod
    def arguments(cls):
        _, docs = cls.docs()
        return [
          cls.make_args('-p', '--diff', action='store_true', help=docs['diff']),
          cls.make_args('-r', '--show', help=docs['show']),
          cls.make_args('-n', '--limit', metavar='NUM', type=int, help=docs['limit'])
        ]

    def run(self):

        repo_check()

        # Interrupt for git log results in bad tty
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        try:
            commit_logs(self.limit, diff=self.diff, show_revision=self.show, extra_args=self.extra_args, to_pager=True)
        except Exception as e:
            # Oddly, git log returns non-zero exit whenever user exits while it is still printing
            if self.debug:
                log.exception(e)
