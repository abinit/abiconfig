#!/usr/bin/env python
"""
Provides commands to interact with the collection of abiconf configuration files
and automate the compilation of Abinit on clusters.
"""
from __future__ import unicode_literals, division, print_function, absolute_import

import sys
import os
import argparse
import time
import shutil

from pprint import pprint
from socket import gethostname
from abiconfig.core.utils import get_ncpus, marquee, is_string, which, chunks
from abiconfig.core import termcolor
from abiconfig.core.termcolor import cprint
from abiconfig.core.options import AbinitConfigureOptions, ConfigMeta, Config, ConfigList, get_actemplate_string
from abiconfig.core import release


def find_top_srctree(start_path, ntrials=10):
    """
    Returns the absolute path of the ABINIT source tree.
    Assume start_path is within the source tree.

    Raises:
        `RuntimeError` if build tree is not found after ntrials attempts.
    """
    abs_path = os.path.abspath(start_path)

    trial = 0
    while trial <= ntrials:
        config_ac = os.path.join(abs_path, "configure.ac")
        abinit_f90 = os.path.join(abs_path, "src", "98_main", "abinit.F90")
        # Check if we are in the top of the ABINIT source tree
        found = os.path.isfile(config_ac) and os.path.isfile(abinit_f90)
        if found:
            return abs_path
        else:
            abs_path, tail = os.path.split(abs_path)
            trial += 1

    raise RuntimeError("Cannot find the ABINIT source tree after %s trials" % ntrials)


def abiconf_new(options):
    """Generate new configuration file."""
    template = get_actemplate_string()
    new_filename = options.new_filename
    if new_filename is None:
        new_filename = gethostname() + "-compiler-mpi-libs-extra.ac"

    with open(new_filename, "wt") as f:
        f.write(template)
    return 0


def abiconf_opts(options):
    """List available configure options."""
    confopts = AbinitConfigureOptions.from_myoptions_conf()
    if options.optnames is None or not options.optnames:
        # Print all options.
        for opt in confopts.values():
            if options.verbose:
                cprint(marquee(opt.name), "yellow")
                print(opt)
            else:
                print(repr(opt))

        if options.verbose == 0:
            print("\nUse -v for further information")
    else:
        for optname in options.optnames:
            opt = confopts[optname]
            cprint(marquee(opt.name), "yellow")
            print(opt)

    return 0


def abiconf_coverage(options):
    """Analyse the coverage of autoconf options in the Abinit test farm."""
    # Either build configs from internal directories or from command-line arguments.
    if options.paths is None:
        configs = ConfigList.get_clusters()
    else:
        if len(options.paths) == 1 and os.path.isdir(options.paths[0]):
            # Directory with files.
            configs = ConfigList.from_dir(options.paths[0])
        else:
            # List of files.
            configs = ConfigList.from_files(options.paths)

    return configs.coverage(AbinitConfigureOptions.from_myoptions_conf(), verbose=options.verbose)


def abiconf_hostname(options):
    """Find configuration files for this hostname."""

    def show_hostnames():
        cprint(marquee("List of available hostnames"), "yellow")
        all_hosts = sorted({conf.meta["hostname"] for conf in configs})
        for chunk in chunks(all_hosts, 7):
            cprint(", ".join(chunk), "blue")

    if options.show_hostnames:
        show_hostnames()
        return 0

    hostname = gethostname() if options.hostname is None else options.hostname
    #print("Finding configuration files for hostname: `%s`" % hostname)
    nfound = 0
    configs = ConfigList.get_clusters()
    for conf in configs:
        # TODO: Should handle foo.bar.be case
        #if not (hostname in conf.meta["keywords"] or hostname in conf.basename):
        if not hostname in conf.meta["hostname"]:
            continue
        nfound += 1
        cprint(marquee(conf.basename), "yellow")
        print(conf)

    if nfound == 0:
        cprint("No configuration file for `%s`. Will print internal list." % hostname, "red")
        show_hostnames()

    return 0


def abiconf_list(options):
    """List all configuration files."""
    configs = ConfigList.get_clusters()
    cprint(marquee("List of available configuration files"), "yellow")
    for i, config in enumerate(configs):
        print("[%d] %s" % (i, config.basename))
        if options.verbose:
            pprint(config.meta)
            print(92* "=")
    if options.verbose == 0: print("\nUse -v for further information")
    return 0


