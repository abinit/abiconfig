#!/usr/bin/env python
""""""
from __future__ import unicode_literals, division, print_function, absolute_import

import sys
import os
import argparse

from abiconfig.core.options import AbinitConfigureOptions, ConfigList
from abiconfig.core.termcolor import cprint


def abiconf_list(cliopts, confopts, configs):
    """List available configure options."""
    for opt in confopts.values():
        print(opt)
    return 0


def abiconf_check(cliopts, confopts, configs):
    """Check configuration files.."""
    return configs.check(confopts)


def abiconf_hostname(cliopts, confopts, configs):
    """Find configuration files for this hostname."""
    from socket import gethostname
    hostname = gethostname() if cliopts.hostname is None else cliopts.hostname
    cprint("Finding configuration files for hostname: %s" % hostname, "yellow")
    for conf in configs:
	if hostname not in conf.basename: continue
	print(conf)
    return 0


def abiconf_find(cliopts, confopts, configs):
    """Test coverage."""
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
        if cliopts.verbose: print("Listing all buildbot builders found in", modir)
        for i, builder in enumerate(builders):
            print("[%d] %s" % (i, builder))
        return 0

    builder = cliopts.builder
    if builder not in builders:
        cprint("Cannot find builder %s in %s" % (builder, builders), "red")
        return 1

    workdir = builder
    acfile = builder + ".ac"
    script = "workon.sh"
    for conf in configs:
        if conf.basename == acfile: break
    else:
        cprint("Cannot find configuration file associated to %s" % builder, "red")
        return 1

    # Look before you leap.
    if os.path.exists(workdir):
	cprint("Directory %s already exists. Returning" % workdir, "red")
	return 1
    if os.path.exists(script):
	cprint("Script %s already exists. Will execute it" % script, "yellow")
	return os.system("bash %s" % script)

    # Create build directory, add symbolic link to the ac file.
    # generare shell script to load modules, run configure and make.
    os.mkdir(workdir)
    os.chdir(workdir)
    os.symlink(conf.path, acfile)

    # Write sh script to start new with modules and run it.
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
    abiconf.py hostname                       => Find conf files for this host
    abiconf.py list                           => List configure options
    abiconf.py find                           =>
    abiconf.py check                          =>
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
    copts_parser.add_argument('-s', '--source', default=".", help='Path to the Abinit source tree')

    # Build the main parser.
    parser = argparse.ArgumentParser(epilog=str_examples(), formatter_class=argparse.RawDescriptionHelpFormatter)

    # Create the parsers for the sub-commands
    subparsers = parser.add_subparsers(dest='command', help='sub-command help', description="Valid subcommands")

    # Subparser for list command.
    p_list = subparsers.add_parser('list', parents=[copts_parser], help=abiconf_list.__doc__)

    # Subparser for check command.
    p_check = subparsers.add_parser('check', parents=[copts_parser], help=abiconf_check.__doc__)

    # Subparser for find command.
    p_hostname = subparsers.add_parser('hostname', parents=[copts_parser], help=abiconf_hostname.__doc__)
    p_hostname.add_argument("hostname", nargs="?", default=None,
                            help="Find configuration file for this hostname. If not given hostname is autodetected.")

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

    #root = find_top_srctree(start_path=cliopts.source)
    #options_conf = os.path.join(root, "config", "specs", "options.conf")
    options_conf = "/Users/gmatteo/git/abiconfig/abiconfig/options.conf"
    print("Reading configure options from %s" % os.path.relpath(options_conf))
    confopts = AbinitConfigureOptions.from_file(options_conf)

    #confdir = os.path.join(root, "doc", "build", "config-examples")
    confdir = "/Users/gmatteo/git/abiconfig/abiconfig/clusters"
    configs = ConfigList.from_dir(confdir)
    print("Found %d config files inside %s" % (len(configs), os.path.relpath(confdir)))

    # Dispatch.
    return globals()["abiconf_" + cliopts.command](cliopts, confopts, configs)


if __name__ == "__main__":
    sys.exit(main())
