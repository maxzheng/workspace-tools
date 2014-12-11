#!/usr/bin/env python2.6

import os
import setuptools


def find_files(path):
  return [os.path.join(path, f) for f in os.listdir(path)]


setuptools.setup(
  name = 'workspace-tools',
  version = '0.0.1',

  author = 'Max Zheng',
  author_email = 'mzheng@linkedin.com',

  description = open('README.md').read(),

  install_requires=[
    'brownie',
    'subprocess32',
  ],

  setup_requires=['setuptools-git'],

  package_dir={'': 'src'},
  packages=setuptools.find_packages('src'),
  include_package_data=True,

  scripts=find_files('bin'),
)
