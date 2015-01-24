import argparse
import logging
import pkg_resources


from workspace.commands.bump import setup_bump_parser
from workspace.commands.checkout import setup_checkout_parser
from workspace.commands.clean import setup_clean_parser
from workspace.commands.commit import setup_commit_parser
from workspace.commands.test import setup_test_parser
from workspace.commands.diff import setup_diff_parser
from workspace.commands.log import setup_log_parser
from workspace.commands.publish import setup_publish_parser
from workspace.commands.push import setup_push_parser
from workspace.commands.update import setup_update_parser
from workspace.commands.status import setup_status_parser
from workspace.commands.setup import setup_setup_parser
from workspace.utils import log_exception


DESCRIPTION = """
Tools to simplify workspace / scm management when working with multiple repositories.

It helps you do more with less work by seamlessly integrating all workspace tooling into one where
you can simply run one command instead of many native commands individually to do common tasks.
And it is SCM agnostic (git/git-svn/svn), so you don't need to remember the different syntaxes.

To get started
---------------
* Optionally setup workspace environment/shortcuts, run "wst setup -h" for options.
    - "wst setup -a" is recommended. :)
* To checkout a product, run: wst checkout <git or svn repository url> [<url2> ...]
    - Product that use svn is checked out with git-svn
* All commands are named appropriately for what they do, but see its --help for additional info.
* For more info, read the docs at http://workspace-tools.readthedocs.org
"""


def main():
  """
  Main controller for 'wst'.
  Copy this to create your own controller to make changes to parsers or pass in an init callable to ws_entry_point.

  I.e. To customize a command, such as checkout, do this::

    parser, subparsers, parsers = setup_parsers()
    parsers['checkout'].add_argument('-c', '--cool-new-feature', action='store_true', help='Adds cool new feature to checkoout')
  """
  parser, subparsers, parsers = setup_parsers()
  ws_entry_point(parser)


def setup_parsers(package_name=None):
  """
  Sets up parsers for all commands

  :param str package_name: Additional package name to show version for.
                           By default, it shows the version for 'workspace-tools' package when ``wst -v`` is run
  :return: A tuple of (parser, subparsers, parsers) where::
              parser - :class:`argparse.ArgumentParser` instance
              subparsers - argparse subparsers instance for parser
              parsers - Dict mapping of command to its parser instance
  :rtype: tuple(argparse.ArgumentParser, argparse._SubParsersAction, dict)
  """
  logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

  parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.register('action', 'parsers', AliasedSubParsersAction)
  setup_parser(parser, package_name)

  subparsers = parser.add_subparsers(title='sub-commands', help='List of sub-commands')
  subparsers.remove_parser = lambda *args, **kwargs: _remove_parser(subparsers, *args, **kwargs)

  parsers = {
    'bump': setup_bump_parser(subparsers),
    'checkout': setup_checkout_parser(subparsers),
    'clean': setup_clean_parser(subparsers),
    'commit': setup_commit_parser(subparsers),
    'diff': setup_diff_parser(subparsers),
    'log': setup_log_parser(subparsers),
    'publish': setup_publish_parser(subparsers),
    'push': setup_push_parser(subparsers),
    'setup': setup_setup_parser(subparsers),
    'status': setup_status_parser(subparsers),
    'test': setup_test_parser(subparsers),
    'update': setup_update_parser(subparsers)
  }

  return parser, subparsers, parsers


def ws_entry_point(parser):
  """
  Main entry point for 'wst' that parses args, sets up config, and executes command.

  :param argparse.ArgumentParser parser: The parser to get args from
  """
  args = parser.parse_args()

  if args.debug:
    logging.root.setLevel(logging.DEBUG)

  with log_exception(exit=True, stack=args.debug):
    args.command(**args.__dict__)


def setup_parser(parser, package_name=None):
  """
  Sets up the main parser

  :param ArgumentParser parser:
  :param str package_name: Additional package name to show version for.
                           By default, it shows the version for 'workspace-tools' package when ``wst -v`` is run
  """
  version = '\n'.join('%s %s' % (pkg, pkg_resources.get_distribution(pkg).version)
                      for pkg in filter(None, [package_name, 'workspace-tools']))
  parser.add_argument('-v', '--version', action='version', version=version)
  parser.add_argument('--debug', action='store_true', help='Turn on debug mode')


def _remove_parser(self, name, **kwargs):
  # remove choice help from list
  if 'help' in kwargs:
    alias_name = '%s (' % name
    self._choices_actions = [action
                             for action in self._choices_actions
                             if action.dest != name and not action.dest.startswith(alias_name)]

  # remove the parser from the map
  self._name_parser_map.pop(name, None)

  # remove aliases
  aliases = kwargs.pop('aliases', ())
  for alias in aliases:
    self._name_parser_map.pop(alias, None)


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
