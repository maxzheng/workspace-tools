from glob import glob
import logging
import os
import sys

from workspace.scm import repo_check, product_name, repo_path
from workspace.utils import silent_run, run, split_doc

log = logging.getLogger(__name__)
DEVELOP_ACTIONS = ('devenv', 'build', 'pytest', 'precommit', 'coverage')
TOX_INI_FILE = 'tox.ini'
TOX_INI_TMPL = """\
[tox]
envlist = devenv

[testenv]
downloadcache = {toxworkdir}/_download
recreate = True
setenv =
	PIP_PROCESS_DEPENDENCY_LINKS=1
	PIP_DEFAULT_TIMEOUT=60
	ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future
basepython = python

[testenv:devenv]
commands =
	pip install -e .
	ln -sf {envbindir}/activate .
recreate = False
skipsdist = True
deps =
	pytest
	pytest-xdist
	pytest-cov
	{[testenv:precommit]deps}
	{[testenv:build]deps}
whitelist_externals =
	ln
envdir = {toxworkdir}/%s

[testenv:build]
commands =
	{envpython} setup.py "{[testenv:build]targets}"
targets = sdist
deps =
	sphinx!=1.2b2
	setuptools-git

[testenv:precommit]
commands =
	flake8 --config tox.ini src test
recreate = False
skipsdist = True
deps =
	flake8

[testenv:test]
commands =
	py.test test
deps =
	pytest
usedevelop = True

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

def setup_develop_parser(subparsers):
  doc, docs = split_doc(develop.__doc__)
  develop_parser = subparsers.add_parser('develop', aliases=['de'], description=doc, help=doc)
  develop_parser.add_argument('action', nargs='?', choices=DEVELOP_ACTIONS, default='devenv', help=docs['action'])
  group = develop_parser.add_mutually_exclusive_group()
  group.add_argument('-s', '--show', action='store_true', help=docs['show'])
  group.add_argument('-r', '--recreate', action='store_true', help=docs['recreate'])
  group.add_argument('--init', action='store_true', help=docs['init'])

  develop_parser.set_defaults(command=develop)

  return develop_parser


def develop(action='devenv', show=False, recreate=False, init=False, **kwargs):
  """ Manages development environments for product.

  :param str action: Develop action (for tox -e) to take. Defaults to devenv.
  :param bool show: Show where product dependencies are installed from and their versions in devenv.
  :param bool recreate: Completely recreate the development environment by removing the existing first
  :param bool init: Initialize development environment by setting up tox with devenv, build,
                    precommit (flake8), test, and coverage virtual environment.
  """
  repo_check()

  if show:
    show_installed_dependencies()
    sys.exit(0)

  elif init:
    init_env()
    sys.exit(0)

  tox_inis = glob('tox*.ini')
  if not tox_inis:
    log.error('No tox.ini found. Please use --init first to setup tox.')
  elif len(tox_inis) > 1:
    log.warn('More than one ini files found - will use first one: %s', ', '.join(tox_inis))

  # Strip out venv bin path to python to avoid issues with it being removed when running tox
  if hasattr(sys, 'real_prefix'):
    venv_bin = os.path.dirname(sys.prefix)
    os.environ['PATH'] = os.pathsep.join([p for p in os.environ['PATH'].split(os.pathsep)
                                          if os.path.exists(p) and not os.path.samefile(p, venv_bin)])

  cmd = ['tox', '-c', tox_inis[0], '-e', action]

  if recreate:
    cmd.append('-r')
    log.info('Recreating development environment')
    silent_run(cmd)

  elif action == 'devenv':
    log.info('Setting up development environment')
    silent_run(cmd)

  else:
    run(cmd)


def init_env():
  tox_ini = TOX_INI_TMPL % product_name(repo_path())
  tox_ini_file = os.path.join(repo_path(), TOX_INI_FILE)
  with open(tox_ini_file, 'w') as fp:
    fp.write(tox_ini)

  if tox_ini_file.startswith(os.getcwd() + os.path.sep):
    tox_ini_file = tox_ini_file[len(os.getcwd())+1:]
  log.info('Created %s', tox_ini_file)

  test_dir = os.path.join(repo_path(), 'test')
  if not os.path.exists(test_dir):
    os.makedirs(test_dir)
    test_file = os.path.join(test_dir, 'test_%s' % product_name(repo_path()).replace('-', '_'))
    with open(test_file, 'w') as fp:
      fp.write('# Placeholder for tests')

def show_installed_dependencies():
  script_template = """
import os
import pkg_resources

cwd = os.getcwd()
workspace_dir = os.path.dirname(cwd)

libs = [r.key for r in pkg_resources.get_distribution('%s').requires()]
output = []

def strip_cwd(dir):
  if dir.startswith(cwd + '/'):
    dir = dir[len(cwd):].lstrip('/')
  elif dir.startswith(workspace_dir):
    dir = os.path.join('..', dir[len(workspace_dir):].lstrip('/'))
  return dir

for lib in sorted(libs):
  try:
    dist = pkg_resources.get_distribution(lib)
    output.append('%%-25s %%-10s  %%s' %% (lib, dist.version, strip_cwd(dist.location)))
  except pkg_resources.DistributionNotFound:
    print '%%s is not installed' %% lib
  except Exception as e:
    print e

print '\\n'.join(output)
"""

  name = product_name(repo_path())
  script = script_template % name

  python = os.path.join('.tox', name, 'bin', 'python')

  if not os.path.exists(python):
    log.error('Development environment is not setup. Please run develop without --show to set it up first.')
    sys.exit()

  log.info('Product dependencies:')
  run([python, '-c', script])
