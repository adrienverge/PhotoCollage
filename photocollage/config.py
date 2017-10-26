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


import yaml


class YamlConfig(object):
    """Handles configuration, based on a YAML file.

    Takes care of writing configuration to filesystem at exit.

    >>> import os
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

    """
    def __init__(self, cfg_fn, *args, **kwargs):
        self._data = dict(*args, **kwargs)
        self.cfg_fn = cfg_fn
        self.load()

    def load(self):
        self._data.clear()
        if self.cfg_fn is not None:
            try:
                with open(self.cfg_fn, 'r') as fin:
                    self._data.update(yaml.load(fin))
            except (IOError, OSError):
                pass

    def store(self):
        with open(self.cfg_fn, 'w') as fout:
            fout.write(yaml.dump(self._data))

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __repr__(self):
        return "<{0} object: {1}>".format(self.__class__.__name__,
                                          self._data)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
