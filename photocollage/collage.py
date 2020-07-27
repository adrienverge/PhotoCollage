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

import random

"""
Summary of collage objects:

----------------------
|                    |
|                    |
|       Page         |       The "Page" object represents the whole page that
|                    |       will give the final assembled image.
|                    |
----------------------

----------------------
|      |      |      |
|      |Column|      |
|      |      |Column|       A page is divided into columns.
|Column|      |      |
|      |      |      |
----------------------

----------------------
| Cell | Cell        |                   Each column contains cells. When a
|------|          x--|----- CellExtent   is located in several columns,
| Cell |-------------|                   its "extended" flag is set, and a
|------| Cell |      |                   CellExtent object is added to the
| Cell |      | Cell |                   column on the right to reserve the
----------------------                   place.

      ,------> Photo
     /          ,---------> Photo
----------------------
|      |             |                   Each cell is associated
|------|             |                   to a photo.
|      |-------------|
|------|      |      |----> Photo
|      |      |      |
----------------------
             `----------> Photo

The layout placing process is divided in three phases.

Phase A: Fill columns with photos.
  Photos are added to columns, one by one, until there are no more photos.
  Each new photo is put in the smallest column, so as to have balanced
  columns. If two columns have approximately the same height, a photo can be
  "extended" to fit two columns. In this case, the "Cell" object is put in
  the first column, and the second column takes a "CellExtent" object to
  reserve the taken space.

Phase B: Set all columns to same height.
  A global common height is computed for all columns, and every of them is
  stressed or extended to this common length. This can result in a decrease
  or increase in columns' width.

Phase C: Adapt columns' width.
  Since cells in a column may have different widths, each column width is set
  to the smallest width amongst its images.

"""


class Photo:
    def __init__(self, filename, w, h, orientation=0):
        self.filename = filename
        self.w = w
        self.h = h
        self.orientation = orientation
        self.offset_w = 0.5
        self.offset_h = 0.5

    @property
    def ratio(self):
        return float(self.h) / float(self.w)

    def move(self, x, y):
        self.offset_w = self.calculate_new_offset(self.offset_w, x)
        self.offset_h = self.calculate_new_offset(self.offset_h, y)

    @staticmethod
    def calculate_new_offset(offset, value):
        new_offset = offset + value
        if new_offset < 0:
            new_offset = 0
        elif new_offset > 1:
            new_offset = 1
        return new_offset


class Cell:
    """Represents a cell in a column

    Properties:
    <- x -><- w ->
    ---------------------- ^
    |      |             | |y
    |------|             | |
    |      |-------------| v
    |------| Cell |      | ^
    |      |      |      | |h
    ---------------------- v

    """
    def __init__(self, parents, photo):
        self.parents = parents
        self.photo = photo
        self.extent = None
        self.h = self.w * self.wanted_ratio

    def __repr__(self):
        """Representation of the cell in ASCII art"""
        end = "]"
        if self.extent is not None:
            end = "--"
        return "[%d %d%s" % (self.w, self.h, end)

    @property
    def x(self):
        return self.parents[0].x

    @property
    def y(self):
        """Returns the cell's y coordinate

        It assumes that the cell is in a single column, so it is the previous
        cell's y + h.

        """
        prev = None
        for c in self.parents[0].cells:
            if self is c:
                if prev:
                    return prev.y + prev.h
                return 0
            prev = c

    @property
    def w(self):
        return sum(c.w for c in self.parents)

    @property
    def ratio(self):
        return self.h / self.w

    @property
    def wanted_ratio(self):
        return self.photo.ratio

    def scale(self, alpha):
        self.h *= alpha

    def is_extended(self):
        return hasattr(self, 'extent') and self.extent is not None

    def is_extension(self):
        return isinstance(self, CellExtent)

    def content_coords(self):
        """Returns the coordinates of the contained image

        These are computed in order not to loose space, so the content area
        will always be greater than the cell itself. It is the space taken by
        the contained image if it wasn't cropped.

        """
        # If the contained image is too thick to fit
        if self.wanted_ratio < self.ratio:
            h = self.h
            w = self.h / self.wanted_ratio
            y = self.y
            x = self.x - (w - self.w) / 2.0
        # If the contained image is too tall to fit
        elif self.wanted_ratio > self.ratio:
            w = self.w
            h = self.w * self.wanted_ratio
            x = self.x
            y = self.y - (h - self.h) / 2.0
        else:
            w = self.w
            h = self.h
            x = self.x
            y = self.y
        return x, y, w, h

    def top_neighbor(self):
        """Returns the cell above this one"""
        prev = None
        for c in self.parents[0].cells:
            if self is c:
                return prev
            prev = c

    def bottom_neighbor(self):
        """Returns the cell below this one"""
        prev = None
        for c in reversed(self.parents[0].cells):
            if self is c:
                return prev
            prev = c