def abiconf_get(options):
    """Get a copy of a configuration file from its basename"""
    configs = ConfigList.get_clusters()
    if options.basename is None:
        confopts = AbinitConfigureOptions.from_myoptions_conf()
        return abiconf_list(options)

    for i, config in enumerate(configs):
        if config.basename == options.basename:
            cprint("Copying file to %s" % options.basename, "yellow")
            shutil.copy(config.path, options.basename)
            return 0
    else:
        cprint("Cannot find configuration file for %s" % options.basename, "red")
        return 1


def abiconf_keys(options):
    """Find configuration files containing keywords."""
    configs = ConfigList.get_clusters()
    if options.keys is None or not options.keys:
        # Print list of available keywords.
        all_keys = set()
        for conf in configs:
            all_keys.update(conf.meta["keywords"])

        cprint(marquee("Available keywords"), "yellow")
        for chunk in chunks(all_keys, 7):
            cprint(", ".join(chunk), "blue")

    else:
        # Find configuration files containing keywords.
        keys = options.keys
        if is_string(keys): keys = [keys]
        keys = set(keys)
        for conf in configs:
            if keys.issubset(conf.meta["keywords"]):
                print("")
                cprint(marquee(conf.basename), "yellow")
                if options.verbose:
                    print(conf)
                else:
                    pprint(conf.meta)
        if options.verbose == 0: print("\nUse -v for further information")

    return 0


def abiconf_script(options):
    """Generate submission script from configuration file."""
    path = options.path
    if path is None:
        print("Available configuration files.")
        return abiconf_list(options)

    if os.path.exists(path):
        conf = Config.from_file(path)
    else:
        configs = ConfigList.get_clusters()
        for conf in configs:
            if conf.basename == path: break
        else:
            raise ValueError("Cannot find %s in internal list" % path)

    print(conf.get_script_str())
    return 0


#def abiconf_load(options):
#    """Load modules from ac file."""
#    raise NotImplementedError("")
#    conf = Config.from_file(options.path)
#    print("Loading modules from ", conf.basename)
#
#    script = os.path.join(workdir, "source_modules.sh")
#    with open(script, "wt+") as fh:
#        fh.write("#!/bin/bash\n")
#        fh.write("# Generated by abiconf.py on %s\n" % time.strftime("%c"))
#        #fh.write("module purge\n")
#        #for module in conf.meta["modules"]:
#        #    fh.write("module load %s\n" % module)
#
#    cprint("Activating modules", "yellow")
#    retcode = os.system(". %s" % script)
#    os.system("module list")
#    for app in ("mpirun", "mpiexec", "mpif90", "mpicc"):
#        print(app, "-->", which(app))
#
#    return retcode


def abiconf_convert(options):
    """Read a configuration file without metadata section and convert it."""
    path = options.path
    try:
        Config.from_file(path)
        cprint("%s is already a valid abiconf file. Nothing to do" % path, "magenta")
        return 0
    except:
        pass

    # Build template with metadata section
    lines = ConfigMeta.get_template_lines()

    # Add it to the file.
    with open(path, "rt") as fh:
        lines += fh.readlines()
    with open(path, "wt") as fh:
        fh.writelines(lines)

    conf = Config.from_file(path)
    print(conf)
    return 0


