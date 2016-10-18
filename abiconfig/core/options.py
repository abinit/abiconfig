from __future__ import unicode_literals, division, print_function, absolute_import

import sys
import os
import re
import json

from collections import OrderedDict, defaultdict
from pprint import pformat
from datetime import datetime, date
from abiconfig.core.utils import is_string, marquee
from abiconfig.core.termcolor import cprint


def rmquotes(s):
    """Remove quotation marks from string"""
    s = s.strip()
    s = re.sub(r'^"|"$', "", s)
    s = re.sub(r"^'|'$", "", s)
    return s


def get_actemplate_string():
    """
    Return string with autoconf template.
    """
    with open(os.path.join(os.path.dirname(__file__), "config-template.ac"), "rt") as f:
        return f.read()


class Option(object):
    """
    The recognized attributes are the following:

      * description : mandatory attribute, with no default value,
		      containing a short description of what the option does;

      * values      : optional attribute, defining the permitted values of
		      the option, as follows:

			* @includes : include flags ('-I...');
			* @integer  : integer values;
			* @libs     : library flags ('-L... -l...);
			* any space-separated enumeration of strings;

		      for 'enable_*' options, 'values' defaults to 'no yes';

      * default     : optional attribute, setting the default value of
		      the option, which must be compatible with 'values';
		      if omitted, the option will be left unset;

      * status      : mandatory attribute, set as 'stable' in the '[DEFAULT]'
		      section, which can be one of the following:

			* changed <what_changed> (e.g. 'changed meaning'),
			  when the name of the option did not change;
			* dropped, for long-removed options;
			* hidden, for options belonging to a subsystem;
			* new, for new options;
			* obsolete, for soon-to-be-removed options;
			* renamed <old_name>, for renamed options;
			* removed, for removed options;
			* stable, for unchanged options (expected default);

		      NOTE: all new options must be set with
			   'status = new';

      * group       : mandatory attribute, specifying under which category
		      the option will be displayed; must be a single word
		      corresponding to a group option defined in this
		      file;

      * help        : mandatory attribute, containing the help text of the
		      option; if 'values' is defined, each of them must be
		      described in a " * value: explanation" list;

      * defines     : optional attribute, specifying a space-separated
		      list of C preprocessing macros associated to the
		      option, which will be set to 1 if the option is set
		      to 'yes' (case-sensitive, 'enable_*' options only);
		      prepending a '!' to a macro name will define it when
		      the option is set to 'no';

      * conditionals: optional attribute, specifying a space-separated
		      list of Makefile conditionals associated to the
		      option, which will be triggered if the option is
		      set to 'yes' (case-sensitive, 'enable_*' options
		      only); prepending a '!' to a conditional name will
		      trigger it when the option is set to 'no'.

    Notes:

      * Though the 'description' attribute must always be provided, 'status'
	may be omitted if it equals its default value (see '[DEFAULT]'
	section).

      * The option groups must start with 'group_'.
    """
    def __init__(self, name, parser):
        self.name = name
        self.description = parser.get(name, "description")
        self.values = parser.myget(name, "values", "").split()
        self.default = parser.myget(name, "default", None)
        self.status = parser.get(name, "status")
        self.group = parser.myget(name, "group", None)  # This is not mandatory!
        self.help = parser.myget(name, "help", "None")  # This is not mandatory!
        self.defines = parser.myget(name, "defines", "").split()
        self.conditionals = parser.myget(name, "conditionals", "").split()

        # Replace ['@libs'] with []
        if len(self.values) == 1 and self.values[0].startswith("@"):
            self.values = []

    def __repr__(self):
        return "<name=%s, default=%s, status=%s>" % (self.name, self.default, self.status)

    def __str__(self):
        lines = []
        app = lines.append
        app("name = %s" % self.name)
        app("description = %s" % self.description)
        app("values = %s" % str(self.values))
        app("default = %s" % self.default)
        app("status = %s" % self.status)
        app("group = %s" % self.group)
        app("help = %s" % self.help)
        app("defines = %s" % str(self.defines))
        app("conditionals = %s" % str(self.conditionals))
        return "\n".join(lines)

    #def validate(self, value):
    #    if not self.values: return []
    #    errors = []
    #    return errors


try:
    import ConfigParser as configparser
except ImportError:
    # py3k
    import configparser


class MyConfigParser(configparser.ConfigParser):

    def myget(self, section, option, default):
        """Return default if option is not present in section."""
        try:
            return self.get(section, option)
        except configparser.NoOptionError:
            return default


