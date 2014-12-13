import argparse
import logging
import pkg_resources
import sys

from workspace.config import init_config
from workspace.commands.checkout import setup_checkout_parser
from workspace.commands.clean import setup_clean_parser
from workspace.commands.commit import setup_commit_parser
from workspace.commands.develop import setup_develop_parser
from workspace.commands.diff import setup_diff_parser
from workspace.commands.log import setup_log_parser
from workspace.commands.update import setup_update_parser
from workspace.commands.status import setup_status_parser
from workspace.commands.setup import setup_setup_parser
from workspace.commands.push import setup_push_parser


DESCRIPTION = """
Tools to simplify workspace / scm management when working with multiple repositories.

To get started
---------------
* Optionally setup workspace environment/shortcuts, run "wst setup -h" for options.
    - "wst setup -a" is recommended. :)
* To checkout a product, run: wst checkout <git or svn repository url> [<url2> ...]
    - Product that use svn is checked out with git-svn
* All commands are named appropriately for what they do, but see its --help for additional info.
"""


def main():
  """
  Main controller for 'ws'. Copy this to create your own controller with custom _setup_parsers.

  To customize a command, such as checkout, do this::

    parser, subparsers, parsers = setup_parsers()
    parsers['checkout'].add_argument('-c', '--cool-new-feature', action='store_true', help='Adds cool new feature to checkoout')

  """
  parser, subparsers, parsers = setup_parsers()
  ws_entry_point(parser)


def setup_parsers():
  """
  Default setup for command parsers.

  :ret (parser, subparsers, parsers): parser - :class:`argparse.ArgumentParser' instance
                                      subparsers - argparse subparsers instance for parser
                                      parsers - Dict mapping of command to its parser instance
  """
  logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

  parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=argparse.RawDescriptionHelpFormatter)
  setup_parser(parser)

  _money_patch_aliases(parser)

  subparsers = parser.add_subparsers(title='sub-commands', help='List of sub-commands')

  parsers = {
    'checkout': setup_checkout_parser(subparsers),
    'clean': setup_clean_parser(subparsers),
    'commit': setup_commit_parser(subparsers),
    'develop': setup_develop_parser(subparsers),
    'diff': setup_diff_parser(subparsers),
    'log': setup_log_parser(subparsers),
    'push': setup_push_parser(subparsers),
    'setup': setup_setup_parser(subparsers),
    'status': setup_status_parser(subparsers),
    'update': setup_update_parser(subparsers)
  }

  return parser, subparsers, parsers


def ws_entry_point(parser):
  """
  Main entry point for 'ws' that sets up argparse and executes command.

  :param :class:`argparse.ArgumentParser` parser:
  """
  args = parser.parse_args()

  if args.debug:
    logging.root.setLevel(logging.DEBUG)

  init_config()

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
