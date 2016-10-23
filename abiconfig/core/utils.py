"""
Utilities. Some routines are taken from https://github.com/materialsvirtuallab/monty
"""
from __future__ import unicode_literals, division, print_function, absolute_import

import sys
import os

def get_ncpus():
    """
    Number of virtual or physical CPUs on this system
    """
    # Python 2.6+
    # May raise NonImplementedError
    try:
        import multiprocessing
        return multiprocessing.cpu_count()
    except (ImportError, NotImplementedError):
        pass

    cprint('Cannot determine number of CPUs on this system! Returning 4', "red")
    return 4


def marquee(text="", width=78, mark='='):
    """
    Return the input string centered in a 'marquee'.

    Args:
        text (str): Input string
        width (int): Width of final output string.
        mark (str): Character used to fill string.

    :Examples:

    >>> marquee('A test', width=40, mark="*")
    '**************** A test ****************'

    >>> marquee('A test', width=40, mark='-')
    '---------------- A test ----------------'

    marquee('A test',40, ' ')
    '                 A test                 '
    """
    if not text:
        return (mark*width)[:width]

    nmark = (width-len(text)-2)//len(mark)//2
    if nmark < 0:
        nmark = 0

    marks = mark * nmark
    return '%s %s %s' % (marks, text, marks)


def boxed(msg, ch="=", pad=5):
    """
    Returns a string in a box

    Args:
        msg: Input string.
        ch: Character used to form the box.
        pad: Number of characters ch added before and after msg.

    >>> print(boxed("hello", ch="*", pad=2))
    ***********
    ** hello **
    ***********
    """
    if pad > 0:
        msg = pad * ch + " " + msg.strip() + " " + pad * ch

    return "\n".join([len(msg) * ch,
                      msg,
                      len(msg) * ch,
                     ])


def make_banner(s, width=78, mark="="):
    banner = marquee(s, width=width, mark=mark)
    return "\n" + len(banner) * mark + "\n" + banner + "\n" + len(banner) * mark


def is_string(s):
    """True if s behaves like a string (duck typing test)."""
    try:
        s + " "
        return True

    except TypeError:
        return False


def which(cmd):
    """
    Returns full path to a executable.

    Args:
        cmd (str): Executable command to search for.

    Returns:
        (str) Full path to command. None if it is not found.

    Example::

        full_path_to_python = which("python")

    Taken from monty.os.path
    """
    import os
    def is_exe(fp):
        return os.path.isfile(fp) and os.access(fp, os.X_OK)

    fpath, fname = os.path.split(cmd)
    if fpath:
        if is_exe(cmd):
            return cmd
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, cmd)
            if is_exe(exe_file):
                return exe_file
    return None


def chunks(items, n):
    """
    Yield successive n-sized chunks from a list-like object.

    >>> import pprint
    >>> pprint.pprint(list(chunks(range(1, 25), 10)))
    [(1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
     (11, 12, 13, 14, 15, 16, 17, 18, 19, 20),
     (21, 22, 23, 24)]
    """
    import itertools
    it = iter(items)
    chunk = tuple(itertools.islice(it, n))
    while chunk:
        yield chunk
        chunk = tuple(itertools.islice(it, n))


def pprint_table(table, out=sys.stdout, rstrip=False):
    """
    Prints out a table of data, padded for alignment
    Each row must have the same number of columns.

    Args:
        out:
            Output stream (file-like object)
        table:
            The table to print. A list of lists.
        rstrip:
            if true, trailing withespaces are removed from the entries.
    """
    def max_width_col(table, col_idx):
        """Get the maximum width of the given column index"""
        return max([len(row[col_idx]) for row in table])

    if rstrip:
        for row_idx, row in enumerate(table):
            table[row_idx] = [c.rstrip() for c in row]

    col_paddings = []
    ncols = len(table[0])
    for i in range(ncols):
        col_paddings.append(max_width_col(table, i))

    for row in table:
        # left col
        out.write( row[0].ljust(col_paddings[0] + 1) )
        # rest of the cols
        for i in range(1, len(row)):
            col = row[i].rjust(col_paddings[i] + 2)
            out.write(col)
        out.write("\n")


def find_abinit_toptree(start_path=".", ntrials=20):
    """
    Returns the absolute path of the ABINIT source tree.
    Assume start_path is within the source tree.

    Return None if build tree is not found after ntrials attempts.
    """
    abs_path = os.path.abspath(start_path)

    trial = 1
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

    print("Cannot find the ABINIT source tree after %s trials" % ntrials)
    return None
