from __future__ import absolute_import
from glob import glob
import logging
import os
import re
import sys

import click
import requests

from workspace.commands import AbstractCommand
from workspace.scm import is_repo, product_name


log = logging.getLogger(__name__)

BASHRC_FILE = "~/.bashrc"
WSTRC_FILE = "~/.wstrc"

WS_SETUP_START = '# Added by "workspace setup" (do not remove comments before / after function)'
WS_SETUP_END = "# workspace setup - end"

WS_FUNCTION_TEMPLATE = """\
alias _wst=%s

function ws() {
  if [ $# -gt 0 ]; then
    _wst "$@";
  else
    cd %s
    ls
  fi
}

function activate() {
  venv=${1:-${PWD##*/}}
  if [ -e ./activate ]; then
    source ./activate
  elif [ -e bin/activate ]; then
    source bin/activate
  elif [ -e ../build/$venv/venv/bin/activate ]; then
    source ../build/$venv/venv/bin/activate
  elif [ -e build/$venv/venv/bin/activate ]; then
    source build/$venv/venv/bin/activate
  elif [ -e $venv/activate ]; then
    source $venv/activate
  elif [ -e ~/.virtualenvs/$venv/bin/activate ]; then
    source ~/.virtualenvs/$venv/bin/activate
  elif [ -e .tox/$venv/bin/activate ]; then
    source .tox/$venv/bin/activate
  else
    echo "No activate script found. Please setup your venv."
  fi
}

function open_files_from_last_command() {
  if [ "$1" ]; then
    last_command="1 ag '$@'"
  else
    last_command=`history 100 | grep  -E "^\s+[0-9]+\s+(ag|ack|grep|find|which|ls) " | tail -1`
  fi

  if [ -z "$last_command" ]; then
    echo No ag, ack, grep, find, or which command found in last 100 commands.
    return
  fi

  declare -a "parts=($last_command)"
  command=${parts[1]}

  if [[ "$command" = "ag" || "$command" = "ack" || "$command" = "grep" ]]; then
    full_command=${parts[@]:1}
    pattern=+/${parts[2]}

    raw_parts=(${last_command// / })  # Need the quote retained to sub properly
    last_part=${raw_parts[@]:(-1)}

    if [[ $last_part != "-l" ]]; then
        sub_expr=" $last_part= $last_part -l"
    else
        sub_expr=
    fi

    if [ "$1" ]; then
      files=`ag -l "$@"`
    elif [ -z "$sub_expr" ]; then
      files=`fc -s $command`
    else
      files=`fc -s "$sub_expr" $command`
    fi

    if [ -z "$files" ]; then
      echo No files found from output
    else
      vim -p $files "$pattern" --cmd "set ignorecase smartcase"
    fi

  else
    files=`fc -s $command`

    if [ -z "$files" ]; then
      echo No files found from output
    else
      vim -p $files
    fi

  fi
}
"""
COMMAND_FUNCTION_TEMPLATE = 'function %s() { _wst %s "$@"; }\n'
COMMAND_ALIAS_TEMPLATE = 'alias %s=%s\n'
COMMANDS = {
  'a': "'activate'",
  'd': "'deactivate'",
  'tv': "'open_files_from_last_command'  # from ag/ack/grep/find/which [t]o [v]im",

  'co': 'checkout',
  'ci': 'commit',
  'di': '_diff',
  'st': 'status',
  'up': 'update',

  '_bu': 'bump',
  '_cl': 'clean',
  '_lo': 'log',
  '_mg': 'merge',
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
    branches=
  fi

  if [ ! -z "$branches" ]; then
    COMPREPLY=( $( compgen -W "$branches" -- $cur ) )
  fi
}
function _env_file_completer() {
  local cur=${COMP_WORDS[COMP_CWORD]}

  if ls tox*.ini &>/dev/null || ls .tox*.ini &>/dev/null; then
    envs=`grep -h '^\[testenv:' .tox*.ini tox*.ini 2>/dev/null | sed -E 's/^\[testenv:(.+)]/\\1/' | grep -vE '^(py|pydev)$'`
    COMPREPLY=( $( compgen -W "$envs" -- $cur ) )
  fi
}

complete -o default -F _branch_file_completer co
complete -o default -F _branch_file_completer checkout
complete -o default -F _env_file_completer test
complete -F _branch_file_completer push

complete -o default log
complete -o default di
"""
TOX_INI_FILE = 'tox.ini'
TOX_INI_TMPL = """\
[tox]
envlist = cover, py37, style

[testenv]
# Consolidate all deps here instead of separately in test/style/cover so we
# have a single env to work with, which makes debugging easier (like which env?).
# Not as clean but easier to work with during development, which is better.
deps =
    flake8
    mock
    pytest
    pytest-cov
    pytest-fixtures
    pytest-xdist
    sphinx
install_command =
    pip install -U {packages}
