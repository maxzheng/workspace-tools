import argparse
import logging
import pkg_resources
import sys

from workspace.commands.checkout import setup_checkout_parser
from workspace.commands.clean import setup_clean_parser
from workspace.commands.commit import setup_commit_parser
from workspace.commands.diff import setup_diff_parser
from workspace.commands.log import setup_log_parser
from workspace.commands.update import setup_update_parser
from workspace.commands.status import setup_status_parser
from workspace.commands.setup import setup_setup_parser
from workspace.commands.push import setup_push_parser
from workspace.config import CONFIG_FILE


def main():
  """ Main controller for 'ws'. Copy this to create your own controller with custom setup_parsers """
  ws_entry_point(default_setup_argparse)


def default_setup_argparse(parser, subparsers):
  """
  Default setup for parsers. Copy this to customize your own.

  To customize a command, such as checkout, do this::

    checkout_parser = setup_checkout_parser(subparsers)
    checkout_parser.add_argument('-c', '--cool-new-feature', action='store_true', help='Adds cool new feature to checkoout')

  """
  setup_parser(parser)

  setup_checkout_parser(subparsers)
  setup_clean_parser(subparsers)
  setup_commit_parser(subparsers)
  setup_diff_parser(subparsers)
  setup_log_parser(subparsers)
  setup_push_parser(subparsers)
  setup_setup_parser(subparsers)
  setup_status_parser(subparsers)
  setup_update_parser(subparsers)


def ws_entry_point(setup_parsers):
  """
  Main entry point for 'ws' that sets up argparse and executes command.

  :param setup_parsers: A function to setup argparse that accepts :class:`argparse.ArgumentParser` and subparsers instance.
                         Customize arguments by providing a custom function based on default_setup_argparse.
  """
  logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

  parser = argparse.ArgumentParser()
  _money_patch_aliases(parser)

  subparsers = parser.add_subparsers(title='sub-commands', help='List of sub-commands')
  setup_parsers(parser, subparsers)

  args = parser.parse_args()

  if args.debug:
    logging.root.setLevel(logging.DEBUG)

  args.command(**args.__dict__)


def setup_parser(parser):
  """ Sets up the main parser """
  parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + pkg_resources.get_distribution('workspace-tools').version)
  parser.add_argument('--debug', action='store_true', help='Turn on debug mode')


def _money_patch_aliases(parser):
  """ Add 'aliases' param to sub parsers """
  parser.register('action', 'parsers', AliasedSubParsersAction)


# Copied from https://gist.github.com/sampsyo/471779
class AliasedSubParsersAction(argparse._SubParsersAction):

  class _AliasedPseudoAction(argparse.Action):
    def __init__(self, name, aliases, help):
      dest = name
      if aliases:
        dest += ' (%s)' % ','.join(aliases)
      sup = super(AliasedSubParsersAction._AliasedPseudoAction, self)
      sup.__init__(option_strings=[], dest=dest, help=help)

  def add_parser(self, name, **kwargs):
    if 'aliases' in kwargs:
      aliases = kwargs['aliases']
      del kwargs['aliases']
    else:
      aliases = []

    parser = super(AliasedSubParsersAction, self).add_parser(name, **kwargs)

    # Make the aliases work.
    for alias in aliases:
      self._name_parser_map[alias] = parser
    # Make the help text reflect them, first removing old help entry.
    if 'help' in kwargs:
      help = kwargs.pop('help')
      self._choices_actions.pop()
      pseudo_action = self._AliasedPseudoAction(name, aliases, help)
      self._choices_actions.append(pseudo_action)

    return parser
