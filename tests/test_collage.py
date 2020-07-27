# Copyright (C) 2014 Adrien Vergé
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

import unittest
from unittest.mock import Mock, patch

from photocollage.collage import Page, Photo


class TestCollage(unittest.TestCase):
    def setUp(self):
        self.p1 = Mock()
        self.p2 = Mock()

    def force_cell_position(self, pos):
        """Disable random in placing cells"""
        self.p1.stop()
        self.p1 = patch("random.choice",
                        new=Mock(side_effect=lambda x: x[pos]))
        self.p1.start()

    def prevent_cell_extension(self):
        self.p2.stop()
        self.p2 = patch("random.random", new=Mock(side_effect=lambda: 0.0))
        self.p2.start()

    def force_cell_extension(self):
        self.p2.stop()
        self.p2 = patch("random.random", new=Mock(side_effect=lambda: 1.0))
        self.p2.start()

    def test_next_free_col(self):
        self.force_cell_position(0)
        self.prevent_cell_extension()

        page = Page(100, 0.6, 4)
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 10))
        wanted = "[25 25] [25 25]  "
        self.assertEqual(repr(page), wanted)

        page = Page(40, 0.6, 4)
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

        page = Page(50, 0.6, 5)
        self.force_cell_extension()
        page.add_cell(Photo("img", 10, 15))
        page.add_cell(Photo("img", 10, 10))
        self.prevent_cell_extension()
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 50))
        wanted = ("[20 30-- ------] [20 20-- ------] [10 10]\n"
                  "                                  [10 50]")
        self.assertEqual(repr(page), wanted)

    def test_remove_empty_cols(self):
        page = Page(1, 0.6, 100)
        self.prevent_cell_extension()
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 10))
        page.remove_empty_cols()
        self.assertEqual(len(page.cols), 5)

    def test_bottom_hole_A1(self):
        """
        ----------------------
        |      |      |      |
        |      |-------------|
        |------|             |
        |      |--------------
        |      |      |
        ---------------
        """
        page = Page(30, 0.6, 3)
        self.force_cell_position(0)
        self.prevent_cell_extension()
        page.add_cell(Photo("img", 10, 15))
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 10))
        self.force_cell_extension()
        page.add_cell(Photo("img", 10, 5))
        self.prevent_cell_extension()
        page.add_cell(Photo("img", 10, 15))
        page.add_cell(Photo("img", 10, 10))

        wanted = ("[10 15] [10 10]  [10 10]\n"
                  "[10 15] [20 10-- ------]\n"
                  "        [10 10]         ")
        self.assertEqual(repr(page), wanted)

        page.remove_bottom_holes()
        wanted = ("[10 15] [10 10]  [10 10]\n"
                  "[10 15] [20 10-- ------]\n"
                  "        [20 10-- ------]")
        self.assertEqual(repr(page), wanted)

    def test_bottom_hole_A2(self):
        """
        ----------------------
        |      |      |      |
        |      |-------------|
        |------|             |
        |      |--------------
        |      |      |      |
        --------      --------
        """
        page = Page(30, 0.6, 3)
        self.force_cell_position(0)
        self.prevent_cell_extension()
        page.add_cell(Photo("img", 10, 15))
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 10))
        self.force_cell_extension()
        page.add_cell(Photo("img", 10, 5))
        self.prevent_cell_extension()
        page.add_cell(Photo("img", 10, 15))
        self.force_cell_position(1)
        page.add_cell(Photo("img", 10, 10))

        wanted = ("[10 15] [10 10]  [10 10]\n"
                  "[10 15] [20 10-- ------]\n"
                  "                 [10 10]")
        self.assertEqual(repr(page), wanted)

        page.remove_bottom_holes()
        wanted = ("[10 15] [10 10]  [10 10]\n"
                  "[10 15] [20 10-- ------]\n"
                  "        [20 10-- ------]")
        self.assertEqual(repr(page), wanted)

    def test_bottom_hole_B2(self):
        """
        ----------------------
        |      |      |      |
        |-------------|------|
        |             |      |
        ---------------------|
               |             |
               ---------------
        """
        page = Page(30, 0.6, 3)
        self.force_cell_position(0)
        self.prevent_cell_extension()
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 10))
        self.force_cell_extension()
        page.add_cell(Photo("img", 10, 5))
        self.prevent_cell_extension()
        page.add_cell(Photo("img", 10, 10))
        self.force_cell_position(2)
        self.force_cell_extension()
        page.add_cell(Photo("img", 10, 5))

        wanted = ("[10 10]  [10 10]  [10 10]\n"
                  "[20 10-- ------]  [10 10]\n"
                  "         [20 10-- ------]")
        self.assertEqual(repr(page), wanted)

        page.remove_bottom_holes()
        wanted = ("[10 10]  [10 10] [10 10]\n"
                  "[20 10-- ------] [10 10]\n"
                  "[20 10-- ------]        ")
        self.assertEqual(repr(page), wanted)

    def test_bottom_hole_B1(self):
        """
        ----------------------
        |      |      |      |
        |------|-------------|
        |      |             |
        |---------------------
        |             |
        ---------------
        """
        page = Page(30, 0.6, 3)
        self.force_cell_position(0)
        self.prevent_cell_extension()
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 10))
        page.add_cell(Photo("img", 10, 10))
        self.force_cell_extension()
        page.add_cell(Photo("img", 10, 5))
        page.add_cell(Photo("img", 10, 5))

        wanted = ("[10 10]  [10 10]  [10 10]\n"
                  "[10 10]  [20 10-- ------]\n"
                  "[20 10-- ------]         ")
        self.assertEqual(repr(page), wanted)

        page.remove_bottom_holes()
        wanted = ("[10 10] [10 10]  [10 10]\n"
                  "[10 10] [20 10-- ------]\n"
                  "        [20 10-- ------]")
        self.assertEqual(repr(page), wanted)


if __name__ == '__main__':
    unittest.main()