recreate = False
skipsdist = True
usedevelop = True
setenv =
    PIP_PROCESS_DEPENDENCY_LINKS=1
    PIP_DEFAULT_TIMEOUT=60
    ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future
envdir = {homedir}/.virtualenvs/{name}_{envname}
commands =
    pytest {env:PYTESTARGS:}

[testenv:py36]
envdir = {homedir}/.virtualenvs/{name}

[testenv:style]
basepython = python3.6
envdir = {homedir}/.virtualenvs/{name}
commands =
    flake8 --config tox.ini

[testenv:cover]
basepython = python3.6
envdir = {homedir}/.virtualenvs/{name}
commands =
    pytest {env:PYTESTARGS:} --cov . --cov-report=xml --cov-report=html --cov-report=term --cov-report=annotate:textcov \\
                             --cov-fail-under=80

[flake8]
exclude = .git,.tox,.eggs,__pycache__,docs,build,dist
ignore = E111,E121,W292,E123,E226,W503
max-line-length = 120

# Uncomment to enable concurrency for pytest
#[pytest]
#addopts = -n 4
"""
SETUP_PY_TMPL = """\
import setuptools


setuptools.setup(
    name='%s',
    version='0.0.1',

    author='<PLACEHOLDER>',
    author_email='<PLACEHOLDER>',

    description='<PLACEHOLDER>',
    long_description=open('%s').read(),

    url='<PLACEHOLDER>',

    install_requires=open('%s').read(),

    license='MIT',

    packages=setuptools.find_packages(),
    include_package_data=True,

    python_requires='>=3.6',
    setup_requires=['setuptools-git', 'wheel'],

    # entry_points={
    #    'console_scripts': [
    #        'script_name = package.module:entry_callable',
    #    ],
    # },

    # Standard classifiers at https://pypi.org/classifiers/
    classifiers=[
      'Development Status :: 5 - Production/Stable',

      'Intended Audience :: Developers',
      'Topic :: Software Development :: <PLACEHOLDER SUB-TOPIC>',

      'License :: OSI Approved :: MIT License',

      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.6',
    ],

    keywords='<KEYWORDS>',
)
"""
README_TMPL = """\
{name}
===========

<PLACEHOLDER DESCRIPTION>

To install::

    pip install {name}