def abiconf_workon(options):
    """
    Used by developers to compile the code with the settings and
    the modules used by one of the buildbot builders.
    """
    # If confname is not specified, print full list and return
    configs = ConfigList.get_clusters()
    if options.confname is None:
        print("Available configuration files.")
        return abiconf_list(options)

    confname = options.confname
    if os.path.exists(confname):
        # Init conf from local file
        conf = Config.from_file(confname)
    else:
        # Find it in the abiconf database.
        for conf in configs:
            if conf.basename == confname or conf.path == confname: break
        else:
            cprint("Cannot find configuration file associated to `%s`" % confname, "red")
            return 1

    if options.verbose:
        #cprint("Reading configuration file %s" % confname, "yellow")
        print("Configuration file:")
        print(conf)

    # Script must be executed inside the abinit source tree.
    #find_top_srctree(".", ntrials=0)

    cwd = os.getcwd()
    workdir = os.path.join(cwd, "_build_" + confname)
    script = os.path.join(workdir, "workon_" + confname + ".sh")
    acfile = os.path.join(workdir, conf.basename)

    # Look before you leap.
    if os.path.exists(workdir):
        if not options.remove:
            cprint("Build directory `%s` already exists. Use `-r to remove it`. Returning" % workdir, "red")
            return 1
        else:
            shutil.rmtree(workdir)

    # Create build directory, copy ac file.
    # generare shell script to load modules, run configure and make.
    print("Creating build directory", workdir)
    os.mkdir(workdir)
    shutil.copy(conf.path, acfile)

    # Write shell script to start new with modules and run it.
    has_nag = "nag" in conf.meta["keywords"]
    nthreads = options.jobs
    if nthreads == 0: nthreads = get_ncpus()

    with open(script, "w+") as fh:
        fh.write("#!/bin/bash\n")
        fh.write("# Generated by abiconf.py on %s\n" % time.strftime("%c"))
        pre_conf = conf.meta.get("pre_configure")
        if pre_conf is not None:
            for cmd in pre_conf:
                fh.write("%s\n" % cmd)

        conf_lines = [
            "[! -f __configure_done__ ] && ../configure --with-config-file='%s'\n" % os.path.basename(acfile),
            "touch __configure_done__\n",
        ]
        if has_nag:
            # taken from pre_configure_nag.sh
            conf_lines.insert(0, "sed -i -e 's/ -little/& \| -library/' -e 's/\-\\#\\#\\#/& -dryrun/' ../configure\n")
            # taken from post_configure_nag.sh
            conf_lines.append("sed -i -e 's/\t\$.FCFLAGS. \\//' src/98_main/Makefile\n")

        fh.writelines(conf_lines)

        post_conf = conf.meta.get("post_configure")
        if post_conf is not None:
            for cmd in post_conf:
                fh.write("%s\n" % cmd)

        # command > >(tee stdout.log) 2> >(tee stderr.log >&2)
        # http://stackoverflow.com/questions/692000/how-do-i-write-stderr-to-a-file-while-using-tee-with-a-pipe
        cprint("`make stdout` redirected to make.stdout file", "yellow")
        cprint("`make stderr` redirected to make.stderr file", "yellow")
        fh.write("make -j%d > >(tee make.stdout) 2> >(tee make.stderr >&2) \n" % nthreads)

        post_make = conf.meta.get("post_make")
        if post_make is not None:
            for cmd in post_make:
                fh.write("%s\n" % cmd)

        fh.write("make check\n")

        fh.seek(0)
        cprint("abiconf script:", "yellow")
        for line in fh.readlines():
            print(line, end="")

    retcode = 0
    if options.make:
	# The code gets stuck here if -jN. Should find better approach
        os.chdir(workdir)
        retcode = os.system(". %s" % script)
        if retcode != 0:
            cprint("make returned retcode %s" % retcode, "red")
            stderr_path = os.path.join(workdir, "make.stderr")
            with open(stderr_path, "rt") as fh:
                err = fh.read()
                if err:
                    cprint("Errors found in %s" % stderr_path, "red")
                    cprint(err, "red")
	os.chdir(cwd)

    return retcode


