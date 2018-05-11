import sys
from traceback import print_tb

from click.testing import CliRunner as ClickRunner


class CliRunner(ClickRunner):
    """ Customize ClickRunner with additional helper methods to make testing easier """

    def invoke_and_assert_exit(self, expected_exit_code, *args, **kwargs):
        """
        Assert exit code, or print out stdout/stderr from Click run so we know what's going on.

        :param int expected_exit_code: The exit code that we expect to see
        :param list args: Positional args to pass to :meth:`ClickRunner.invoke`
        :param dict kwargs: Keyword args to pass to :meth:`ClickRunner.invoke`
        :return: Result from :meth:`ClickRunner.invoke`
        :raises AssertionError: if exit code is not as expected
        """
        result = self.invoke(*args, **kwargs)

        if result.exception:
            print('--- stderr from CliRunner.invoke ---')
            print(result.exception)
            print_tb(result.exception.__traceback__, file=sys.stdout)
            print('--- stderr end ---')

        if result.output:
            print('--- stdout from CliRunner.invoke ---')
            print(result.output)
            print('--- stdout end ---')

        assert expected_exit_code == result.exit_code, \
            'Expected exit code {}, but got {}'.format(expected_exit_code, result.exit_code)

        return result
