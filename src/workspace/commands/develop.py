from glob import glob
import logging
import os
import re
import sys

from workspace.scm import repo_check, product_name, repo_path
from workspace.utils import run, split_doc

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

[testenv:pytest]
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
SETUP_PY_TMPL = """\
#!/usr/bin/env python

import os
import setuptools


setuptools.setup(
  name='%s',
  version='0.0.1',

  author='<AUTHOR>',
  author_email='<AUTHOR_EMAIL>',

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
    'Topic :: Software Development :: <SUB-TOPIC>',

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

<DESCRIPTION>
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


def develop(action='devenv', show=False, recreate=False, init=False, debug=False, **kwargs):
  """
  Manages development environments for product.

  :param str action: Develop action (for tox -e) to take. Defaults to devenv.
  :param bool show: Show where product dependencies are installed from and their versions in devenv.
  :param bool recreate: Completely recreate the development environment by removing the existing first
  :param bool init: Initialize development environment by setting up tox with devenv, build,
                    precommit (flake8), test, and coverage virtual environment. Also create setup.py,
                    README.rst, and src / test directories if they don't exist.
  """
  repo_check()

  if show:
    show_installed_dependencies()
    sys.exit(0)

  elif init:
    init_env()
    sys.exit(0)

  tox_inis = glob(os.path.join(repo_path(), 'tox*.ini'))

  if not tox_inis:
    log.error('No tox.ini found. Please use --init first to setup tox.')
    sys.exit(1)

  elif len(tox_inis) > 1:
    log.warn('More than one ini files found - will use first one: %s', ', '.join(tox_inis))

  # Strip out venv bin path to python to avoid issues with it being removed when running tox
  if 'VIRTUAL_ENV' in os.environ:
    venv_bin = os.environ['VIRTUAL_ENV']
    os.environ['PATH'] = os.pathsep.join([p for p in os.environ['PATH'].split(os.pathsep)
                                          if os.path.exists(p) and not p.startswith(venv_bin)])

  cmd = ['tox', '-c', tox_inis[0], '-e', action]

  if recreate:
    cmd.append('-r')
    log.info('Recreating development environment')
    run(cmd, silent=not debug, cwd=repo_path())
    strip_version_from_entry_scripts(repo_path())

  elif action == 'devenv':
    log.info('Setting up development environment')
    run(cmd, silent=not debug, cwd=repo_path())
    strip_version_from_entry_scripts(repo_path())

  else:
    run(cmd, cwd=repo_path())


def strip_version_from_entry_scripts(repo):
  """ Strip out version spec "==1.2.3" from entry scripts as they require re-develop when version is changed in develop mode. """
  name = product_name(repo)
  script_bin = os.path.join(repo, '.tox', name, 'bin')

  if os.path.exists(script_bin):
    name_version_re = re.compile('%s==[0-9\.]+' % name)
    removed_from = []
    for script in os.listdir(script_bin):
      script_path = os.path.join(script_bin, script)

      with open(script_path) as fp:
        script = fp.read()

      if name_version_re.search(script):
        new_script = name_version_re.sub(name, script)
        with open(script_path, 'w') as fp:
          fp.write(new_script)
        removed_from.append(os.path.basename(script_path))

    if removed_from:
      log.info('Removed version spec from entry script(s): %s', ', '.join(removed_from))

def _relative_path(path):
  if path.startswith(os.getcwd() + os.path.sep):
    path = path[len(os.getcwd())+1:]
  return path


def init_env():
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

  requirements_file = os.path.join(repo_path(), 'requirements.txt')
  if not os.path.exists(requirements_file):
    with open(requirements_file, 'w') as fp:
      pass
    log.info('Created %s', _relative_path(requirements_file))

  setup_py_file = os.path.join(repo_path(), 'setup.py')
  if not os.path.exists(setup_py_file):
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

  python = os.path.join(repo_path(), '.tox', name, 'bin', 'python')

  if not os.path.exists(python):
    log.error('Development environment is not setup. Please run develop without --show to set it up first.')
    sys.exit(1)

  log.info('Product dependencies:')
  run([python, '-c', script])
