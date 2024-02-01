# -*- coding: utf-8 -*-
# Copyright (C) 2017 Joël Bourgault
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

import os
import unittest

from photocollage.config import OptionsManager, YamlOptionsManager


class TestOptionsManager(unittest.TestCase):
    def setUp(self):
        self.opts = OptionsManager()

    def test_set_option(self):
        self.opts.a = 1
        self.assertEqual(self.opts._data, {'a': 1})

    def test_set_second_option(self):
        self.opts.a = 1
        self.opts.b = 2
        self.assertEqual(self.opts._data, {'a': 1, 'b': 2})

    def test_setdefault(self):
        self.opts.a = 1
        self.opts.setdefault(a=0, b=2)
        self.assertEqual(self.opts._data, {'a': 1, 'b': 2})

    def test_update(self):
        self.opts.a = 1
        self.opts.update(a=0, b=2)
        self.assertEqual(self.opts._data, {'a': 0, 'b': 2})


class TestYamlOptionsManager(unittest.TestCase):
    def setUp(self):
        self.opts_fn = "opts.yml"
        self.yaml_content = "config: {last_visited_dir: /home/adrien/photos}\n"
        self.opts_content = {'last_visited_dir': '/home/adrien/photos'}

        if os.path.exists(self.opts_fn):
            os.remove(self.opts_fn)
        self.opts = YamlOptionsManager(self.opts_fn)

    def test_store(self):
        self.opts.config = self.opts_content
        self.opts.store()
        with open(self.opts_fn) as fh:
            opts_file_content = fh.read()
        self.assertEqual(opts_file_content, self.yaml_content)

    def test_read(self):
        with open(self.opts_fn, 'w') as fh:
            fh.write(self.yaml_content)
        self.opts.load()
        self.assertEqual(self.opts.config, self.opts_content)


if __name__ == '__main__':
    unittest.main()
