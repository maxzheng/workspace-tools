from __future__ import absolute_import
from __future__ import print_function
import argparse
import logging
import os
import pkg_resources
import re
import sys
import tempfile

import simplejson as json

from workspace.commands import AbstractCommand
from workspace.commands.helpers import expand_product_groups, ToxIni
from workspace.config import config
from workspace.scm import (product_name, repo_path, product_repos, product_path, repos,
                           workspace_path, current_branch, project_path)
from workspace.utils import run, log_exception, parallel_call

log = logging.getLogger(__name__)

TEST_RE = re.compile('\d+ (?:passed|error|failed|xfailed).* in [\d\.]+ seconds')
BUILD_RE = re.compile('BUILD SUCCESSFUL')


class Test(AbstractCommand):
    """
      Run tests and manage test environments for product.

      Extra optional boolean args (such as -s, -v, -vv, etc) are passed to py.test.

      :param list env_or_file: The tox environment to act upon, or a file to pass to py.test (only used
                               if file exists, we don't need to redevelop, and py.test is used as a command
                               for the default environements). Defaults to the envlist in tox.
      :param str repo: Repo path to test instead of current repo
      :param bool show_dependencies: Show where product dependencies are installed from and their versions.
      :param bool test_dependents: Run tests in this product and in checked out products that depends on this product.
                                   This product must be installed as editable in its dependents for the results to be useful.
                                   Most args are ignored when this is used.
      :param bool redevelop: Redevelop the test environment by installing on top of existing one.
                             This is implied if test environment does not exist, or whenever requirements.txt or
                             pinned.txt is modified after the environment was last updated.
                             Use -ro to do redevelop only without running tests.
                             Use -rr to remove the test environment first before redevelop (recreate).
      :param bool install_only: Modifier for redevelop. Perform install only without running test.
      :param bool match_test: Only run tests with method name that matches pattern
      :param bool return_output: Return test output instead of printing to stdout
      :param str num_processes: Number of processes to use when running tests in parallel
      :param list tox_cmd: Alternative tox command to run.
                           If env is passed in (from env_or_file), '-e env' will be appended as well.
      :param str tox_ini: Path to tox_ini file.
      :param dict tox_commands: Map of env to list of commands to override "[testenv:env] commands" setting for env.
                                Only used when not developing.
      :param list args: Additional args to pass to py.test
      :param bool silent: Run tox/py.test silently. Only errors are printed and followed by exit.
      :param bool debug: Turn on debug logging
      :param list install_editable: List of products or product groups to install in editable mode.
      :param list extra_args: Extra args from argparse to be passed to py.test
      :return: Dict of env to commands ran on success. If return_output is True, return a string output.
               If test_dependents is True, return a mapping of product name to the mentioned results.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('tox_commands', {})
        kwargs.setdefault('silent', False)  # Enables test output streaming for return_output=True
        super(Test, self).__init__(*args, **kwargs)

    @classmethod
    def arguments(cls):
        _, docs = cls.docs()
        return [
          cls.make_args('env_or_file', nargs='*', help=docs['env_or_file']),
          cls.make_args('-k', metavar='NAME_PATTERN', dest='match_test', help=docs['match_test']),
          cls.make_args('-n', metavar='NUM_PROCESSES', type=int, dest='num_processes', help=docs['num_processes']),
          cls.make_args('-d', '--show-dependencies', metavar='FILTER', action='store', nargs='?', help=docs['show_dependencies'], const=True),
          cls.make_args('-t', '--test-dependents', action='store_true', help=docs['test_dependents']),
          cls.make_args('-r', '--redevelop', action='count', help=docs['redevelop']),
          cls.make_args('-o', action='store_true', dest='install_only', help=argparse.SUPPRESS),
          cls.make_args('-e', '--install-editable', nargs='+', help=docs['install_editable'])
        ]

    @classmethod
    def supports_style_check(cls, repo=None):
        try:
            if not repo:
                repo = project_path()
            tox = ToxIni(repo)
            return 'style' in tox.envlist

        except Exception as e:
            log.debug(e)

        return False

    @classmethod
    def summarize(cls, tests, include_no_tests=True):
        """
          Summarize the test results

          :param dict|str tests: Map of product name to test result, or the test result of the current prod.
          :param bool include_no_tests: Include "No tests" results when there are no tests found.
          :return: A tuple of (success, list(summaries)) where success is True if all tests pass and summaries
                   is a list of passed/failed summary of each test or just str if 'tests' param is str.
        """
        prod_name = product_name()

        if isinstance(tests, dict):
            product_tests = tests
        else:
            product_tests = {}
            product_tests[prod_name] = tests

        success = True
        summaries = []

        def append_summary(summary, name=None):
            if len(product_tests) == 1:
                summaries.append(summary)
            else:
                summaries.append("%s: %s" % (name, summary))

        for name in sorted(product_tests, key=lambda n: n == prod_name or n):
            if not product_tests[name]:
                success = False
                append_summary('Test failed / No output', name)

            elif product_tests[name] is True:
                append_summary('Test successful / No output', name)

            elif 'collected 0 items' in product_tests[name] and 'error' not in product_tests[name]:
                append_summary('No tests')

            else:
                match = TEST_RE.search(product_tests[name])

                if not match:  # Fall back to build if there are no tests.
                    match = BUILD_RE.search(product_tests[name])

                if match:
                    append_summary(match.group(0), name)
                else:
                    append_summary('No test summary found in output', name)

                summary_lines = [l for l in product_tests[name].replace('xfailed', '').split('\n') if l.startswith('===')]
                if not len(summary_lines) == 2 or 'failed' in summary_lines[-1] or 'error' in summary_lines[-1]:
                    success = False

        return success, summaries if isinstance(tests, dict) else summaries[0]

    def run(self):
        if self.test_dependents:
            name = product_name()

            # Convert None to list for tuple([])
            if not self.env_or_file:
                self.env_or_file = []
            if not self.extra_args:
                self.extra_args = []

            test_args = (
              ('env_or_file', tuple(self.env_or_file)),
              ('return_output', True),
              ('num_processes', self.num_processes),
              ('silent', True),
              ('debug', self.debug),
              ('extra_args', tuple(self.extra_args))
            )

            test_repos = [repo_path()]
            test_repos.extend(r for r in repos(workspace_path()) if self.product_depends_on(r, name) and r not in test_repos)
            test_args = [(r, test_args, self.__class__) for r in test_repos]

            def test_done(result):
                name, output = result
                success, summary = self.summarize(output)

                if success:
                    log.info('%s: %s', name, summary)

                else:
                    temp_output_file = os.path.join(tempfile.gettempdir(), 'test-%s.out' % name)
                    with open(temp_output_file, 'w') as fp:
                        fp.write(output)
                    temp_output_file = 'See ' + temp_output_file

                    log.error('%s: %s', name, '\n\t'.join([summary, temp_output_file]))

            def show_remaining(completed, all_args):
                completed_repos = set(product_name(r) for r, _, _ in completed)
                all_repos = set(product_name(r) for r, _, _ in all_args)
                remaining_repos = sorted(list(all_repos - completed_repos))
                if len(remaining_repos):
                    repo = remaining_repos.pop()
                    more = '& %d more' % len(remaining_repos) if remaining_repos else ''
                    return '%s %s' % (repo, more)
                else:
                    return 'None'

            repo_results = parallel_call(test_repo, test_args, callback=test_done, show_progress=show_remaining, progress_title='Remaining')

            for _, result in list(repo_results.values()):
                success, _ = self.summarize(result)
                if not (success or self.return_output):
                    sys.exit(1)

            return dict(list(repo_results.values()))

        if not self.repo:
            self.repo = project_path()

        # Strip out venv bin path to python to avoid issues with it being removed when running tox
        if 'VIRTUAL_ENV' in os.environ:
            venv_bin = os.environ['VIRTUAL_ENV']
            os.environ['PATH'] = os.pathsep.join([p for p in os.environ['PATH'].split(os.pathsep)
                                                  if os.path.exists(p) and not p.startswith(venv_bin)])

        envs = []
        files = []

        if self.env_or_file:
            for ef in self.env_or_file:
                if os.path.exists(ef):
                    files.append(os.path.abspath(ef))
                else:
                    envs.append(ef)

        pytest_args = ''
        if self.match_test or self.num_processes is not None or files or self.extra_args:
            pytest_args = []
            if self.match_test:
                pytest_args.append('-k ' + self.match_test)
            if self.num_processes is not None:
                pytest_args.append('-n ' + str(self.num_processes))
            if self.extra_args:
                pytest_args.extend(self.extra_args)
            if files:
                pytest_args.extend(files)
            pytest_args = ' '.join(pytest_args)
            os.environ['PYTESTARGS'] = pytest_args

        tox = ToxIni(self.repo, self.tox_ini)

        if not envs:
            envs = tox.envlist

        env_commands = {}

        if self.install_only and not self.redevelop:
            self.redevelop = 1

        if self.show_dependencies:
            for env in envs:
                self.show_installed_dependencies(tox, env, filter_name=self.show_dependencies)

        elif self.install_editable:
            for env in envs:
                if len(envs) > 1:
                    print(env + ':')
                self.install_editable_dependencies(tox, env, editable_products=self.install_editable)

        elif self.redevelop:
            if self.tox_cmd:
                cmd = self.tox_cmd
            else:
                cmd = ['tox', '-c', tox.tox_ini]

            if envs:
                cmd.extend(['-e', ','.join(envs)])

            if self.redevelop > 1:
                cmd.append('-r')

            if self.install_only:
                cmd.append('--notest')

            output = run(cmd, cwd=self.repo, raises=not self.return_output, silent=self.silent, return_output=self.return_output)

            if not output:
                if self.return_output:
                    return False
                else:
                    sys.exit(1)

            for env in envs:
                env_commands[env] = ' '.join(cmd)

                # Touch envdir
                envdir = tox.envdir(env)
                if os.path.exists(envdir):
                    os.utime(envdir, None)

                # Strip entry version
                self._strip_version_from_entry_scripts(tox, env)

            if self.return_output:
                return output

        else:
            for env in envs:
                envdir = tox.envdir(env)

                def requirements_updated():
                    req_mtime = 0
                    requirements_files = ['requirements.txt', 'pinned.txt', 'tox.ini']
                    for req_file in requirements_files:
                        req_path = os.path.join(self.repo, req_file)
                        if os.path.exists(req_path):
                            req_mtime = max(req_mtime, os.stat(req_path).st_mtime)
                    return req_mtime > os.stat(envdir).st_mtime

                if not os.path.exists(envdir) or requirements_updated():
                    env_commands.update(
                        self.commander.run('test', env_or_file=[env], repo=self.repo, redevelop=True, tox_cmd=self.tox_cmd,
                                           tox_ini=self.tox_ini, tox_commands=self.tox_commands, match_test=self.match_test,
                                           num_processes=self.num_processes, silent=self.silent,
                                           debug=self.debug, extra_args=self.extra_args))
                    continue

                if len(envs) > 1 and not self.silent:
                    print(env)

                commands = self.tox_commands.get(env) or tox.commands(env)
                env_commands[env] = '\n'.join(commands)

                for command in commands:
                    full_command = os.path.join(envdir, 'bin', command)

                    command_path = full_command.split()[0]
                    if os.path.exists(command_path):
                        if 'py.test' in full_command:
                            if 'PYTESTARGS' in full_command:
                                full_command = full_command.replace('{env:PYTESTARGS:}', pytest_args)
                            else:
                                full_command += ' ' + pytest_args
                        activate = '. ' + os.path.join(envdir, 'bin', 'activate')
                        output = run(activate + '; ' + full_command, shell=True, cwd=self.repo, raises=False, silent=self.silent, return_output=self.return_output)
                        if not output:
                            if self.return_output:
                                return False
                            else:
                                sys.exit(1)

                        if env != envs[-1] and not self.silent:
                            print()

                        if self.return_output:
                            return output
                    else:
                        log.error('%s does not exist', command_path)
                        if self.return_output:
                            return False
                        else:
                            sys.exit(1)

        return env_commands

    def _strip_version_from_entry_scripts(self, tox, env):
        """ Strip out version spec "==1.2.3" from entry scripts as they require re-develop when version is changed in develop mode. """
        name = product_name(tox.path)
        script_bin = tox.bindir(env)

        if os.path.exists(script_bin):
            name_version_re = re.compile('%s==[0-9\.]+' % name)
            removed_from = []
            for script in os.listdir(script_bin):
                script_path = os.path.join(script_bin, script)

                if os.path.isfile(script_path):
                    try:
                        with open(script_path) as fp:
                            script = fp.read()

                    except Exception:
                        continue  # Binary files

                    if name_version_re.search(script):
                        new_script = name_version_re.sub(name, script)
                        with open(script_path, 'w') as fp:
                            fp.write(new_script)
                        removed_from.append(os.path.basename(script_path))

            if removed_from:
                log.debug('Removed version spec from entry script(s): %s', ', '.join(removed_from))

    def show_installed_dependencies(self, tox, env, return_output=False, filter_name=None):
        script_template = """
    import json
    import os
    import pip
    import sys

    # Required params to run this script
    package = '%s'
    json_output = %s
    env = '%s'
    filter_name = '%s'

    cwd = os.getcwd()
    workspace_dir = os.path.dirname(cwd)

    try:
      libs = [(p.key, p.version, p.location) for p in pip.get_installed_distributions()]
    except Exception as e:
      print(e)
      sys.exit(1)

    output = []

    if not json_output:
      print(env + ':')

    def strip_cwd(dir):
      if dir.startswith(cwd + '/'):
        dir = dir[len(cwd):].lstrip('/')
      elif dir.startswith(workspace_dir):
        dir = os.path.join('..', dir[len(workspace_dir):].lstrip('/'))
      return dir

    for lib, version, location in sorted(libs):
      if filter_name and filter_name not in lib:
        continue
      if json_output:
        output.append((lib, version, location))
      else:
        output.append('  %%-25s %%-10s  %%s' %% (lib, version, strip_cwd(location)))

    if json_output:
      print(json.dumps(output))
    else:
      print('\\n'.join(output))
    """

        name = product_name(tox.path)
        filter_name = isinstance(filter_name, str) and filter_name or ''
        script = script_template % (name, return_output, env, filter_name)

        python = tox.bindir(env, 'python')

        if not os.path.exists(python):
            log.error('Test environment %s is not installed. Please run without -d / --show-dependencies to install it first.', env)
            sys.exit(1)

        return run([python, '-c', script], return_output=return_output, raises=False)

    def install_editable_dependencies(self, tox, env, editable_products):
        name = product_name(tox.path)
        editable_products = expand_product_groups(editable_products)

        dependencies_output = self.show_installed_dependencies(tox, env, return_output=True)
        if not dependencies_output:
            log.debug('%s is not installed or there is no dependencies - skipping editable mode changes', name)
            return

        try:
            product_dependencies_list = json.loads(dependencies_output)
        except Exception as e:
            log.debug('Failed to get installed dependencies - skipping editable mode changes: %s', e)
            return

        product_dependencies = {}

        for dep, _, path in product_dependencies_list:
            product_dependencies[dep] = path

        available_products = [os.path.basename(r) for r in product_repos()]
        libs = [d for d in editable_products if d in available_products and d in product_dependencies and tox.workdir in product_dependencies[d]]

        already_editable = [d for d in editable_products if d in product_dependencies and tox.workdir not in product_dependencies[d]]
        for lib in already_editable:
            log.info('%s is already installed in editable mode.', lib)

        not_dependent = [d for d in editable_products if d not in product_dependencies]
        for lib in not_dependent:
            log.debug('%s is not currently installed (not a dependency) and will be ignored.', lib)

        not_available = [d for d in editable_products if d not in not_dependent and d not in available_products]
        for lib in not_available:
            log.info('%s is a dependency but not checked out in workspace, and so can not be installed in editable mode.', lib)

        pip = tox.bindir(env, 'pip')

        for lib in libs:
            if not self.silent or self.debug:
                log.info('%s: Installing %s in editable mode' % (env, lib))

            with log_exception('An error occurred when installing %s in editable mode' % lib):
                run([pip, 'uninstall', lib, '-y'], raises=False, silent=not self.debug)

                lib_path = product_path(lib)
                if os.path.exists(os.path.join(lib_path, lib, 'setup.py')):
                    lib_path = os.path.join(lib_path, lib)
                run([pip, 'install', '--editable', lib_path], silent=not self.debug)

    def product_depends_on(self, path, name):
        for req_file in config.bump.requirement_files:
            req_path = os.path.join(path, req_file)
            if os.path.exists(req_path):
                with open(req_path) as fp:
                    try:
                        reqs = pkg_resources.parse_requirements(fp.read())
                        if name in [r.project_name for r in reqs]:
                            return True
                    except:
                        pass
        return False


def test_repo(repo, test_args, test_class):
    name = product_name(repo)

    branch = current_branch(repo)
    on_branch = '#' + branch if branch != 'master' else ''
    log.info('Testing %s %s', name, on_branch)

    return name, test_class(repo=repo, **dict(test_args)).run()