class CellExtent(Cell):
    def __init__(self, cell):
        self.origin = cell
        self.origin.extent = self

    def __repr__(self):
        """Representation of the cell in ASCII art"""
        return "------]"

    @property
    def parents(self):
        return (self.origin.parents[1],)

    @property
    def photo(self):
        return self.origin.photo

    @property
    def y(self):
        return self.origin.y

    @property
    def h(self):
        return self.origin.h

    def scale(self, alpha):
        pass


class Column:
    """Represents a column in a page

    Properties:
    <----- x ----><-- w ->
    ---------------------- ^
    |      |      |      | |
    |      |      |      |
    |      |      |Column| h
    |      |      |      |
    -------|      |      | |
           |      |------- v
           --------

    """
    def __init__(self, parent, w):
        self.parent = parent
        self.cells = []
        self.w = w

    def __repr__(self):
        """Representation of the column in ASCII art"""
        return "\n".join(c.__repr__() for c in self.cells)

    @property
    def h(self):
        """Returns the column's total height

        This is not simply the sum of its cells heights, because there can be
        empty spaces between cells.

        """
        if not self.cells:
            return 0
        return self.cells[-1].y + self.cells[-1].h

    @property
    def x(self):
        x = 0
        for c in self.parent.cols:
            if self is c:
                break
            x += c.w
        return x

    def scale(self, alpha):
        self.w *= alpha
        for c in self.cells:
            c.scale(alpha)

    def left_neighbor(self):
        """Returns the column on the left of this one"""
        prev = None
        for c in self.parent.cols:
            if self is c:
                return prev
            prev = c

    def right_neighbor(self):
        """Returns the column on the right of this one"""
        prev = None
        for c in reversed(self.parent.cols):
            if self is c:
                return prev
            prev = c

    def adjust_height(self, target_h):
        """Set the column's height to a given value by resizing cells"""
        # First, make groups of "movable" cells. Since cell extents are not
        # movable, these groups only contain pure cell objects. We only resize
        # those groups.
        class Group:
            def __init__(self, y):
                self.y = y
                self.h = 0
                self.cells = []

        groups = []
        groups.append(Group(0))
        for c in self.cells:
            # While a cell extent is not reached, keep add cells to the group
            if not c.is_extension():
                groups[-1].cells.append(c)
            else:
                # Close current group and create a new one
                groups[-1].h = c.y - groups[-1].y
                groups.append(Group(c.y + c.h))
        groups[-1].h = target_h - groups[-1].y

        # Adjust height for each group independently
        for group in groups:
            if not group.cells:
                continue
            alpha = group.h / sum(c.h for c in group.cells)
            for c in group.cells:
                c.h = c.h * alpha


