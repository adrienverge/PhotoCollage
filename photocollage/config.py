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


# built-in imports
import gettext
import logging
import os
import time

# third-party imports
import yaml

# photocollage imports
from photocollage import APP_NAME

# constant definition
FILE_OPEN_TIME_STEP = 0.32414  #: some random value between opening trials
FILE_OPEN_TIMEOUT = 2  #: in seconds

# logging configuration
top_logger = logging.getLogger(__name__)

gettext.textdomain(APP_NAME)
_ = gettext.gettext
_n = gettext.ngettext


# classes definition
class OptionsLoadError(IOError):
    pass


class OptionsStoreError(IOError):
    pass


class OptionsManager(object):
    """Handles options, as Python attributes, and load/store to filesystem.

    ..Note::
        This class does not write to filesystem. This shall be provided by
        sub-classes. In this case, take care to extend the list of
        protected names (those that will not be stored on filesystem),
        :py:attribute:_PROTECTED_NAMES.

    >>> opts = OptionsManager()
    >>> opts.a = 5
    >>> opts
    <OptionsManager object: {'a': 5}>
    >>> opts.b = 8
    >>> opts
    <OptionsManager object: {'a': 5, 'b': 8}>

    """
    _PROTECTED_NAMES = ('setdefault', 'update')

    def __init__(self, *args, **kwargs):
        self._logger = top_logger.getChild(__name__)
        self._data = dict(*args, **kwargs)

    def __getattribute__(self, item):
        if not item.startswith('_') and item not in self._PROTECTED_NAMES:
            return self._data[item]
        else:
            return super(OptionsManager, self).__getattribute__(item)

    def __setattr__(self, key, value):
        if not key.startswith('_') and key not in self._PROTECTED_NAMES:
            self._data[key] = value
        else:
            super(OptionsManager, self).__setattr__(key, value)

    def setdefault(self, **kwargs):
        """Set values if not already existing

        >>> opts = OptionsManager()
        >>> opts.a = 1
        >>> opts.setdefault(a=0, b=2, c=3)
        >>> opts
        <OptionsManager object: {'a': 1, 'b': 2, 'c': 3}>

        """
        for k, v in kwargs.items():
            self._data.setdefault(k, v)

    def update(self, **kwargs):
        """Update or set values

        >>> opts = OptionsManager()
        >>> opts.a = 1
        >>> opts.update(a=0, b=2, c=3)
        >>> opts
        <OptionsManager object: {'a': 0, 'b': 2, 'c': 3}>

        """
        self._data.update(kwargs)

    def __repr__(self):
        return "<%s object: %s>" % (self.__class__.__name__,
                                    self._data)


class YamlOptionsManager(OptionsManager):
    """Handles options, based on a YAML file.

    Takes care of writing configuration to filesystem at exit.

    >>> opts_fn = "../tests/opts.yml"
    >>> if os.path.exists(opts_fn):
    ...     os.remove(opts_fn)
    ...
    >>> opts = YamlOptionsManager(opts_fn)
    >>> print(opts)
    <YamlOptionsManager object: {}>
    >>> opts.configuration = dict(last_visited_directory="/home/adrien/photos")
    >>> opts.store()
    >>> print(open(opts_fn).read())
    configuration: {last_visited_directory: /home/adrien/photos}
    <BLANKLINE>

    >>> cfg2 = YamlOptionsManager(opts_fn)
    >>> cfg2.load()
    >>> cfg2.configuration
    {'last_visited_directory': '/home/adrien/photos'}

    """
    def __init__(self, opts_fn, *args, **kwargs):
        super(YamlOptionsManager, self).__init__(*args, **kwargs)
        self._PROTECTED_NAMES += ('load', 'store', 'opts_fn')
        self.opts_fn = opts_fn

    def load(self):
        """Load content of *self.opts_fn*, as a YAML file, in instance.

        """
        self._data.clear()
        if self.opts_fn is not None and os.path.exists(self.opts_fn):
            try:
                with open_(self.opts_fn, 'r') as fin:
                    self._data.update(yaml.load(fin))
            except (IOError, OSError) as e:
                raise OptionsLoadError(
                    _("Could not load options file: %s") % e)
        else:
            raise OptionsLoadError(
                _("Could not load options: no opts_fn provided"))

    def store(self):
        """Write instance content to *self.opts_fn*, as YAML file.

        """
        if self.opts_fn is not None:
            self._logger.debug(_("Storing config to filesystem: '%s'")
                               % self.opts_fn)
            dir_ = os.path.dirname(self.opts_fn)
            if dir_:  # no need to investigate if dir_ is ''
                if os.path.exists(self.opts_fn):
                    if os.path.isdir(self.opts_fn):
                        raise OptionsStoreError(
                            _("Cannot store, as opts_fn is a directory : "
                              "'%s'")
                            % self.opts_fn)
                    else:
                        # file exists and will be overwritten: no action
                        pass
                elif os.path.exists(dir_):
                    if os.path.isfile(dir_):
                        raise OptionsStoreError(
                            _("Cannot store, as opts_fn directory exists "
                              "as a file: '%s'")
                            % self.opts_fn)
                    else:
                        # opts_fn directory exists: no action
                        pass
                else:
                    # create directory for storing the file
                    os.makedirs(dir_)

            with open_(self.opts_fn, 'w') as fout:
                fout.write(yaml.dump(self._data))
            self._logger.debug(_("Options file written to disk: '%s'")
                               % self.opts_fn)
        else:
            raise OptionsStoreError(
                _("Could not store config: no opts_fn provided"))

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value


def open_(fn, *args, **kwargs):
    """Wraps around built-in :py:func:open function on *fn*, that waits for
    the resource to become free.

    :param fn: filename to open

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
        raise IOError(
            _("Could not open file within timeout: %s") % fn)
    try:
        fh = open(fn, *args, **kwargs)
    except IOError as e:
        if _top:  # if call from user, show a warning
            logger.warning(
                _("File not available: '%s', waiting for it to be freed: "
                  "%s")
                % (os.path.basename(fn), e))
        time.sleep(FILE_OPEN_TIME_STEP)  # then wait a little
        # update parameters for next trial
        kwargs["timeout_"] = (timeout_ - FILE_OPEN_TIME_STEP
                              if timeout_ > 0 else 0)
        kwargs["_top"] = False
        return open_(fn, *args, **kwargs)
    else:
        logger.debug("File '%s' opened" % os.path.basename(fn))
        return fh


if __name__ == '__main__':
    import doctest
    doctest.testmod()
