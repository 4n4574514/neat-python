"""Does general configuration parsing; used by other classes for their configuration."""
from __future__ import print_function

import os
import warnings



from neat.six_util import iterkeys

from neat.mypy_util import cast, MYPY

if MYPY:
    import sys
    if sys.version_info[0] >= 3:
        from configparser import ConfigParser, Error
    else:
        from ConfigParser import Error, SafeConfigParser as ConfigParser

    from neat.mypy_util import (Any, List, Dict, Tuple, Union, Optional, KnownConfig, # pylint: disable=unused-import
                                Iterable, TextIO, DefaultGenomeConfig)
else:
    Iterable = list

    try:
        from configparser import ConfigParser, Error # pylint: disable=ungrouped-imports
    except ImportError:
        from ConfigParser import Error, SafeConfigParser as ConfigParser # pylint: disable=ungrouped-imports

class ConfigParameter(object):
    """Contains information about one configuration item."""
    def __init__(self,
                 name, # type: str
                 value_type, # type: type
                 default=None # type: Union[None, str, List[str], bool, int, float]
                 ):
        # type: (...) -> None
        self.name = name
        self.value_type = value_type
        self.default = default

    def __repr__(self): # type: () -> str
        if self.default is None:
            return "ConfigParameter({!r}, {!r})".format(self.name,
                                                        self.value_type)
        return "ConfigParameter({!r}, {!r}, {!r})".format(self.name,
                                                          self.value_type,
                                                          self.default)

    def parse(self,
              section, # type: str
              config_parser # type: ConfigParser
              ):
        # type: (...) -> Union[str, List[str], int, bool, float]
        if int == self.value_type:
            return config_parser.getint(section, self.name)
        if bool == self.value_type:
            return config_parser.getboolean(section, self.name)
        if float == self.value_type:
            return config_parser.getfloat(section, self.name)
        if list == self.value_type:
            v = config_parser.get(section, self.name) # type: str
            return v.split(" ")
        if str == self.value_type:
            return config_parser.get(section, self.name)

        raise RuntimeError("Unexpected configuration type: "
                           + repr(self.value_type))

    def interpret(self, config_dict):
        # type: (Dict[str, str]) -> Union[str, int, bool, float, List[str]]
        """
        Converts the config_parser output into the proper type,
        supplies defaults if available and needed, and checks for some errors.
        """
        value = config_dict.get(self.name)
        if value is None:
            if self.default is None:
                raise RuntimeError('Missing configuration item: ' + self.name)
            else:
                warnings.warn("Using default {!r} for '{!s}'".format(self.default, self.name),
                              DeprecationWarning)
                if (str != self.value_type) and isinstance(self.default, self.value_type):
                    return self.default
                else:
                    value = self.default # type: ignore

        try:
            if str == self.value_type:
                return str(value)
            if int == self.value_type:
                return int(value)
            if bool == self.value_type:
                if value.lower() == "true":
                    return True
                elif value.lower() == "false":
                    return False
                else:
                    raise RuntimeError(self.name + " must be True or False")
            if float == self.value_type:
                return float(value)
            if list == self.value_type:
                return value.split(" ")
        except Exception:
            raise RuntimeError("Error interpreting config item '{}' with value {!r} and type {}".format(
                self.name, value, self.value_type))

        raise RuntimeError("Unexpected configuration type: " + repr(self.value_type))

    def format(self, value): # type: (Union[str, int, bool, float, List[str]]) -> str
        if list == self.value_type:
            return " ".join(cast(Iterable,value))
        return str(value)


def write_pretty_params(f, config, params):
    # type: (TextIO, KnownConfig, List[ConfigParameter]) -> None
    param_names = [p.name for p in params] # type: List[str]
    longest_name = max(len(name) for name in param_names) # type: int # c_type: c_uint
    param_names.sort()
    params_dict = dict((p.name, p) for p in params) # type: Dict[str, ConfigParameter]

    for name in param_names:
        p = params_dict[name]
        f.write('{} = {}\n'.format(p.name.ljust(longest_name), p.format(getattr(config, p.name))))


class UnknownConfigItemError(NameError):
    """Error for unknown configuration option - partially to catch typos."""
    pass