"""
COVERAGERC_TMPL = """\
[run]
omit =
    .git/*
    .tox/*
    docs/*
    setup.py
    test/*
    tests/*
"""


class Setup(AbstractCommand):
    """
      Sets up workspace or product environment.

      :param bool product: Initialize product by setting up tox with py27, style, and coverage test environments.
                           Also create setup.py, README.rst, and test directories if they don't exist.
      :param bool commands: Add convenience bash function for certain commands, such as checkout to run
                            "workspace checkout", or "ws" bash function that goes to your workspace directory
                            when no argument is passed in, otherwise runs wst command.
      :param bool commands_with_aliases: Same as --commands plus add shortcut aliases, like "co" for checkout.
                                         This is for those developers that want to get as much done with the least
                                         key strokes - true efficienist! ;)
      :param bool uninstall: Uninstall all functions/aliases.
    """
    #: Dict for additional commands to setup
    additional_commands = None

    @classmethod
    def arguments(cls):
        _, docs = cls.docs()
        return [
          cls.make_args('--product', action='store_true', help=docs['product']),
          cls.make_args('--commands', action='store_true', help=docs['commands']),
          cls.make_args('-a', '--commands-with-aliases', action='store_true', help=docs['commands_with_aliases']),
          cls.make_args('--uninstall', action='store_true', help=docs['uninstall'])
        ]

    def run(self):
        num_options = len([_f for _f in [self.product, self.commands, self.commands_with_aliases, self.uninstall]
                          if _f])
        if num_options > 1:
            log.error('Only one setup option can be selected at a time.')
            sys.exit(1)

        elif not num_options:
            log.error('At least one option must be selected. See -h for options.')
            sys.exit(1)

        if self.product:
            self.setup_product()
        else:
            self.setup_workspace()

    def _create_or_update_file(self, path, content):
        """ Create or update the file depending on if it already exists or not

        :param str path: Path of file to create or update
        :param str content: Text content to write into file
        """
        if os.path.exists(path):
            change = None if open(path).read() == content else 'Updated'
        else:
            change = 'Created'

        if change:
            with open(path, 'w') as fp:
                fp.write(content)

            click.echo('{} {}'.format(change, self._relative_path(path)))

    def setup_product(self):
        project_path = os.getcwd()

        name = product_name(project_path)
        sanitized_name = re.sub('[^A-Za-z]', '_', name)
        placeholder_info = '- please update <PLACEHOLDER> with appropriate value'

        tox_ini = TOX_INI_TMPL.replace('{name}', name)
        tox_ini_file = os.path.join(project_path, TOX_INI_FILE)
        self._create_or_update_file(tox_ini_file, tox_ini)

        readme_files = glob(os.path.join(project_path, 'README*'))
        if readme_files:
            readme_file = readme_files[0]
        else:
            readme_file = os.path.join(project_path, 'README.rst')
            with open(readme_file, 'w') as fp:
                fp.write(README_TMPL.format(name=name))
            click.echo('Created {} {}'.format(self._relative_path(readme_file), placeholder_info))

        coveragerc_file = os.path.join(project_path, '.coveragerc')
        self._create_or_update_file(coveragerc_file, COVERAGERC_TMPL)

        gitignore_file = os.path.join(project_path, '.gitignore')
        resp = requests.get('https://raw.githubusercontent.com/github/gitignore/master/Python.gitignore')
        gitignore_content = resp.text.replace('htmlcov', 'htmlcov/\ntextcov')
        self._create_or_update_file(gitignore_file, gitignore_content)

        setup_py_file = os.path.join(project_path, 'setup.py')
        if os.path.exists(setup_py_file):
            setup_content = open(setup_py_file).read()
            if 'wheel' not in setup_content:
                setup_content = setup_content.replace("setup_requires=['setuptools-git'],",
                                                      "setup_requires=['setuptools-git', 'wheel'],")
                self._create_or_update_file(setup_py_file, setup_content)

        else:
            requirements_file = os.path.join(project_path, 'requirements.txt')
            if not os.path.exists(requirements_file):
                with open(requirements_file, 'w') as fp:
                    pass
                click.echo('Created ' + self._relative_path(requirements_file))

            readme_name = os.path.basename(readme_file)
            requirements_name = os.path.basename(requirements_file)

            with open(setup_py_file, 'w') as fp:
                fp.write(SETUP_PY_TMPL % (name, readme_name, requirements_name))

            click.echo('Created {} {}'.format(self._relative_path(setup_py_file), placeholder_info))

        package_dir = os.path.join(project_path, sanitized_name)
        if not os.path.exists(package_dir):
            os.makedirs(package_dir)
            init_file = os.path.join(package_dir, '__init__.py')
            open(init_file, 'w').close()
            click.echo('Created ' + self._relative_path(init_file))

        test_dir = os.path.join(project_path, 'tests')
        if not os.path.exists(test_dir) and not os.path.exists(os.path.join(project_path, 'test')):
            os.makedirs(test_dir)
            test_file = os.path.join(test_dir, 'test_%s.py' % sanitized_name)
            with open(test_file, 'w') as fp:
                fp.write('def test_{}():\n    """ Test is code\'s best friend. ^_^ """'.format(sanitized_name))
            click.echo('Created ' + self._relative_path(test_file))

    def setup_workspace(self):
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
                if not skip and WSTRC_FILE not in line:
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

            if self.uninstall:
                if os.path.exists(wstrc_path):
                    os.unlink(wstrc_path)
                click.echo('Removed %s and its sourcing reference from %s'.format(WSTRC_FILE, BASHRC_FILE))
                click.echo('Please restart your bash session for the change to take effect')
                return

            fh.write('source %s\n' % WSTRC_FILE)

        with open(wstrc_path, 'w') as fh:
            fh.write(WS_FUNCTION_TEMPLATE % (os.path.abspath(sys.argv[0]), workspace_dir))
            click.echo('Added "ws" bash function with workspace directory set to ' + workspace_dir)

            if self.additional_commands:
                COMMANDS.update(self.additional_commands)

            def special(c):
                return c.startswith("'") or c.startswith('"') or c.startswith(' ')

            if self.commands or self.commands_with_aliases:
                functions = sorted([f for f in list(COMMANDS.values()) if not special(f)])
                fh.write('\n')
                for func in functions:
                    fh.write(COMMAND_FUNCTION_TEMPLATE % (func, func.lstrip('_')))
                click.echo('Added bash functions: ' + ', '.join([f for f in functions if not f.startswith('_')]))

            if self.commands_with_aliases:
                fh.write('\n')
                aliases = [item for item in sorted(list(COMMANDS.items()), key=lambda x: x[1].lstrip('_'))
                           if not item[0].startswith('_')]
                for alias, command in aliases:
                    fh.write(COMMAND_ALIAS_TEMPLATE % (alias, command.lstrip(' ')))
                click.echo('Added aliases: ' + ', '.join(["%s=%s" % (a, c.lstrip('_ ')) for a, c in aliases
                                                          if not special(c)]))
                click.echo('Added special aliases: ' + ', '.join(["%s=%s" % (a, c.lstrip('_ '))
                                                                  for a, c in aliases if special(c)]))

                fh.write(AUTO_COMPLETE_TEMPLATE)

        click.echo('To use, run "source {}" or open a new shell.'.format(WSTRC_FILE))

    def _relative_path(self, path):
        if path.startswith(os.getcwd() + os.path.sep):
            path = path[len(os.getcwd())+1:]
        return path
