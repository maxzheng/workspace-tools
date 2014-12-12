import ConfigParser
import logging
import os
from StringIO import StringIO
import sys

from brownie.caching import memoize


log = logging.getLogger()
config = ConfigParser.RawConfigParser()

CONFIG_FILE = os.path.expanduser('~/.config/workspace.cfg')
DEFAULT_CONFIG_TYPE_MAP = {
  int: ['checkout.use_gitsvn_to_clone_svn_commits']
}
DEFAULT_CONFIG = """
#######################################################################################
# Define product groups to take action upon (such as ws develop)
#######################################################################################
[product_groups]
#group_name = product_checkout1 lib_checkout2


#######################################################################################
# XXX: Make changes to 'preferences' in your personal ~/.config/workspace.cfg config file by copying content below (NOT above)
#      These default preferences are meant for everyone, so don't change here.
#######################################################################################
[preferences]
# Check out SVN repo using git-svn and clone the specified # of commits. Set to 0 to disable git-svn clone.
# Higher the number, the longer it takes to clone.
checkout.use_gitsvn_to_clone_svn_commits = 10

# Directory for caching, such as checkout dependencies to be bumped
workspace.cache_directory = /var/tmp/workspace_cache
"""


def product_groups():
  """ Returns a dict with product group name mapped to products """
  return dict((group, names.split()) for group, names in config.items('product_groups'))


def get_pref(key):
  return get_config('preferences', key)


def get_config(section, key):
  """ Returns the config for the given section / key with type coercion, or None """

  get_method_map = getattr(get_config, 'get_method_map', {})
  get_method = get_method_map.get(key, 'get')

  try:
    method = getattr(config, get_method)
    return method(section, key)

  except Exception as e:
    log.warning(e)

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
  config.set(section, key, value)


def write_config_template(file_path=CONFIG_FILE):
  with open(file_path, 'w') as fp:
    sio = StringIO()
    config.write(sio)
    config_template = '#' + '\n#'.join(sio.getvalue().split('\n'))
    fp.write(config_template)


def init_config(config_content_or_files=[StringIO(DEFAULT_CONFIG), CONFIG_FILE], type_maps=DEFAULT_CONFIG_TYPE_MAP):
  """
  Read config string or file

  :param list/str config_files: Either string of config content or list of config fh/files to be loaded
  :param dict type_maps: Dict of type map to pass to set_config_types
  """

  try:
    if isinstance(config_content_or_files, str):
      config_fp = StringIO(ccof)
      config.readfp(config_fp)
    else:
      for f in config_content_or_files:
        if isinstance(f, file):
          config.readfp(f)
        else:
          config.read(f)
  except Exception as e:
    log.error(e)
    sys.exit(1)

  if not config.sections():
    log.error('No config sections defined in: %s', config_content_or_files)
    sys.exit(1)

  if type_maps:
    set_config_types(type_maps)

  return config
