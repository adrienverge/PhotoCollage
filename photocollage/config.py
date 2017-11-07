# -*- coding: utf-8 -*-
# Copyright (C) 2017 Joël BOURGAULT
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


# import
import logging
import os
import time
import yaml


# constant definition
FILE_OPEN_TIME_STEP = 0.32414  #: some random value between opening trials
FILE_OPEN_TIMEOUT = 2  #: in seconds

# logging configuration
logging.basicConfig(level=logging.DEBUG)
top_logger = logging.getLogger(__name__)


# classes definition
class ConfigLoadError(IOError):
    pass


class ConfigStoreError(IOError):
    pass


class YamlConfig(object):
    """Handles configuration, based on a YAML file.

    Takes care of writing configuration to filesystem at exit.

    >>> cfg_fn = "../tests/cfg.yml"
    >>> if os.path.exists(cfg_fn):
    ...     os.remove(cfg_fn)
    ...
    >>> cfg = YamlConfig(cfg_fn)
    >>> print(cfg)
    <YamlConfig object: {}>
    >>> cfg['configuration'] = dict(last_visited_directory="/home/adrien/photos")
    >>> cfg.store()
    >>> print(open(cfg_fn).read())
    configuration: {last_visited_directory: /home/adrien/photos}
    <BLANKLINE>

    >>> cfg2 = YamlConfig(cfg_fn)
    >>> cfg2.load()
    >>> print(cfg2)
    <YamlConfig object: {'configuration': {'last_visited_directory': '/home/adrien/photos'}}>

    """
    def __init__(self, cfg_fn, *args, **kwargs):
        self.logger = top_logger.getChild(__name__)
        self._data = dict(*args, **kwargs)
        self.cfg_fn = cfg_fn

    def load(self):
        """Load content of *self.cfg_fn*, as a YAML file, in instance.

        """
        self._data.clear()
        if self.cfg_fn is not None and os.path.exists(self.cfg_fn):
            try:
                with open_(self.cfg_fn, 'r') as fin:
                    self._data.update(yaml.load(fin))
            except (IOError, OSError) as e:
                raise ConfigLoadError("Could not load config file: {}"
                                      .format(e))
        else:
            raise ConfigLoadError("Could not load config: no cfg_fn "
                                  "provided")

    def store(self):
        """Write instance content to *self.cfg_fn*, as YAML file.

        """
        if self.cfg_fn is not None:
            dir_ = os.path.dirname(self.cfg_fn)
            if os.path.exists(self.cfg_fn):
                if os.path.isdir(self.cfg_fn):
                    raise ConfigStoreError("Cannot store, as cfg_fn is a "
                                           "directory : '{}'"
                                           .format(self.cfg_fn))
                else:
                    # file exists and will be overwritten: no action
                    pass
            elif os.path.exists(dir_):
                if os.path.isfile(dir_):
                    raise ConfigStoreError("Cannot store, as cfg_fn "
                                           "directory exists as a file: "
                                           "'{}'"
                                           .format(self.cfg_fn))
                else:
                    # cfg_fn directory exists: no action
                    pass
            else:
                # create directory for storing the file
                os.makedirs(dir_)

            with open_(self.cfg_fn, 'w') as fout:
                fout.write(yaml.dump(self._data))
        else:
            raise ConfigStoreError("Could not store config: no cfg_fn "
                                   "provided")

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __repr__(self):
        return "<{0} object: {1}>".format(self.__class__.__name__,
                                          self._data)

    def setdefault(self, **kwargs):
        """Set values if not already existing

        >>> cfg = YamlConfig(None)
        >>> cfg['a'] = 1
        >>> cfg.setdefault(a=0, b=2, c=3)
        >>> cfg
        <YamlConfig object: {'a': 1, 'b': 2, 'c': 3}>

        """
        for k, v in kwargs.items():
            self._data.setdefault(k, v)

    def update(self, **kwargs):
        """Update or set values

        >>> cfg = YamlConfig(None)
        >>> cfg['a'] = 1
        >>> cfg.update(a=0, b=2, c=3)
        >>> cfg
        <YamlConfig object: {'a': 0, 'b': 2, 'c': 3}>

        """
        self._data.update(kwargs)


def open_(fn, *args, **kwargs):
    """Wraps around built-in :py:func:open function, that waits for the
    resource to become free.

    *ars* and *kwargs* are passed to built-in :py:func:open function.

    ..Note:
        Some keyword arguments are reserved:

        * Parameter *timeout_* is used to set a maximum waiting time (in
          seconds). Deactivated if value is 0, default value is
          :py:const:FILE_OPEN_TIMEOUT.
        * Parameter *_top* is used for control of warning display to user.

    """
    logger = top_logger.getChild("open_")
    timeout_ = kwargs.pop("timeout_", FILE_OPEN_TIMEOUT)
    _top = kwargs.pop("_top", True)  # True by default
    if timeout_ < 0:
        raise IOError("Could not open file within timeout: {}"
                      .format(fn))
    try:
        fh = open(fn, *args, **kwargs)
    except IOError as e:
        if _top:  # if call from user, show a warning
            logger.warning("File not available: '{}', waiting for it to be"
                           " freed: {}"
                           .format(os.path.basename(fn), e))
        time.sleep(FILE_OPEN_TIME_STEP)  # then wait a little
        kwargs["timeout_"] = timeout_ - FILE_OPEN_TIME_STEP if timeout_ > 0 else 0
        kwargs["_top"] = False  # force _top at False for new try
        return open_(fn, *args, **kwargs)   # and make a new try
    else:
        logger.debug("File '{}' opened".format(os.path.basename(fn)))
        return fh


if __name__ == '__main__':
    import doctest
    doctest.testmod()
