import logging
import os
import pkg_resources
import re
import sys

import requests
import simplejson

from workspace.commands.commit import commit
from workspace.commands.update import update
from workspace.commands.helpers import expand_product_groups
from workspace.config import config
from workspace.scm import checkout_branch, all_branches, repo_check, is_git_repo
from workspace.utils import split_doc


log = logging.getLogger(__name__)


def setup_bump_parser(subparsers):
  doc, docs = split_doc(bump.__doc__)

  bump_parser = subparsers.add_parser('bump', description=doc, help=doc)
  bump_parser.add_argument('names', nargs='*', help=docs['names'])
  bump_parser.add_argument('-f', '--file', help=docs['file'])
  bump_parser.add_argument('-m', '--msg', help=docs['msg'])
  bump_parser.add_argument('-a', '--append', action='store_true', help=docs['append'])
  bump_parser.add_argument('-n', '--dry-run', action='store_true', help=docs['dry_run'])
  bump_parser.set_defaults(command=bump)

  return bump_parser


def bump(names=None, file=None, msg=None, append=False, dry_run=False, quiet=False, **kwargs):
  """
    Bump dependency versions in requirements.txt, pinned.txt, or any specified file.

    :param str names: Only bump dependencies that match the name.
                      Name can be a product group name defined in workspace.cfg
                      To bump to a specific version instead of latest, append version to name
                      (i.e. requests==1.2.3 or 'requests>=1.2.3'). When > or < is used, be sure to quote.
    :param str file: Requirement file to bump. Defaults to requirements.txt or pinned.txt
                     that are set by bump.requirement_files in workspace.cfg.
    :param str msg: Summary commit message to be appended
    :param bool append: Append bump changes to current branch and update existing rb if any (from .git/config)
    :param bool dry_run: Performs a dry run by printing out the changes instead of committing/creating an rb
    :param bool quiet: Be quieter by not printing certain errors and 'up to date' message. This can be used
                       to enhance bump in your own code by suppressing those errors/messages.
  """
  repo_check()

  if names:
    names = expand_product_groups(names)

  if file:
    requirement_files = [file]

  else:
    requirement_files = config.bump.requirement_files.strip().split()

  requirement_filters = {}
  if names:
    requirements = _parse_requirements(names)
    requirement_filters = dict([(r.project_name, r) for r in requirements])

  if not append and is_git_repo():
    if 'bump' in all_branches():
      log.error('There is already a "bump" branch. Please commit or delete it first before doing another bump.')
      sys.exit(1)
    checkout_branch('master')

  #update(raises=True)

  updated_requirement_files = {}
  found_requirement_file = False

  for file in requirement_files:
    if not os.path.exists(file):
      continue

    found_requirement_file = True

    with open(file) as fp:
      requirements_str = fp.read()

    requirements = []
    updated_requirements = []
    filter_matched = False

    for req in requirements_str.strip().split('\n'):
      if not req or req.startswith('#'):
        continue

      req = _parse_requirements(req, file)[0]

      if not requirement_filters or req.project_name in requirement_filters and not requirement_filters[req.project_name].specs:
        filter_matched = True
        if req.specs:
          latest_version = _latest_module_version(req.project_name)
          if latest_version not in req:
            op = req.specs[0][0]
            if op == '<':
              op = '<='
            elif op == '>':
              op = '>='
            elif op == '!=':
              log.warn('%s will not be bumped as it explicitly excludes latest version')
              op = None
            if op:
              req.specs = [(op, latest_version)]
              updated_requirements.append(str(req))

      elif req.project_name in requirement_filters and requirement_filters[req.project_name].specs:
        filter_matched = True
        if str(req) != str(requirement_filters[req.project_name]):
          req = requirement_filters[req.project_name]
          all_module_versions = _all_module_versions(req.project_name)
          if req.specs and not any(version in req for version in all_module_versions):
            log.error('There are no published versions that satisfies requirement %s', req)
            log.error('The requirement should match at least one of these: %s', ', '.join(all_module_versions[:10]))
            sys.exit(1)
          updated_requirements.append(str(req))

      requirements.append(req)

    if updated_requirements:
      if not dry_run:
        with open(file, 'w') as fp:
          for req in requirements:
            fp.write(str(req) + '\n')

      updated_requirement_files[file] = updated_requirements

  if not quiet and not found_requirement_file:
    log.error('None of the requirement file(s) were found: %s', ', '.join(requirement_files))
    sys.exit(1)

  if not quiet and not filter_matched:
    log.error('None of the specified dependencies were found in %s', file)
    sys.exit(1)

  if updated_requirement_files:
    commit_msg = ''
    for file in sorted(updated_requirement_files.keys()):
      requirements = ('\n  ').join(sorted(updated_requirement_files[file]))
      commit_msg += 'Updated %s:\n  %s\n' % (file, requirements)

    if dry_run:
      log.info("Changes that would be made:\n\n%s\n", commit_msg.strip())
    elif is_git_repo():
      branch = None if append else 'bump'
      commit(msg=commit_msg.strip(), branch=branch)
    else:
      log.info(commit_msg.replace('\n', ''))

  elif not quiet:
    log.info('No need to bump. Everything is up to date!')


def _module_info(module):
  module_json_url = 'https://pypi.python.org/pypi/%s/json' % module

  try:
    logging.getLogger('requests').setLevel(logging.WARN)
    response = requests.get(module_json_url)
    response.raise_for_status()

    return simplejson.loads(response.text)
  except Exception as e:
    raise Exception('Could not get module info from %s: %s', module_json_url, e)

def _latest_module_version(module):
  return _module_info(module)['info']['version']

def _all_module_versions(module):
  return sorted(_module_info(module)['releases'].keys(), key=lambda x: x.split(), reverse=True)

def _parse_requirements(names, in_file=None):
  try:
    return list(pkg_resources.parse_requirements(names))
  except Exception as e:
    in_file = ' in %s' % in_file if in_file else ''
    log.error(' '.join(e) + in_file)
    sys.exit(1)
