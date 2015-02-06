#!/usr/bin/env python2.6

import os
import setuptools


def find_files(path):
  return [os.path.join(path, f) for f in os.listdir(path)]


setuptools.setup(
  name='workspace-tools',
  version='0.7.1',

  author='Max Zheng',
  author_email='maxzheng.os @t gmail.com',

  description=open('README.rst').read(),

  entry_points={
    'console_scripts': [
      'wst = workspace.controller:main',
    ],
  },

  install_requires=open('requirements.txt').read(),

  license='MIT',

  package_dir={'': 'src'},
  packages=setuptools.find_packages('src'),
  include_package_data=True,

  setup_requires=['setuptools-git'],

  classifiers=[
    'Development Status :: 5 - Production/Stable',

    'Intended Audience :: Developers',
    'Topic :: Software Development :: Development Tools',

    'License :: OSI Approved :: MIT License',

    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
  ],

  keywords='git svn scm development tools',
)
