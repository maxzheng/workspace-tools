import argparse
from glob import glob
import logging
import os
import re
import sys

from workspace.scm import is_repo, repo_check, product_name, repo_path
from workspace.utils import split_doc


log = logging.getLogger(__name__)

BASHRC_FILE = "~/.bashrc"
WSTRC_FILE = "~/.wstrc"

WS_SETUP_START = '# Added by "workspace setup" (do not remove comments before / after function)'
WS_SETUP_END = "# workspace setup - end"

WS_FUNCTION_TEMPLATE = """\
alias _wst=%s

function ws ()
{
  if [ $# -gt 0 ]; then
    _wst "$@";
  else
    cd %s
    ls
  fi
}
"""
COMMAND_FUNCTION_TEMPLATE = 'function %s() { _wst %s "$@"; }\n'
COMMAND_ALIAS_TEMPLATE = 'alias %s=%s\n'
COMMANDS = {
  'a': "'source .tox/${PWD##*/}/bin/activate'",  # Must use single quote for $PWD##* to work properly
  'd': "'deactivate'",

  'co': 'checkout',
  'ci': 'commit',
  'di': '_diff',
  'st': 'status',
  'up': 'update',

  '_bu': 'bump',
  '_cl': 'clean',
  '_lo': 'log',
  '_pu': 'push',
  '_pb': 'publish',
  '_te': 'test',
}
AUTO_COMPLETE_TEMPLATE = """
function _branch_file_completer() {
    local cur=${COMP_WORDS[COMP_CWORD]}

    if git status &> /dev/null; then
        branches=`git branch`
    else
        branches=''
    fi

    COMPREPLY=( $( compgen -W "$branches" -- $cur ) )
}

complete -o default -F _branch_file_completer co
complete -o default -F _branch_file_completer checkout
complete -F _branch_file_completer push

complete -o default log
complete -o default di
"""
TOX_INI_FILE = 'tox.ini'
TOX_INI_TMPL = """\
[tox]
envlist = py27

[testenv]
downloadcache = {toxworkdir}/_download
recreate = True
setenv =
	PIP_PROCESS_DEPENDENCY_LINKS=1
	PIP_DEFAULT_TIMEOUT=60
	ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future
basepython = python

[testenv:py27]
commands =
	py.test
recreate = False
skipsdist = True
usedevelop = True
deps =
	pytest
	pytest-xdist
	pytest-cov
	{[testenv:style]deps}
	sphinx!=1.2b2
whitelist_externals =
	ln
envdir = {toxworkdir}/%s

[testenv:style]
commands =
	flake8 --config tox.ini src test
recreate = False
skipsdist = True
deps =
	flake8

[testenv:coverage]
commands =
	py.test --cov=src --cov-report=xml --cov-report=html --cov-report=term test
deps =
	pytest
	pytest-cov
usedevelop = True

[flake8]
ignore = E111,E121,W292,E123,E226
max-line-length = 160
"""
SETUP_PY_TMPL = """\
#!/usr/bin/env python

import os
import setuptools


setuptools.setup(
  name='%s',
  version='0.0.1',

  author='<PLACEHOLDER>',
  author_email='<PLACEHOLDER>',

  description=open('%s').read(),

#  entry_points={
#    'console_scripts': [
#      'script_name = package.module:entry_callable',
#    ],
#  },

  install_requires=open('%s').read(),

  license='MIT',

  package_dir={'': 'src'},
  packages=setuptools.find_packages('src'),
  include_package_data=True,

  setup_requires=['setuptools-git'],

#  scripts=['bin/cast-example'],

  classifiers=[
    'Development Status :: 5 - Production/Stable',

    'Intended Audience :: Developers',
    'Topic :: Software Development :: <PLACEHOLDER SUB-TOPIC>',

    'License :: OSI Approved :: MIT License',

    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
  ],

  keywords='<KEYWORDS>',
)
"""
README_TMPL = """\
%s
===========

<PLACEHOLDER DESCRIPTION>
"""

def setup_setup_parser(subparsers):
  doc, docs = split_doc(setup.__doc__)
  setup_parser = subparsers.add_parser('setup', description=doc, formatter_class=argparse.RawDescriptionHelpFormatter,
                                       help='Setup workspace or product environment')
  group = setup_parser.add_mutually_exclusive_group(required=True)
  group.add_argument('--product', action='store_true', help=docs['product'])
  group.add_argument('--commands', action='store_true', help=docs['commands'])
  group.add_argument('-a', '--commands-with-aliases', action='store_true', help=docs['commands_with_aliases'])
  group.add_argument('--uninstall', action='store_true', help=docs['uninstall'])
  setup_parser.set_defaults(command=setup)

  return setup_parser


