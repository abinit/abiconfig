#!/usr/bin/env python
""""""
from __future__ import unicode_literals, division, print_function, absolute_import

import sys
import os
import argparse

from pprint import pprint
from abiconfig.core.utils import get_ncpus, marquee, is_string
from abiconfig.core.termcolor import cprint
from abiconfig.core.options import AbinitConfigureOptions, ConfigList


def abiconf_opts(cliopts, confopts, configs):
    """List available configure options."""
    for opt in confopts.values():
        print(opt)
    return 0


def abiconf_check(cliopts, confopts, configs):
    """Check configuration files.."""
    return configs.check(confopts)


def abiconf_hostname(cliopts, confopts, configs):
    """Find configuration files for this hostname."""
    def show_hostnames():
        print(marquee("List of available hostnames"))
        for h in sorted({conf.meta["hostname"] for conf in configs}):
            print(h)

    if cliopts.show_hostnames:
        show_hostnames()
        return 0

    from socket import gethostname
    hostname = gethostname() if cliopts.hostname is None else cliopts.hostname
    cprint("Finding configuration files for hostname: `%s`" % hostname, "yellow")
    nfound = 0
    for conf in configs:
	if not (hostname in conf.meta or hostname in conf.basename): continue
        nfound += 1
	print(conf)

    if nfound == 0:
        cprint("Cannot find configuration files for this hostname", "yellow")
        show_hostnames()

    return 0


def abiconf_keys(cliopts, confopts, configs):
    """Find configuration files containing keywords."""
    if cliopts.keys is None:
        # Print list of available keywords.
        all_keys = set()
        for conf in configs:
            all_keys.update(conf.meta["keywords"])

        cprint(marquee("Available keywords"), "yellow")
        for i, key in enumerate(all_keys):
            print("[%d] %s" % (i, key))

    else:
        # Find configuration files containing keywords.
        keys = cliopts.keys
        if is_string(keys): keys = [keys]
        keys = set(keys)
        for conf in configs:
            if keys.issubset(conf.meta["keywords"]):
                cprint(marquee(conf.path), "yellow")
                pprint(conf.meta)
    return 0

def abiconf_find(cliopts, confopts, configs):
    """Find configuration files matching a given condition."""
    optname = cliopts.optname
    for conf in configs:
        if optname in conf:
            print(conf[optname])
    return 0


def abiconf_workon(cliopts, confopts, configs):
    """
    Used by developers to compile the code with the settings and
    the modules used by one of the buildbot builders.
    """
    # Get list of builders from modir
    modir = "/etc/modulefiles/builders/"
    if not os.path.exists(modir):
        cprint("Cannot find module directory %s" % modir, "red")
        return 1
    builders = os.listdir(modir)

    # If builder name is not specified, print list of builders and return
    # else create build directory to compile the code.
    if cliopts.builder is None:
        if cliopts.verbose: print("Listing all buildbot builders found in `%s`" % modir)
        for i, builder in enumerate(builders):
            print("[%d] %s" % (i, builder))
        return 0

    builder = cliopts.builder
    if builder not in builders:
        cprint("Cannot find builder `%s` in `%s`" % (builder, builders), "red")
        return 1

    workdir = builder
    acfile = builder + ".ac"
    script = "_workon.sh"
    for conf in configs:
        if conf.basename == acfile: break
    else:
        cprint("Cannot find configuration file associated to builder `%s`" % builder, "red")
        return 1

    # Look before you leap.
    if os.path.exists(workdir):
	cprint("Directory `%s` already exists. Returning" % workdir, "red")
	return 1
    if os.path.exists(script):
	cprint("Script `%s` already exists. Will execute it." % script, "yellow")
	return os.system("bash %s" % script)

    # Create build directory, add symbolic link to the ac file.
    # generare shell script to load modules, run configure and make.
    os.mkdir(workdir)
    os.chdir(workdir)
    os.symlink(conf.path, acfile)

    # Write shell script to start new with modules and run it.
    has_nag = "nag" in builder
    nthreads = get_ncpus()
    with open(script, "w+") as fh:
        fh.write("#!/bin/sh\n")
        fh.write("module purge\n")
        fh.write("module load %s\n" % builder)
	if has_nag: # pre_configure_nag.sh
	    fh.write("sed -i -e 's/ -little/& \| -library/' -e 's/\-\\#\\#\\#/& -dryrun/' ../configure\n")
        fh.write("../configure --with-config-file=./%s\n" % acfile)
	if has_nag: # post_configure_nag.sh
	    fh.write("sed -i -e 's/\t\$.FCFLAGS. \\//' src/98_main/Makefile\n")
        fh.write("make -j%d > make.stdout 2> make.stderr\n" % nthreads)

	fh.seek(0)
	cprint("Executing:", "yellow")
	for line in fh.readlines():
	    print(line)

    return os.system("bash %s" % script)


