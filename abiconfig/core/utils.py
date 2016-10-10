from __future__ import unicode_literals, division, print_function, absolute_import


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
