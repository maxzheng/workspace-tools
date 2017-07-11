from __future__ import absolute_import
import argparse
import logging
import pkg_resources
import sys
import textwrap

from workspace.commands.bump import Bump
from workspace.commands.checkout import Checkout
from workspace.commands.clean import Clean
from workspace.commands.commit import Commit
from workspace.commands.diff import Diff
from workspace.commands.log import Log
from workspace.commands.merge import Merge
from workspace.commands.publish import Publish
from workspace.commands.push import Push
from workspace.commands.update import Update
from workspace.commands.status import Status
from workspace.commands.setup import Setup
from workspace.commands.test import Test
from workspace.utils import log_exception


log = logging.getLogger(__name__)


class Commander(object):
    """
      Tools to simplify workspace / scm management when working with multiple repositories.

      It helps you do more with less work by seamlessly integrating all workspace tooling into one where
      you can simply run one command instead of many native commands individually to do common tasks.

      To get started
      ---------------
      * Optionally setup workspace environment/shortcuts, run "wst setup -h" for options.
          - "wst setup -a" is recommended. :)
      * To checkout a product, run: wst checkout <git repository url> [<url2> ...]
      * All commands are named appropriately for what they do, but see its --help for additional info.
      * For more info, read the docs at http://workspace-tools.readthedocs.org
    """

    @classmethod
    def commands(cls):
        """
          Map of command name to command classes.
          Override commands to replace any command name with another class to customize the command.
        """
        cs = [Bump, Checkout, Clean, Commit, Diff, Log, Merge, Publish, Push, Setup, Status, Test, Update]
        return dict((c.name(), c) for c in cs)

    @classmethod
    def command(cls, name):
        """ Get command class for name """
        return cls.commands().get(name)

    @classmethod
    def main(cls):
        logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
        cls()._run()

    def _run(self):
        """
          Sets up logging, parser, and creates the necessary command sequences to run, and runs
          the command given by the user.
        """
        self.setup_parsers()

        args, extra_args = self.parser.parse_known_args()

        if args.command not in [c.name() for c in list(self.commands().values()) if 'extra_args' in c.docs()[1]] and extra_args:
            log.error('Unrecognized arguments: %s', ' '.join(extra_args))
            sys.exit(1)

        if args.debug:
            logging.root.setLevel(logging.DEBUG)

        with log_exception(exit=True, stack=args.debug):
            args_dict = args.__dict__
            args_dict['extra_args'] = extra_args
            return self.run(args.command, **args_dict)

    def run(self, name=None, **kwargs):
        """
          Run the command by name with given args.

          :param str name: Name of command to run. If not given, this calls self._run()
          :param kwargs: Args to pass to the command constructor
        """
        if not name:
            return self._run()

        if name in self.commands():
            kwargs['commander'] = self
            return self.command(name)(**kwargs).run()
        else:
            log.error('Command "%s" is not registered. Override Commander.commands() to add.', name)
            sys.exit(1)

    def _setup_parser(self):
        """
          Sets up the main parser.

          To show version of your customized wst package when --version is invoked, set cls.package_name to your package name.
        """
        self.parser = argparse.ArgumentParser(description=textwrap.dedent(self.__doc__),
                                              formatter_class=argparse.RawDescriptionHelpFormatter)
        self.parser.register('action', 'parsers', AliasedSubParsersAction)

        versions = []
        for pkg in [_f for _f in [getattr(self, 'package_name', None), 'workspace-tools'] if _f]:
            try:
                versions.append('%s %s' % (pkg, pkg_resources.get_distribution(pkg).version))
            except Exception:
                pass

        self.parser.add_argument('-v', '--version', action='version', version='\n'.join(versions))
        self.parser.add_argument('--debug', action='store_true', help='Turn on debug mode')

    def setup_parsers(self):
        """
          Sets up parsers for all commands
        """

        self._setup_parser()

        self.subparsers = self.parser.add_subparsers(title='sub-commands', help='List of sub-commands')
        self.subparsers.remove_parser = lambda *args, **kwargs: _remove_parser(self.subparsers, *args, **kwargs)

        for name, command in sorted(self.commands().items()):
            doc, _ = command.docs()
            help = list(filter(None, doc.split('\n')))[0]
            aliases = [command.alias] if command.alias else None

            parser = self.subparsers.add_parser(name, aliases=aliases, description=textwrap.dedent(doc), help=help,
                                                formatter_class=argparse.RawDescriptionHelpFormatter)
            parser.set_defaults(command=name)

            cmd_args = command.arguments()

            if isinstance(cmd_args, tuple):
                normal_args, chain_args = cmd_args
            else:
                normal_args = cmd_args
                chain_args = []

            for args, kwargs in normal_args:
                parser.add_argument(*args, **kwargs)

            if chain_args:
                group = parser.add_argument_group('chaining options')
                for args, kwargs in chain_args:
                    group.add_argument(*args, **kwargs)


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
            aliases = kwargs['aliases'] or []
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