class Page:
    """Represents a whole page

    Properties:
    <-------- w -------->
    ---------------------- ^
    |                    | |
    |                    |
    |        Page        | h
    |                    |
    |                    | |
    ---------------------- v

    """
    def __init__(self, w, target_ratio, no_cols):
        self.target_ratio = target_ratio
        col_w = float(w)/no_cols
        self.cols = []
        for i in range(no_cols):
            self.cols.append(Column(self, col_w))

    def __repr__(self):
        """Representation of the page in ASCII art

        Returns something like:
        [62 52]    [125 134-- ------]    [62 87]
        [62 47]    [62 66]    [125 132-- [62 45]
        [62 46]    ------]    [62 49]    ------]
        [62 78]    ------]    [62 49]    [62 45]
        [125 102-- ------]    [62 49]    [62 65]
        [125 135--            [62 85]    [62 53]
        [125 91--             [125 89--  [62 64]
                                 ------]
        """
        lines = []
        n = 0
        end = False
        while not end:
            lines.append("")
            end = True
            for col in self.cols:
                cells = col.__repr__().split("\n")
                w = max(len(cell) for cell in cells)
                if col != self.cols[-1]:
                    w += 1
                cell = w * " "
                if n < len(cells):
                    cell = cells[n] + (w - len(cells[n])) * " "
                    if n < len(cells) - 1:
                        end = False
                lines[-1] += cell
            n += 1
        return "\n".join(lines)

    @property
    def no_cols(self):
        return len(self.cols)

    @property
    def w(self):
        return sum(c.w for c in self.cols)

    @property
    def h(self):
        return max(c.h for c in self.cols)

    @property
    def ratio(self):
        return self.h / self.w

    def scale(self, alpha):
        for c in self.cols:
            c.scale(alpha)

    def scale_to_fit(self, max_w, max_h=None):
        if max_h is None or self.w * max_h > self.h * max_w:
            self.scale(max_w / self.w)
        else:
            self.scale(max_h / self.h)

    def next_free_col(self):
        """Returns the column with lowest height"""
        minimum = min(c.h for c in self.cols)
        candidates = []
        for c in self.cols:
            if c.h == minimum:
                candidates.append(c)
        return random.choice(candidates)

    def add_cell_single_col(self, col, photo):
        col.cells.append(Cell((col,), photo))

    def add_cell_multi_col(self, col1, col2, photo):
        cell = Cell((col1, col2), photo)
        extent = CellExtent(cell)
        col1.cells.append(cell)
        col2.cells.append(extent)

    def add_cell(self, photo):
        """Add a new cell in the best computed place

        If possible, and if it's worth, make a "multiple-column" cell.

        """
        col = self.next_free_col()
        left = col.left_neighbor()
        right = col.right_neighbor()
        if 2 * random.random() > photo.ratio:
            if left and abs(col.h - left.h) < 0.5 * col.w:
                return self.add_cell_multi_col(left, col, photo)
            elif right and abs(col.h - right.h) < 0.5 * col.w:
                return self.add_cell_multi_col(col, right, photo)

        self.add_cell_single_col(col, photo)

    def remove_empty_cols(self):
        i = 0
        while i < len(self.cols):
            if len(self.cols[i].cells) == 0:
                self.cols.pop(i)
            else:
                i += 1

    def remove_bottom_holes(self):
        """Remove holes created by extended cells

        Example (case A):
        The bottom-right cell should be extended to fill the hole.
        ----------------------             ----------------------
        |      |      |      |             |      |      |      |
        |      |-------------|             |      |-------------|
        |------|             |             |------|             |
        |      |--------------             |      |--------------
        |      |      |  ^                 |      |  ^   |      |
        --------------- hole               -------- hole --------

        Example (case B):
        The bottom cell should be moved under the other extended cell.
        ----------------------             ----------------------
        |      |      |      |             |      |      |      |
        |------|-------------|             |-------------|------|
        |      |             |             |             |      |
        |---------------------             ---------------------|
        |             |   <-- hole      hole ->   |             |
        ---------------                           ---------------

        """
        for col in self.cols:
            cell = col.cells[-1]
            if cell == col.cells[0]:
                continue

            # Case A
            # If cell is not extended, is below an extended cell and has no
            # neighbour under the latter, it should be extended.
            if not cell.is_extended() and not cell.is_extension():
                # Case A1
                if cell.top_neighbor().is_extended() \
                        and cell.top_neighbor().extent \
                        .bottom_neighbor() is None:
                    # Extend cell to right
                    extent = CellExtent(cell)
                    col.right_neighbor().cells.append(extent)
                    cell.parents = (col, col.right_neighbor())
                # Case A2
                elif cell.top_neighbor().is_extension() \
                        and cell.top_neighbor().origin \
                        .bottom_neighbor() is None:
                    # Extend cell to left
                    col.cells.remove(cell)
                    col.left_neighbor().cells.append(cell)
                    extent = CellExtent(cell)
                    col.cells.append(extent)
                    cell.parents = (col.left_neighbor(), col)
            # Case B
            # If cell is extended and one of the cells above is extended too,
            # the bottom cell should be placed right below the top one.
            elif cell.is_extended() and cell.extent.bottom_neighbor() is None:
                # Case B1
                if cell.extent.top_neighbor().is_extended() \
                        and cell.extent.top_neighbor().extent \
                        .bottom_neighbor() is None:
                    # Move cell to right
                    col.cells.remove(cell)
                    col.right_neighbor().cells.remove(cell.extent)
                    col.right_neighbor().cells.append(cell)
                    col.right_neighbor().right_neighbor().cells \
                        .append(cell.extent)
                    cell.parents = (col.right_neighbor(),
                                    col.right_neighbor().right_neighbor())
                # Case B2
                elif cell.top_neighbor().is_extension() \
                        and cell.top_neighbor().origin \
                        .bottom_neighbor() is None:
                    # Move cell to left
                    col.cells.remove(cell)
                    col.right_neighbor().cells.remove(cell.extent)
                    col.left_neighbor().cells.append(cell)
                    col.cells.append(cell.extent)
                    cell.parents = (col.left_neighbor(), col)

    def adjust_cols_heights(self):
        """Set all columns' heights to same value by shrinking them"""
        target_h = self.w * self.target_ratio
        for c in self.cols:
            c.adjust_height(target_h)

    def adjust(self):
        self.remove_empty_cols()
        self.remove_bottom_holes()
        self.adjust_cols_heights()

    def get_cell_at_position(self, x, y):
        for col in self.cols:
            if x >= col.x and x < col.x + col.w:
                for cell in col.cells:
                    if y >= cell.y and y < cell.y + cell.h:
                        if cell.is_extension():
                            return cell.origin
                        return cell
        return None

    def swap_photos(self, cell1, cell2):
        cell1.photo, cell2.photo = cell2.photo, cell1.photo