class AbinitConfigureOptions(OrderedDict):
    """
    Stores information on the options supported by the Abinit configure script.
    Dictionary: option_name --> Option instance
    """
    @classmethod
    def from_myoptions_conf(cls):
        """Read configure options from my internal copy of options.conf"""
        options_conf = os.path.join(os.path.dirname(__file__), "options.conf")
        return cls.from_file(options_conf)

    @classmethod
    def from_file(cls, path):
        """Build the object from the options.conf file."""
        # Init INI parser
        parser = MyConfigParser()
        parser.read(path)

        new = cls()
        for arg in sorted(parser.sections()):
            new[arg] = Option(arg, parser)
        return new

    def __str__(self):
        return "\n".join(repr(opt) for opt in self.values())


def is_string_list(obj):
    return isinstance(obj, (list, tuple)) and all(is_string(s) for s in obj)

def is_description(obj):
    """True if valid description entry."""
    if is_string(obj): return True
    if isinstance(obj, (list, tuple)):
        return all(is_string(s) for s in obj)
    return False


def is_valid_date(obj):
    """Want date in the format `2011-12-24`"""
    if not is_string(obj): return False
    datetime.strptime(obj, "%Y-%m-%d")
    return True


class ConfigMeta(dict):
    """
    hostname
    author
    date
    description
    keywords
    pre_configure
    post_configure
    post_make
    """

    reqkey_validator = [
        ("hostname", is_string),
        ("author", is_string),
        ("date", is_valid_date),
        ("description", is_description),
        ("keywords", is_string_list),
        #("pre_configure", is_string_list),
        #("post_configure", is_string_list),
        #("post_make", is_string_list),
    ]

    @classmethod
    def get_template_lines(cls):
        """
        Return template (list of strings). Useful if we have to add the metadata section
        to a pre-existen configure file.
        """
        from socket import gethostname
        d = {"hostname": gethostname(),
             "author": "J. Doe",
             "date": str(date.today()),
             "description": "description",
             "keywords": [""],
             "pre_configure": [""],
        }
        #new = cls(**d)
        #errors = new.validate()
        #if errors: raise ValueError(str(errors))

        lines = json.dumps(d, indent=4).splitlines()
        for i in range(len(lines)):
            lines[i] = "# " + lines[i]

        # Add markers.
        lines.insert(0, "#---")
        lines.append("#---")

        return [l + "\n" for l in lines]

    def __init__(self, *args, **kwargs):
        super(ConfigMeta, self).__init__(*args, **kwargs)

        # description could be either a string or a list of strings.
        # If list, a newline is added at the end of each item and a single string is built.
        if isinstance(self["description"], (list, tuple)):
            lines = []
            for l in self["description"]:
                if not l.endswith("\n"): l += "\n"
                lines.append(l)
            self["description"] = "".join(lines)

        # Add hostname to keywords.
        if self["hostname"] not in self["keywords"]:
            self["keywords"].append(self["hostname"])

    def validate(self):
        """Poor-man validation. Return list of errors (strings)."""
        errors = []
        eapp = errors.append
        for key, validator in self.reqkey_validator:
            if key not in self:
                eapp("Missing key: %s" % key)
            else:
                if not validator(self[key]):
                    eapp("Wrong value for key: %s. Got type: %s" % (key, type(self[key])))

        return errors


class Config(OrderedDict):
    """
    Store configuration options read from an abinit .ac file.
    Essentially, a mapping option name --> value.

    Attributes:

        path:

        basename:

        meta: dictionary with metadata (see ConfigMeta)
    """
    @classmethod
    def from_file(cls, path):
        """
        Initialize the object from an .ac file.
        """
        path = os.path.abspath(path)
        new = cls()
        new.path = path
        new.basename = os.path.basename(path)

        with open(path, "rt") as fh:
            lines = fh.readlines()

            # Read header with metadata.
            inmeta, meta = 0, []
            for line in lines:
                if line.startswith("#---"): inmeta += 1
                if inmeta == 2: break
                if inmeta and not line.startswith("#---"):
                    meta.append(line.replace("#", "", 1))

            try:
                new._parse_meta("".join(meta))
            except:
                # FIXME: This is to support config file with metadata (e.g. buildbot ac files)
                raise
                pass

            # FIXME: Add support for
            """
            with_linalg_libs="-L${EBROOTIMKL}/mkl/lib/intel64 \
                -Wl,--start-group -lmkl_intel_lp64 -lmkl_sequential -lmkl_core -Wl,--end-group -lpthread -lm"
            """

            for line in lines:
                line = line.strip()
                if line.startswith("#") or not line: continue
                i = line.index("=")
                name, value = line[:i], line[i+1:]
                # Remove double quote from string.
                # Call it twice to handle optname=""value""
                for i in range(2): value = rmquotes(value)
                new[name] = value

        return new

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.path)

    def __str__(self):
        return self.to_string()

    def to_string(self):
        """String representation."""
        lines = [self.path, " "]
        lines.extend([pformat(self.meta, indent=2), " "])
        lines.extend("%s=%s" % (k, v) for k, v in self.items())
        return "\n".join(lines)

    def _parse_meta(self, s):
        self.meta = ConfigMeta(**json.loads(s))

        errors = []
        eapp = errors.append
        if not self.meta:
            eapp("Empty metadata section")

        elist = self.meta.validate()
        if elist:
            errors.extend(elist)

        if errors:
            raise ValueError("Wrong metadata section in file: %s\n%s" % (self.path, "\n".join(errors)))


