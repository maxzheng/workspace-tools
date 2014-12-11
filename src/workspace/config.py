import ConfigParser
import logging
import os
import sys

from brownie.caching import memoize


log = logging.getLogger()


CONFIG_FILE = 'workspace.cfg'
CONFIG_FILES = (os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'etc', CONFIG_FILE),
                      os.path.expanduser('~/.config/' + CONFIG_FILE))
DEFAULT_CONFIGS = {
}


def product_groups():
  """ Returns a dict with product group name mapped to products """
  return dict((group, names.split()) for group, names in config().items('product_groups'))


def get_pref(key):
  return get_config('preferences', key)


def get_config(section, key):
  """ Returns the config for the given section / key with type coercion, or None """

  get_method_map = {
    'bump.check_last_commits': 'getint',
    'checkout.use_gitsvn_to_clone_svn_commits': 'getint',
    'checkout.without_branch_suffix': 'getboolean',
    'push.precommit_check': 'getboolean'
  }

  get_method = get_method_map.get(key, 'get')

  try:
    method = getattr(config(), get_method)
    return method(section, key)

  except Exception as e:
    if key in DEFAULT_CONFIGS:
      return DEFAULT_CONFIGS[key]
    else:
      log.warning("%s: %s", CONFIG_FILE, e)

  return None


def set_config(section, key, value):
  """ Sets the config value for the given section / key """
  config().set(section, key, value)


@memoize
def config():
  """ Returns a :cls:`RawConfigParser` instance for remote and local configs """

  config = ConfigParser.RawConfigParser()  # Don't set defaults here as they get injected into product_groups too

  try:
    config.read(CONFIG_FILES)
  except Exception as e:
    log.error(e)
    sys.exit(1)

  if not config.sections():
    log.error('Failed to read from config files: %s', ', '.join(CONFIG_FILES))
    sys.exit(1)

  return config
