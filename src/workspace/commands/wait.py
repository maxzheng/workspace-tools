import logging

from workspace.commands import AbstractCommand

log = logging.getLogger(__name__)


class Wait(AbstractCommand):
  """
    Wait for an event to be completed. Useful for chaining sequences of commands.

    :param int review: Wait for 'Ship It' from review board.
    :param bool publish: Wait for a new version to be published.
    :param int interval: Minutes to wait between each check.
                         Defaults to 5 minutes.
  """
  @classmethod
  def arguments(cls):
    _, docs = cls.docs()
    return [
      cls.make_args('-r', '--review', action='store_true', help=docs['review']),
      cls.make_args('-P', '--publish', action='store_true', help=docs['publish']),
      cls.make_args('-i', '--interval', type=int, default=5, help=docs['interval'])
    ]

  def run(self):
    raise NotImplementedError('Not implemented. Please implement Wait.run() in a subclass.')
