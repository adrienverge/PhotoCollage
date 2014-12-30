# -*- coding: utf-8 -*-
"""
Copyright (C) 2014 Adrien Vergé

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import unittest
from unittest.mock import Mock, patch

from photocollage.collage import Page, Photo


class TestCollage(unittest.TestCase):
    def setUp(self):
        # Disable random in placing cells
        patch("random.choice", new=Mock(side_effect=lambda x: x[0])).start()
        self.p = Mock()

    def prevent_cell_extension(self):
        self.p.stop()
        self.p = patch("random.random", new=Mock(side_effect=lambda: 0.0))
        self.p.start()

    def force_cell_extension(self):
        self.p.stop()
        self.p = patch("random.random", new=Mock(side_effect=lambda: 1.0))
        self.p.start()

    def test_next_free_col(self):
        self.prevent_cell_extension()

        page = Page(100, 4)
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 10))
        wanted = "[25 25] [25 25]  "
        self.assertEqual(repr(page), wanted)

        page = Page(40, 4)
        page.add_cell(Photo("img", 10, 20))
        page.add_cell(Photo("img", 10, 15))
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 22))
        wanted = ("[10 20] [10 15] [10 10] [10 10]\n"
                  "        [10 22] [10 10] [10 10]")
        self.assertEqual(repr(page), wanted)

        page = Page(50, 5)
        self.force_cell_extension()
        page.add_cell(Photo("img", 10, 15))
        page.add_cell(Photo("img", 10, 10))
        self.prevent_cell_extension()
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 50))
        wanted = ("[20 30-- ------] [20 20-- ------] [10 10]\n"
                  "                                  [10 50]")
        self.assertEqual(repr(page), wanted)

if __name__ == '__main__':
    unittest.main()
