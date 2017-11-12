from __future__ import division, print_function, absolute_import

import io
import os

from setuptools import setup, find_packages
from glob import glob
from abiconfig.core import release

# Get the long description from the relevant file
with io.open('README.md', encoding='utf-8') as f:
    long_description = f.read()

platforms = ['Linux', 'darwin']

keywords = ["ABINIT", "ab initio", "first principles", "configuration files"]

classifiers=[
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: GPL License",
    "Operating System :: OS Independent",
    "Topic :: Scientific/Engineering :: Physics",
    "Topic :: Scientific/Engineering :: Chemistry",
    "Topic :: Software Development :: Libraries :: Python Modules"
],

setup(name='abiconfig',
      version=release.__version__,
      description="Configuration files to compile ABINIT on supercomputers.",
      long_description=long_description,
      author="Matteo Giantomassi",
      author_email='gmatteo@gmail.com',
      url='https://github.com/gmatteo/abiconfig',
      license='GPL',
      platforms=platforms,
      classifiers=classifiers,
      keywords=keywords,
      packages=find_packages(),
      scripts=glob(os.path.join("abiconfig", "scripts", "*.py")),
      package_data={
            "abiconfig.core": ["*.conf", "*.ac"],
            "abiconfig.clusters": ["*.ac"],
        },
      )
