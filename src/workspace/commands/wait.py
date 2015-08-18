import logging
import sys

from tabulate import tabulate

from workspace.commands import AbstractCommand
from workspace.utils import background_processes, run, run_in_background

log = logging.getLogger(__name__)


class Wait(AbstractCommand):
  """
    Wait for an event to be completed and optionally start background/waiting tasks.

    If no argument is passed, then show running background/waiting tasks.
    Any extra arguments passed to wait will be run in the background. I.e. ws wait sleep 10

    :param int review: Wait for 'Ship It' from review board.
    :param bool publish: Wait for a new version to be published.
    :param int interval: Minutes to wait between each check.
                         Defaults to 5 minutes.
    :param list extra_args: Arbitrary commands to run in background.
  """
  def __init__(self, *args, **kwargs):
    #: Run wait in background if possible
    self.in_background = False

    super(Wait, self).__init__(*args, **kwargs)

  @classmethod
  def arguments(cls):
    _, docs = cls.docs()
    return [
      cls.make_args('-r', '--review', action='store_true', help=docs['review']),
      cls.make_args('-P', '--publish', action='store_true', help=docs['publish']),
      cls.make_args('-i', '--interval', type=int, default=5, help=docs['interval'])
    ]

  def run(self):
    if self.extra_args:
      run_in_background(' '.join(self.extra_args))
      run(self.extra_args, shell=True)
      sys.exit(0)

    if not (self.review or self.publish):
      processes = background_processes()
      if processes:
        print tabulate(processes, headers=['PID', 'Task'])
      sys.exit(0)

    raise NotImplementedError('Not implemented. Please implement Wait.run() in a subclass.')
