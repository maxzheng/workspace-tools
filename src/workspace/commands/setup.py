import argparse
import logging
import os
import sys

from workspace.scm import is_repo


log = logging.getLogger(__name__)

WS_SETUP_START = '# Added by "workspace setup" (do not remove comments before / after function)'
WS_SETUP_END = "# workspace setup - end"
WS_FUNCTION_TEMPLATE = """
alias _workspace=%s

function ws ()
{
  if [ $# -gt 0 ]; then
    _workspace "$@";
  else
    cd %s
    ls
  fi
}
"""
COMMAND_FUNCTION_TEMPLATE = 'function %s() { _workspace %s "$@"; }\n'
COMMAND_ALIAS_TEMPLATE = 'alias %s=%s\n'
COMMANDS = {
  'a': '"source ./activate"',
  'd': '"deactivate"',

  'co': 'checkout',
  'ci': 'commit',
  'de': 'develop',
  'di': '_diff',
  'st': 'status',
  'up': 'update',

  '_cl': 'clean',
  '_lo': 'log',
  '_pu': 'push',
  '_pb': 'publish',
}


def setup_setup_parser(subparsers):
  setup_parser = subparsers.add_parser('setup', description=setup.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, help='Optional (refer to setup --help). Setup workspace environment. Run from primary workspace directory.')
  group = setup_parser.add_mutually_exclusive_group()
  group.add_argument('-c', '--commands', action='store_true', help='Add convenience bash function for certain commands, such as checkout to run "workspace checkout"')
  group.add_argument('-a', '--commands-with-aliases', action='store_true', help='Same as --commands plus add shortcut aliases, like "co" for checkout. This is for those developers that want to get as much done with the least key strokes - true efficienist! ;)')
  group.add_argument('--uninstall', action='store_true', help='Uninstall all functions/aliases')
  setup_parser.set_defaults(command=setup)

  return setup_parser


def setup(commands=None, commands_with_aliases=None, uninstall=False, additional_commands=None, **kwargs):
  """
  Sets up workspace environment.

  While "wst" will work for multiple workspaces, this should only be run in your primary workspace directory.

  It sets up a "ws" bash function that goes to your workspace directory when no argument is passed in, otherwise
  runs wst command. And also additional functions / aliases for some commands if --commands/--commands-with-aliases
  is passed in. --commands-with-aliases (-a) is recommended. :)

  This can be re-run multiple times to change setup.
  """
  bashrc_content = None
  bashrc_file = "~/.bashrc"
  bashrc_path = os.path.expanduser(bashrc_file)
  bashrc_script = []

  if os.path.exists(bashrc_path):
    with open(bashrc_path) as fh:
      bashrc_content = fh.read()

    skip = False
    for line in bashrc_content.split('\n'):
      if line in (WS_SETUP_START, WS_SETUP_END):
        skip = not skip
        continue
      if not skip:
        bashrc_script.append(line)

    bashrc_script = '\n'.join(bashrc_script).strip().split('\n')  # could be better

  repo_path = is_repo()
  if repo_path:
    workspace_dir = os.path.dirname(repo_path).replace(os.path.expanduser('~'), '~')
  else:
    workspace_dir = os.getcwd().replace(os.path.expanduser('~'), '~')

  with open(bashrc_path, 'w') as fh:
    if bashrc_script:
      fh.write('\n'.join(bashrc_script) + '\n\n')

    if uninstall:
      log.info('Removed ws and related functions/aliases from %s', bashrc_file)
      return

    fh.write(WS_SETUP_START)

    fh.write(WS_FUNCTION_TEMPLATE % (os.path.realpath(sys.argv[0]), workspace_dir))
    log.info('Added "ws" bash function with workspace directory set to %s', workspace_dir)

    if additional_commands:
      COMMANDS.update(additional_commands)

    if commands or commands_with_aliases:
      functions = sorted([f for f in COMMANDS.values() if not f.startswith('"')])
      fh.write('\n')
      for func in functions:
        fh.write(COMMAND_FUNCTION_TEMPLATE % (func, func.lstrip('_')))
      log.info('Added additional bash functions: %s', ', '.join([f for f in functions if not f.startswith('_')]))

    if commands_with_aliases:
      fh.write('\n')
      aliases = [item for item in sorted(COMMANDS.items(), key=lambda x: x[0]) if not item[0].startswith('_')]
      for alias, command in aliases:
        fh.write(COMMAND_ALIAS_TEMPLATE % (alias, command))
      log.info('Added aliases: %s', ', '.join(["%s=%s" % (a, c.lstrip('_')) for a, c in aliases]))

    fh.write(WS_SETUP_END + '\n')

  log.info('To use, run "source %s" or open a new shell.', bashrc_file)
