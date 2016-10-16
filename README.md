## About

This repo is a holding area for configuration files used to compile Abinit on clusters.
Each configuration files contains a header with metadata in json format followed by 
the configure options supported by the Abinit build system. 
The metadata section contains information such as the list of modules that must be loaded
to configure/execute Abinit on the cluster, a brief description of the options activated
and a list of keywords associated to the configuration file.
The configuration file can be copied directly from this repository or, alternatively,
one can install the package and use the `abiconf.py` script to search from configure scripts
by hostname, by keywords. `abiconf.py` also provides commands to automate the configuration/make procedure.
Contributions from users and sysadmins are welcome. 

<!---
Precompiled versions of Abinit are also available on the conda channel

    conda. 

Note that, for the time being, the conda versions do not support MPI 
and the binaries are statically linked against the internal version of Blas/Lapack/FFT.
They are handy especially if you want to try Abinit on your machine but they are not
supposed to be used for high-performance calculations.

For more advanced approaches to the installation of Abinit on clusters, see

    spack 
    easybuild
-->

Getting abiconfig
=================

<!---
From pip
--------

The easiest way to install abiconf is to use `pip`, as follows::

    pip install abiconf
-->

From github
-----------

The developmental version is available at the `gitlab repo <https://gitlab.abinit.org/gmatteo/abiconfig>`_. 
Clone the repo with::

    git clone git@gitlab.abinit.org:gmatteo/abiconfig.git

After cloning the source, cd to the abiconfig directory and type::

    python setup.py install --user

or 

    sudo python setup.py install

if you have root privileges on the machine.

Please fork the project on gitalb, if you plan to contribute to `abiconfig`, 

Using abiconf.py script
=======================

Use: 

```
abiconfig.py hostname zenobe
```

to list the configuration files available for the `zenobe` machine. 
If the machine name is not provided, the full list of configuration files is printed.

Use:

```
abiconfig.py keys intel mkl
```

to find the configuration files containing the keywords: `intel` and `mkl`.

Once you have found the configuration file for your machine in the abiconf database, use:

```
abiconfig.py workon zenobe.ac
```

to compile the code.

Use

```
abiconfig.py --help 
```

to get the list of available commands and 

```
abiconfig.py command --help 
```

to list the options supported by `command`.