class ConfigList(list):
    """
    List of Config object. It's usually initialized from a directory containing .ac files.
    """
    @classmethod
    def from_mydirs(cls, dir_basenames):
        """
        Initialize ConfiList from abiconf directories.

        Args:
            dir_basenames: List with directory basenames e.g. ["clusters"]
        """
        root = os.path.join(os.path.dirname(__file__), "..")

        new = ConfigList()
        for d in dir_basenames:
            dirpath = os.path.join(root, d)
            new.extend(cls.from_dir(dirpath))
        return new

    @classmethod
    def from_dir(cls, top):
        """Parse all .ac files starting located inside directory top."""
        new = cls()

        for dirpath, dirnames, filenames in os.walk(top):
            for f in filenames:
                if not f.endswith(".ac"): continue
                path = os.path.join(dirpath, f)
                try:
                    new.append(Config.from_file(path))
                except Exception as exc:
                    cprint("Exception while parsing %s:\n%s" % (path, str(exc)), "red")
                    raise

        return new

    @classmethod
    def from_files(cls, files):
        new = cls()
        for f in files:
            if not f.endswith(".ac"): continue
            try:
                new.append(Config.from_file(f))
            except Exception as exc:
                cprint("Exception while parsing %s:\n%s" % (f, str(exc)), "red")
                raise
        return new

    def coverage(self, options, verbose=0):
        # Init mapping option.name --> [(config0.path, value0), (config1.path, value1), ...]
        # This dict is used to test if all the options are tested in the configuration files:
        #       - empty list --> the option is never used.
        #       - non-empty list --> the option is used in len(list) files.
        #         An additional check on the values may be required at the end.
        retcode = 0
        optmap = {optname: [] for optname in options}

        # Mapping: config.path --> list_of_errors
        config_errors = defaultdict(list)

        # Ignore these options.
        builtin_opts = set(["CPP", "CC", "CFLAGS", "CXX", "FC", "FCFLAGS", "AR", "ARFLAGS_EXTRA",
                            "MPI_RUNNER", "CFLAGS_EXTRA", "CXXFLAGS", "FCFLAGS_EXTRA", "RANLIB",
                            "NM", "LD", "CPPFLAGS_EXTRA", "FC_LDFLAGS_EXTRA", "FPPFLAGS", "NVCC",
                            "NVCC_CFLAGS", "CC_LIBS_EXTRA", "FC_LIBS_EXTRA",
			    ])

        for conf in self:
            for name, value in conf.items():
                if name in builtin_opts or name.startswith("fcflags_opt"): continue
                if name not in options:
                    config_errors[conf.path].append("Unknown option: %s" % name)
                    retcode += 1
                    continue
                opt = options[name]
                #if opt.status in ("dropped", "removed"):
                #value_errors = opt.validate(value)
                #if value_errors: config_errors[conf.path].extend(value_errors)
                optmap[name].append((conf.path, value))

        # Print errors detected in configuration files.
        if config_errors:
            retcode += 1
            cprint("Found %d erroneous configuration files" % len(config_errors), "red")
            for path, errors in config_errors.items():
                cprint("In configuration file: %s" % path, "red")
                for i, err in enumerate(errors):
                    print("[%d] %s" % (i, err))
                print(90 * "-")

        # Print possible problems detected in optmap.
        optval_usage = {}
        for name, tuples in optmap.items():
            #count[name] = len(tuples)
            if not tuples:
                retcode += 1
                cprint("%s is never used" % name, "magenta")
            else:
                #print("%s is used in %s configuration files" % (name, len(tuples)))
                opt = options[name]
                if opt.values:
		    # Test if all values are tested in the config file.
                    optval_usage[name] = {v: [] for v in opt.values}
                    #print(d[name])
                    for path, val in tuples:
                        if "+" not in val:
                            optval_usage[name][val].append(path)
                        else:
			    # handle "mkl+magma" case
                            for v in val.split("+"):
                                optval_usage[name][v].append(path)

        i = 0
        for name, d in optval_usage.items():
            if all(l for l in d.values()): continue
            i += 1
            if i == 1:
                print(" ")
                cprint("The following values are never used in the config files", "yellow")
                retcode += 1
            cprint("[%s]" % name, "yellow")
            for k, l in d.items():
                if not l: cprint(k, "yellow")

        return retcode