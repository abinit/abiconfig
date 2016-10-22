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

    [spack](https://github.com/LLNL/spack)
    [easybuild](https://github.com/hpcugent/easybuild)
-->

## Getting abiconfig

<!---
From pip
--------

The easiest way to install abiconf is to use `pip`, as follows:

    pip install abiconf
-->

## From github

The developmental version is available at the [gitlab repo](https://gitlab.abinit.org/gmatteo/abiconfig).
Clone the repo with:

    git clone https://gitlab.abinit.org/gmatteo/abiconfig.git

After cloning the source, cd to the abiconfig directory and type:

    python setup.py install --user

or

    sudo python setup.py install

if you have root privileges on the machine.

Please fork the project on gitlab, if you plan to contribute to `abiconfig`,

## Using abiconf.py

Use:

    abiconfig.py hostname zenobe

to list the configuration files available for the `zenobe` machine.
If the machine name is not provided, the full list of configuration files is printed.

Use:

    abiconfig.py keys intel mkl

to find the configuration files containing the keywords: `intel` and `mkl` and

    abiconfig.py keys

to get the full list of keywords.

Once you have found a configuration file for your machine in the abiconfig database, use:

    abiconfig.py workon zenobe.ac

to compile the code.

Use

    abiconfig.py --help

to get the list of available commands and

    abiconfig.py command --help

to list the options supported by `command`.

## Contributing

Each configuration file must start with a metadata section enclosed between two `---` markers.
The text between the markers represents a dictionary in json format followed by the
Abinit configure options in normalized form (remove the initial `--` from the option name,
replace `-` with `_`).

```
#---
#{
#"hostname": "nic4",
#"author": "J. Doe",
#"date": "2016-09-30",
#"description": "Configuration file for nic4. Uses intel compilers, openmpi, mkl (sequential) and external netcdf4/hdf5",
#"keywords": ["linux", "intel", "openmpi", "mkl", "hdf5"],
#"qtype": "slurm",
#"pre_configure": [
#   "module purge",
#   "module load openmpi/1.7.5/intel2013_sp1.1.106",
#   "module load intel/mkl/64/11.1/2013_sp1.1.106",
#   "module load hdf5/1.8.13/openmpi-1.7.5-intel2013_sp1.1.106",
#   "module load netcdf/4.3.2/openmpi-1.7.5-intel2013_sp1.1.106"
# ]
#}
#---

# Abinit configure options in normalized form follows.

#install architecture-independent files in PREFIX
#prefix="~/local/"

# MPI/OpenMP
with_mpi_prefix="${MPI_HOME}"
enable_mpi="yes"
enable_mpi_io="yes"
enable_openmp="no"

# BLAS/LAPACK provided by MKL (dynamic linking)
# See https://software.intel.com/en-us/articles/intel-mkl-link-line-advisor
with_linalg_flavor="mkl"
with_linalg_libs="-L${MKLROOT}/lib/intel64 -lmkl_intel_lp64 -lmkl_core -lmkl_sequential -lpthread -lm -ldl"
```

If possible, try to avoid hard-coded values e.g. use `${MKLROOT}` instead of the full path to the MKL library.
The user is supposed to load the modules defined in the `pre_configure` section before running `configure`
and the modules with automatically set these environment variables.
The big advantage is that one link against a different MKL version by just changing the MKL module
declared in the json dictionary.

The following keywords must be defined in the json dictionary:

  * hostname

    The name of machine (mandatory). Prefer the short version over the long version
    e.g. use `hmem` instead of `hmem.ucl.ac.be`

  * date

    Creation date in the format `yyyy-mm-dd` e.g. `2011-12-24` (mandatory)

  * author

    The author of the configuration file (mandatory).

  * description

    String or list of strings with info about the configuration file (mandatory)

  * keywords

    List of strings with tags associated to the configuration file (mandatory).
    Use `abiconf.py keys` to get the list of keywords already used
    and try to re-use them for new files.

  * pre\_configure

    List of shell commands to be executed before `configure`.
    e.g. commands to load modules required to build/run the executables.
    Optional but highly recommended.

  * post\_configure

    List of shell commands to be executed after `configure`.
    Optional

  * post\_make

    List of shell commands to be executed after `make`.
    Optional

  * qtype:

    String specifying the resource manager used by the cluster e.g. `qtype: "slurm"`.
    Used by `abiconf script` command to generate a submission script template.
    Supported values: `["shell", "slurm", "pbspro", "sge", "moab", "bluegene"]`
    Optional but highly recommended.

  * qkwargs:

    Dictionary with the options that will be used to generate the template for the given `qtype`.
    Optional. `qkwargs` can be used to generate a template script that will work with the
    build specified by the ac file. For example manneback has different Slurm partions
    with nodes belonging to different families.
    The build in `manneback-gcc-openmpi.ac` is not compatible with the Harpertown/Nehalem nodes
    that must be excluded in the slurm script. To do so, we add:

```
	qkwargs": {"exclude": "mb-neh[070,201-212],mb-har[001-014],mb-har[101-116],mb-opt[111-116]"},
```

    to the json dictionary. The template generated by `abiconf script manneback-gcc-openmpi-ac` will contain:

```
	#SBATCH	--exclude=mb-neh[070,201-212],mb-har[001-014],mb-har[101-116],mb-opt[111-116]
```

    See core.qtemplate.py for the list of options that can be specified for each `qtype`.
