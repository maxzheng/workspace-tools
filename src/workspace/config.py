import ConfigParser
import logging
import os
import sys

from brownie.caching import memoize


log = logging.getLogger()


CONFIG_FILE = 'workspace.cfg'
CONFIG_FILES = (os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'etc', CONFIG_FILE),
                      os.path.expanduser('~/.config/' + CONFIG_FILE))
CONFIG_TYPE_MAP = {
  int: ['checkout.use_gitsvn_to_clone_svn_commits']
}

def product_groups():
  """ Returns a dict with product group name mapped to products """
  return dict((group, names.split()) for group, names in config().items('product_groups'))


def get_pref(key):
  return get_config('preferences', key)


def get_config(section, key):
  """ Returns the config for the given section / key with type coercion, or None """

  get_method_map = getattr(get_config, 'get_method_map', {})
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


def set_config_types(type_map):
  """
  Set the types of config keys.

  :param dict type_map: Mapping type to list of keys. I.e.: {int: ['key1', 'key2'], bool: ['key3']}
                        Unmapped keys default to string.
  """

  get_map = getattr(get_config, 'get_method_map', {})

  for type_, keys in type_map.items():
    if type_ is int:
      get_method = 'getint'
    elif type_ is bool:
      get_method = 'getboolean'
    else:
      continue

    get_map.update((key, get_method) for key in keys)

  get_config.get_method_map = get_map


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

  set_config_types(CONFIG_TYPE_MAP)

  return config