class DefaultClassConfig(object):
    """
    Replaces at least some boilerplate configuration code
    for reproduction, species_set, and stagnation classes.
    """

    def __init__(self,
                 param_dict, # type: Dict[str, str]
                 param_list # type: List[ConfigParameter]
                 ):
        # type: (...) -> None
        self._params = param_list
        param_list_names = [] # type: List[str]
        for p in param_list:
            setattr(self, p.name, p.interpret(param_dict))
            param_list_names.append(p.name)
        unknown_list = [x for x in iterkeys(param_dict) if not x in param_list_names] # type: List[str]
        if unknown_list:
            if len(unknown_list) > 1:
                raise UnknownConfigItemError("Unknown configuration items:\n" +
                                             "\n\t".join(unknown_list))
            raise UnknownConfigItemError("Unknown configuration item {!s}".format(unknown_list[0]))

    @classmethod
    def write_config(cls, f, config): # type: (TextIO, DefaultClassConfig) -> None
        # pylint: disable=protected-access
        write_pretty_params(f, config, config._params)


class Config(object):
    """A simple container for user-configurable parameters of NEAT."""

    __params = [ConfigParameter('pop_size', int),
                ConfigParameter('fitness_criterion', str),
                ConfigParameter('fitness_threshold', float),
                ConfigParameter('reset_on_extinction', bool),
                ConfigParameter('no_fitness_termination', bool, False)]

    def __init__(self,
                 genome_type,
                 reproduction_type,
                 species_set_type,
                 stagnation_type,
                 filename # type: str
                 ):
        # type: (...) -> None
        # Check that the provided types have the required methods.
        assert hasattr(genome_type, 'parse_config')
        assert hasattr(reproduction_type, 'parse_config')
        assert hasattr(species_set_type, 'parse_config')
        assert hasattr(stagnation_type, 'parse_config')

        self.genome_type = genome_type
        self.reproduction_type = reproduction_type
        self.species_set_type = species_set_type
        self.stagnation_type = stagnation_type

        if not os.path.isfile(filename):
            raise Exception('No such config file: ' + os.path.abspath(filename))

        parameters = ConfigParser()
        with open(filename) as f:
            if hasattr(parameters, 'read_file'):
                parameters.read_file(f)
            else:
                parameters.readfp(f) # type: ignore

        # NEAT configuration
        if not parameters.has_section('NEAT'):
            raise RuntimeError("'NEAT' section not found in NEAT configuration file.")

        param_list_names = []
        for p in self.__params:
            if p.default is None:
                setattr(self, p.name, p.parse('NEAT', parameters))
            else:
                try:
                    setattr(self, p.name, p.parse('NEAT', parameters))
                    if getattr(self, p.name) is None:
                        setattr(self, p.name, p.default)
                except (Error, RuntimeError):
                    setattr(self, p.name, p.default)
                    warnings.warn("Using default {!r} for '{!s}'".format(p.default, p.name),
                                  DeprecationWarning)
            param_list_names.append(p.name)
        param_dict = dict(parameters.items('NEAT'))
        unknown_list = [x for x in iterkeys(param_dict) if not x in param_list_names] # type: List[str]
        if unknown_list:
            if len(unknown_list) > 1:
                raise UnknownConfigItemError("Unknown (section 'NEAT') configuration items:\n" +
                                             "\n\t".join(unknown_list))
            raise UnknownConfigItemError(
                "Unknown (section 'NEAT') configuration item {!s}".format(unknown_list[0]))


        # Parse type sections.
        genome_dict = dict(parameters.items(genome_type.__name__))
        self.genome_config = genome_type.parse_config(genome_dict) # type: DefaultGenomeConfig # XXX

        species_set_dict = dict(parameters.items(species_set_type.__name__))
        self.species_set_config = species_set_type.parse_config(species_set_dict) # type: DefaultClassConfig # XXX

        stagnation_dict = dict(parameters.items(stagnation_type.__name__))
        self.stagnation_config = stagnation_type.parse_config(stagnation_dict) # type: DefaultClassConfig # XXX

        reproduction_dict = dict(parameters.items(reproduction_type.__name__))
        self.reproduction_config = reproduction_type.parse_config(reproduction_dict) # type; DefaultClassConfig # XXX

    def save(self, filename): # type: (str) -> None
        with open(filename, 'w') as f:
            f.write('# The `NEAT` section specifies parameters particular to the NEAT algorithm\n')
            f.write('# or the experiment itself.  This is the only required section.\n')
            f.write('[NEAT]\n')
            write_pretty_params(f, self, self.__params)

            f.write('\n[{0}]\n'.format(self.genome_type.__name__))
            self.genome_type.write_config(f, self.genome_config)

            f.write('\n[{0}]\n'.format(self.species_set_type.__name__))
            self.species_set_type.write_config(f, self.species_set_config)

            f.write('\n[{0}]\n'.format(self.stagnation_type.__name__))
            self.stagnation_type.write_config(f, self.stagnation_config)

            f.write('\n[{0}]\n'.format(self.reproduction_type.__name__))
            self.reproduction_type.write_config(f, self.reproduction_config)
