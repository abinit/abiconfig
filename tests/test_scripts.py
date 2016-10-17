# coding: utf-8
"""Test abiconf command line script."""
from __future__ import print_function, division, unicode_literals, absolute_import

import os

from scripttest import TestFileEnvironment

script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "abiconfig", "scripts"))


class TestAbiconf(object):
    verbose = "--verbose"
    script = os.path.join(script_dir, "abiconf.py")

    def test_abidoc(self):
        """Testing abiconf.py script"""
        env = TestFileEnvironment()

        # Start with --help. If this does not work...
        print(self.script)
        env.run(self.script, "--help")

        # Script must provide a version option
        #r = env.run(self.script, "--version", expect_stderr=True)
        #assert r.stderr.strip() == "%s version %s" % (os.path.basename(self.script), abilab.__version__)

        # Test hostname
        env.run(self.script, "hostname", self.verbose)
        env.run(self.script, "hostname", "zenobe", self.verbose)

        # Test list
        env.run(self.script, "list", self.verbose)

        # Test keys
        env.run(self.script, "keys", "intel", self.verbose)
        env.run(self.script, "keys", "intel", "mkl", self.verbose)

        # Test doc
        env.run(self.script, "doc", self.verbose)

        # Test opts
        env.run(self.script, "opts", self.verbose)

        # Test load
        #env.run(self.script, "load", "acfile", self.verbose)

        # Test workon
        env.run(self.script, "workon", self.verbose)
        env.run(self.script, "workon", "zenobe-intel-impi-mkl.ac", self.verbose)