def main():

    def str_examples():
        return """\
Usage example:
    abiconf.py hostname [HOST]                => Find conf files for this hostname HOST.
    abiconf.py keys intel mkl                 => Find configuration files with these keywords.
    abiconf.py find                           =>
    abiconf.py opts                           => List available configure options.
    abiconf.py check [DIRorFILEs]             => Check configuration files.
    abiconf.py workon abiref_gnu_5.3_debug    =>
"""

    def show_examples_and_exit(error_code=1):
        """Display the usage of the script."""
        print(str_examples())
        sys.exit(error_code)

    import argparse
    # Parent parser for common options.
    copts_parser = argparse.ArgumentParser(add_help=False)
    copts_parser.add_argument('-v', '--verbose', default=0, action='count', # -vv --> verbose=2
                              help='Verbose, can be supplied multiple times to increase verbosity')

    # Build the main parser.
    parser = argparse.ArgumentParser(epilog=str_examples(), formatter_class=argparse.RawDescriptionHelpFormatter)

    # Create the parsers for the sub-commands
    subparsers = parser.add_subparsers(dest='command', help='sub-command help', description="Valid subcommands")

    # Subparser for hostname command.
    p_hostname = subparsers.add_parser('hostname', parents=[copts_parser], help=abiconf_hostname.__doc__)
    p_hostname.add_argument("hostname", nargs="?", default=None,
                            help="Find configuration file for this hostname. If not given hostname is autodetected.")
    p_hostname.add_argument("-s", "--show-hostnames", default=False, action="store_true", help="List available hostnames.")

    # List configuration files containing these keywords.
    p_keys = subparsers.add_parser('keys', parents=[copts_parser], help=abiconf_hostname.__doc__)
    p_keys.add_argument("keys", nargs="?", default=None,
                            help="Find configuration files with these keywords. "
                                 "Show available keywords if no value is provided.")

    # Subparser for opts command.
    p_opts = subparsers.add_parser('opts', parents=[copts_parser], help=abiconf_opts.__doc__)

    # Subparser for check command.
    p_check = subparsers.add_parser('check', parents=[copts_parser], help=abiconf_check.__doc__)

    # Subparser for find command.
    p_find = subparsers.add_parser('find', parents=[copts_parser], help=abiconf_find.__doc__)
    p_find.add_argument('optname', default=None, help="Option name.")

    # Subparser for workon command.
    p_workon = subparsers.add_parser('workon', parents=[copts_parser], help=abiconf_workon.__doc__)
    p_workon.add_argument('builder', nargs="?", default=None, help="Name of the buildbot builder to work on."
                          "If not given, all builders available on this host are shown (use /etc/modulefiles/builders/)")

    try:
        cliopts = parser.parse_args()
    except Exception as exc:
        show_examples_and_exit(1)

    # Read configure options from my internal copy of options.conf
    confopts = AbinitConfigureOptions.from_myoptions_conf()

    dir_basenames = ["clusters"]
    configs = ConfigList.from_mydirs(dir_basenames)
    #configs = ConfigList.from_dir(confdir)
    if cliopts.verbose:
        print("Found %d configuration files in `%s`" % (len(configs), dir_basenames))

    # Dispatch.
    return globals()["abiconf_" + cliopts.command](cliopts, confopts, configs)


if __name__ == "__main__":
    sys.exit(main())