def setup(product=False, commands=None, commands_with_aliases=None, uninstall=False, additional_commands=None, **kwargs):
  """
  Sets up workspace or product environment.

  :param bool product: Initialize product by setting up tox with py27, style, and coverage test environments.
                       Also create setup.py, README.rst, and src / test directories if they don't exist.
  :param bool commands: Add convenience bash function for certain commands, such as checkout to run
                        "workspace checkout", or "ws" bash function that goes to your workspace directory
                        when no argument is passed in, otherwise runs wst command.
  :param bool commands_with_aliases: Same as --commands plus add shortcut aliases, like "co" for checkout.
                                     This is for those developers that want to get as much done with the least
                                     key strokes - true efficienist! ;)
  :param bool uninstall: Uninstall all functions/aliases.
  """
  if product:
    setup_product()
  else:
    setup_workspace(commands, commands_with_aliases, uninstall, additional_commands)


def setup_product():
  repo_check()

  name = product_name(repo_path())
  placeholder_info = '- please update <PLACEHOLDER> with appropriate value'

  tox_ini = TOX_INI_TMPL % name
  tox_ini_file = os.path.join(repo_path(), TOX_INI_FILE)
  with open(tox_ini_file, 'w') as fp:
    fp.write(tox_ini)

  log.info('Created %s', _relative_path(tox_ini_file))

  readme_files = glob(os.path.join(repo_path(), 'README*'))
  if readme_files:
    readme_file = readme_files[0]
  else:
    readme_file = os.path.join(repo_path(), 'README.rst')
    with open(readme_file, 'w') as fp:
      fp.write(README_TMPL % name)
    log.info('Created %s %s', _relative_path(readme_file), placeholder_info)

  setup_py_file = os.path.join(repo_path(), 'setup.py')
  if not os.path.exists(setup_py_file):
    requirements_file = os.path.join(repo_path(), 'requirements.txt')
    if not os.path.exists(requirements_file):
      with open(requirements_file, 'w') as fp:
        pass
      log.info('Created %s', _relative_path(requirements_file))

    readme_name = os.path.basename(readme_file)
    requirements_name = os.path.basename(requirements_file)

    with open(setup_py_file, 'w') as fp:
      fp.write(SETUP_PY_TMPL % (name, readme_name, requirements_name))

    log.info('Created %s %s', _relative_path(setup_py_file), placeholder_info)

  src_dir = os.path.join(repo_path(), 'src')
  if not os.path.exists(src_dir):
    package_dir = os.path.join(src_dir, re.sub('[^A-Za-z]', '', name))
    os.makedirs(package_dir)
    init_file = os.path.join(package_dir, '__init__.py')
    open(init_file, 'w').close()
    log.info('Created %s', _relative_path(init_file))

  test_dir = os.path.join(repo_path(), 'test')
  if not os.path.exists(test_dir):
    os.makedirs(test_dir)
    test_file = os.path.join(test_dir, 'test_%s.py' % re.sub('[^A-Za-z]', '_', name))
    with open(test_file, 'w') as fp:
      fp.write('# Placeholder for tests')
    log.info('Created %s', _relative_path(test_file))

def setup_workspace(commands, commands_with_aliases, uninstall, additional_commands):
  bashrc_content = None
  bashrc_path = os.path.expanduser(BASHRC_FILE)
  wstrc_path = os.path.expanduser(WSTRC_FILE)

  bashrc_script = []

  if os.path.exists(bashrc_path):
    with open(bashrc_path) as fh:
      bashrc_content = fh.read()

    skip = False
    for line in bashrc_content.split('\n'):
      if line in (WS_SETUP_START, WS_SETUP_END):
        skip = not skip
        continue
      if not skip and not WSTRC_FILE in line:
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
      if os.path.exists(wstrc_path):
        os.unlink(wstrc_path)
      log.info('Removed %s and its sourcing reference from %s', WSTRC_FILE, BASHRC_FILE)
      log.info('Please restart your bash session for the change to take effect')
      return

    fh.write('source %s\n' % WSTRC_FILE)

  with open(wstrc_path, 'w') as fh:
    fh.write(WS_FUNCTION_TEMPLATE % (os.path.realpath(sys.argv[0]), workspace_dir))
    log.info('Added "ws" bash function with workspace directory set to %s', workspace_dir)

    if additional_commands:
      COMMANDS.update(additional_commands)

    if commands or commands_with_aliases:
      functions = sorted([f for f in COMMANDS.values() if not (f.startswith("'") or f.startswith('"'))])
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

      fh.write(AUTO_COMPLETE_TEMPLATE)

  log.info('To use, run "source %s" or open a new shell.', WSTRC_FILE)

def _relative_path(path):
  if path.startswith(os.getcwd() + os.path.sep):
    path = path[len(os.getcwd())+1:]
  return path

