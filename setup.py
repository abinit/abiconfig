import io
import os

from setuptools import setup, find_packages
from glob import glob


# Get the long description from the relevant file
with io.open('README.md', encoding='utf-8') as f:
    long_description = f.read()


platforms = ['Linux', 'darwin']

keywords = ["ABINIT", "ab initio", "first principles"]

classifiers=[
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3.4",
    #"Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    #"License :: OSI Approved :: MIT License",
    #"Operating System :: OS Independent",
    #"Topic :: Scientific/Engineering :: Information Analysis",
    #"Topic :: Scientific/Engineering :: Physics",
    #"Topic :: Scientific/Engineering :: Chemistry",
    #"Topic :: Software Development :: Libraries :: Python Modules"
],


setup(name='abiconfig',
      version='0.0.1',
      description="Configuration files to compile ABINIT on supercomputers.",
      long_description=long_description,
      author="Matteo Giantomassi",
      author_email='gmatteo@gmail.com',
      url='https://github.com/gmatteo/abiconfig',
      license='GNU',
      platforms=platforms,
      classifiers=classifiers,
      keywords=keywords,
      packages=find_packages(),
      scripts=glob(os.path.join("abiconfig", "scripts", "*.py")),
      package_data={"abiconfig.core": ["*.conf"]},
      )