def main():
    #abiconf.py load acfile                    => Load modules from acfile. Print modules and env vars.
    #abiconf.py script basebname               =>
    def str_examples():
        return """\
Usage example:
    abiconf.py hostname [HOST]                => Find configuration files for hostname HOST.
    abiconf.py list                           => List all configuration files.
    abiconf.py keys intel mkl                 => Find configuration files with these keywords.
    abiconf.py convert acfile                 => Add metadata section to an old autoconf file.
    abiconf.py get nic4-ifort-openmpi.ac      => Get a copy of the configuration file.
    abiconf.py new [FILENAME]                 => Generate template file.
    abiconf.py doc                            => Print documented template.
    abiconf.py opts                           => List available configure options.
    abiconf.py workon abiref_gnu_5.3_debug    => Create build directory and compile the code with this
                                                 configuration file.
    abiconf.py coverage [DIRorFILEs]          => Test autoconf options coverage (option for developers).
"""

    def show_examples_and_exit(error_code=1):
        """Display the usage of the script."""
        print(str_examples())
        sys.exit(error_code)

    import argparse
    # Parent parser for common options.
    copts_parser = argparse.ArgumentParser(add_help=False)
    copts_parser.add_argument('-v', '--verbose', default=0, action='count', # -vv --> verbose=2
                              help='Verbose, can be supplied multiple times to increase verbosity.')
    copts_parser.add_argument('--no-colors', default=False, action="store_true", help='Disable ASCII colors.')

    # Build the main parser.
    parser = argparse.ArgumentParser(epilog=str_examples(), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-V', '--version', action='version', version=release.__version__)

    # Create the parsers for the sub-commands
    subparsers = parser.add_subparsers(dest='command', help='sub-command help', description="Valid subcommands")

    # Subparser for hostname command.
    p_hostname = subparsers.add_parser('hostname', parents=[copts_parser], help=abiconf_hostname.__doc__)
    p_hostname.add_argument("hostname", nargs="?", default=None,
                            help="Find configuration file for this hostname. If not given hostname is autodetected.")
    p_hostname.add_argument("-s", "--show-hostnames", default=False, action="store_true",
                            help="List available hostnames.")

    # Subparser for list command.
    p_list = subparsers.add_parser('list', parents=[copts_parser], help=abiconf_list.__doc__)

    p_get = subparsers.add_parser('get', parents=[copts_parser], help=abiconf_get.__doc__)
    p_get.add_argument("basename", nargs="?", default=None, help="Name of the configuration file.")

    # Subparser for keys command.
    p_keys = subparsers.add_parser('keys', parents=[copts_parser], help=abiconf_keys.__doc__)
    p_keys.add_argument("keys", nargs="*", default=None,
                            help="Find configuration files with these keywords. "
                                 "Show available keywords if no value is provided.")

    # Subparser for script.
    p_script = subparsers.add_parser('script', parents=[copts_parser], help=abiconf_script.__doc__)
    p_script.add_argument('path', nargs="?", default=None,
                          help="Configuration file or database entry. None to print all files.")

    # Subparser for load.
    #p_load = subparsers.add_parser('load', parents=[copts_parser], help=abiconf_load.__doc__)
    #p_load.add_argument('path', help="Configuration file.")

    # Subparser for convert.
    p_conv = subparsers.add_parser('convert', parents=[copts_parser], help=abiconf_convert.__doc__)
    p_conv.add_argument('path', help="Configuration file in old format.")

    # Subparser for new command.
    p_new = subparsers.add_parser('new', parents=[copts_parser], help=abiconf_new.__doc__)
    p_new.add_argument('new_filename', nargs="?", default=None, help="Name of new configuration file.")

    # Subparser for doc command.
    p_doc = subparsers.add_parser('doc', parents=[copts_parser], help="Print documented template.")

    # Subparser for opts command.
    p_opts = subparsers.add_parser('opts', parents=[copts_parser], help=abiconf_opts.__doc__)
    p_opts.add_argument('optnames', nargs="*", default=None, help="Select options to show.")

    # Subparser for coverage command.
    p_coverage = subparsers.add_parser('coverage', parents=[copts_parser], help=abiconf_coverage.__doc__)
    p_coverage.add_argument('paths', nargs="+", default=None, help="ac file or directory with ac files.")

    # Subparser for workon command.
    p_workon = subparsers.add_parser('workon', parents=[copts_parser], help=abiconf_workon.__doc__)
    p_workon.add_argument('confname', nargs="?", default=None,
                          help="Configuration file to be used. Either abiconf basename or local file.")
    p_workon.add_argument("-m", '--make', action="store_true", default=False, help="Run configure/make. Default: False.")
    p_workon.add_argument("-j", '--jobs', type=int, default=0, help="Number of threads used to compile/make.")
    p_workon.add_argument("-r", '--remove', default=False, action="store_true", help="Remove build directory.")

    try:
        options = parser.parse_args()
    except Exception as exc:
        show_examples_and_exit(1)

    if options.no_colors:
        # Disable colors
        termcolor.enable(False)

    if options.command == "doc":
        template = get_actemplate_string()
        print(template)
        return 0

    else:
        # Dispatch.
        return globals()["abiconf_" + options.command](options)


if __name__ == "__main__":
    sys.exit(main())
