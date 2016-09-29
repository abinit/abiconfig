#!/usr/bin/env python
""""""
from __future__ import unicode_literals, division, print_function, absolute_import

import sys
import os
import argparse


def main():

    def str_examples():
        return """\
Usage example:
    abiconfig.py search
    abiconfig.py list
    abiconfig.py
"""

    def show_examples_and_exit(err_msg=None, error_code=1):
        """Display the usage of the script."""
        sys.stderr.write(str_examples())
        if err_msg: sys.stderr.write("Fatal Error\n" + err_msg + "\n")
        sys.exit(error_code)

    parser = argparse.ArgumentParser(epilog=str_examples(), formatter_class=argparse.RawDescriptionHelpFormatter)
    #parser.add_argument('-V', '--version', action='version', version="%(prog)s version " + abilab.__version__)

    # Parent parser for common options.
    copts_parser = argparse.ArgumentParser(add_help=False)
    copts_parser.add_argument('-v', '--verbose', default=0, action='count', # -vv --> verbose=2
                              help='verbose, can be supplied multiple times to increase verbosity')
    copts_parser.add_argument('--loglevel', default="ERROR", type=str,
                              help="set the loglevel. Possible values: CRITICAL, ERROR (default), WARNING, INFO, DEBUG")

    # Create the parsers for the sub-commands
    subparsers = parser.add_subparsers(dest='command', help='sub-command help',
                                       description="Valid subcommands, use command --help for help")

    # Subparser for convert command.
    #p_convert = subparsers.add_parser('convert', parents=[copts_parser, path_selector],
    #                                  help="Convert structure to the specified format.")
    #p_convert.add_argument('format', nargs="?", default="cif", type=str,
    #                       help="Format of the output file (cif, cssr, POSCAR, json, mson, abivars).")

    # Parse command line.
    try:
        options = parser.parse_args()
    except Exception as exc:
        show_examples_and_exit(error_code=1)

    # loglevel is bound to the string value obtained from the command line argument.
    # Convert to upper case to allow the user to specify --loglevel=DEBUG or --loglevel=debug
    import logging
    numeric_level = getattr(logging, options.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % options.loglevel)
    logging.basicConfig(level=numeric_level)

    #if options.command == "":

    return 0


if __name__ == "__main__":
    sys.exit(main())
