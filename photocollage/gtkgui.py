# Copyright (C) 2013 Adrien Vergé
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

import copy
import gettext
from io import BytesIO
import math
import os.path
import random
import urllib

import cairo
import gi

from data.pickle.utils import get_pickle_path, get_jpg_path, get_pdf_path
from data.rankers import RankerFactory
from data.sqllite.reader import get_tree_model
from photocollage import APP_NAME, artwork, collage, render
from photocollage.collage import Photo
from photocollage.render import PIL_SUPPORTED_EXTS as EXTS
from photocollage.dialogs.SettingsDialog import SettingsDialog

from data.readers.default import corpus_processor
from yearbook.Yearbook import Yearbook
from yearbook.Yearbook import Page

from images.utils import get_orientation_fixed_pixbuf

gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')

from gi.repository import Gtk, Gdk, GObject, GdkPixbuf  # noqa: E402, I100

gettext.textdomain(APP_NAME)
_ = gettext.gettext
_n = gettext.ngettext


# xgettext --keyword=_n:1,2 -o po/photocollage.pot $(find . -name '*.py')
# cp po/photocollage.pot po/fr.po
# msgfmt -o po/fr.mo po/fr.po


def pil_image_to_cairo_surface(src):
    # TODO: cairo.ImageSurface.create_for_data() is not yet available in
    # Python 3, so we use PNG as an intermediate.
    buf = BytesIO()
    src.save(buf, "png")
    buf.seek(0)
    surface = cairo.ImageSurface.create_from_png(buf)
    buf.close()
    return surface


def get_all_save_image_exts():
    all_types = dict(list(EXTS.RW.items()) + list(EXTS.WO.items()))
    all_images = []
    for file_type in all_types:
        for ext in all_types[file_type]:
            all_images.append(ext)

    return all_images


def set_open_image_filters(dialog):
    """Set our own filter because Gtk.FileFilter.add_pixbuf_formats() contains
    formats not supported by PIL.

    """
    # Do not show the filter to the user, just limit selectable files
    img_filter = Gtk.FileFilter()
    img_filter.set_name(_("All supported image formats"))

    all_types = dict(list(EXTS.RW.items()) + list(EXTS.RO.items()))
    for type in all_types:
        for ext in all_types[type]:
            img_filter.add_pattern("*." + ext)
            img_filter.add_pattern("*." + ext.upper())

    dialog.add_filter(img_filter)
    dialog.set_filter(img_filter)


def set_save_image_filters(dialog):
    """Set our own filter because Gtk.FileFilter.add_pixbuf_formats() contains
    formats not supported by PIL.

    """
    all_types = dict(list(EXTS.RW.items()) + list(EXTS.WO.items()))
    filters = [Gtk.FileFilter()]

    flt = filters[-1]
    flt.set_name(_("All supported image formats"))
    for ext in get_all_save_image_exts():
        flt.add_pattern("*." + ext)
        flt.add_pattern("*." + ext.upper())
    dialog.add_filter(flt)
    dialog.set_filter(flt)

    for file_type in all_types:
        filters.append(Gtk.FileFilter())
        flt = filters[-1]
        name = _("%s image") % file_type
        name += " (." + ", .".join(all_types[file_type]) + ")"
        flt.set_name(name)
        for ext in all_types[file_type]:
            flt.add_pattern("*." + ext)
            flt.add_pattern("*." + ext.upper())
        dialog.add_filter(flt)


def gtk_run_in_main_thread(fn):
    def my_fn(*args, **kwargs):
        GObject.idle_add(fn, *args, **kwargs)

    return my_fn


class ImagePreviewArea(Gtk.DrawingArea):
    """Area to display the poster preview and react to user actions"""
    INSENSITIVE, FLYING, SWAPPING_OR_MOVING = range(3)

    def __init__(self, parent, name):
        super().__init__()
        self.parent = parent
        self.name = name

        parse, color = Gdk.Color.parse("#888888")
        self.modify_bg(Gtk.StateType.NORMAL, color)

        # http://www.pygtk.org/pygtk2tutorial/sec-EventHandling.html
        # https://developer.gnome.org/gdk3/stable/gdk3-Events.html#GdkEventMask
        self.connect("draw", self.draw)
        self.connect("motion-notify-event", self.motion_notify_event)
        self.connect("leave-notify-event", self.motion_notify_event)
        self.connect("button-press-event", self.button_press_event)
        self.connect("button-release-event", self.button_release_event)
        self.set_events(Gdk.EventMask.EXPOSURE_MASK |
                        Gdk.EventMask.LEAVE_NOTIFY_MASK |
                        Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK)

        self.image = None
        self.collage = None
        self.mode = self.INSENSITIVE

        class SwapEnd:
            def __init__(self, cell=None, x=0, y=0):
                self.cell = cell
                self.x = x
                self.y = y

        self.x, self.y = 0, 0
        self.swap_origin = SwapEnd()
        self.swap_dest = SwapEnd()

    def set_collage(self, _image, _collage):
        self.image = pil_image_to_cairo_surface(_image)
        # The Collage object must be deeply copied.
        # Otherwise, SWAPPING_OR_MOVING photos in a new page would also affect
        # the original page (in history).
        # The deep copy is done here (not in button_release_event) because
        # references to cells are gathered in other functions, so that making
        # the copy at the end would invalidate these references.
        self.collage = copy.deepcopy(_collage)
        self.mode = self.FLYING
        self.queue_draw()

    def get_image_offset(self):
        return (round((self.get_allocation().width -
                       self.image.get_width()) / 2.0),
                round((self.get_allocation().height -
                       self.image.get_height()) / 2.0))

    def get_pos_in_image(self, x, y):
        if self.image is not None:
            x0, y0 = self.get_image_offset()
            return int(round(x - x0)), int(round(y - y0))
        return int(round(x)), int(round(y))

    def paint_image_border(self, context, cell, dash=None):
        x0, y0 = self.get_image_offset()

        context.set_source_rgb(1.0, 1.0, 0.0)
        context.set_line_width(2)
        if dash is not None:
            context.set_dash(dash)
        context.rectangle(x0 + cell.x + 1, y0 + cell.y + 1,
                          cell.w - 2, cell.h - 2)
        context.stroke()

    def paint_image_delete_button(self, context, cell):
        x0, y0 = self.get_image_offset()

        x = x0 + cell.x + cell.w - 12
        y = y0 + cell.y + 12

        context.arc(x, y, 8, 0, 6.2832)
        context.set_source_rgb(0.8, 0.0, 0.0)
        context.fill()
        context.arc(x, y, 8, 0, 6.2832)
        context.set_source_rgb(0.0, 0.0, 0.0)
        context.set_line_width(1)
        context.move_to(x - 4, y - 4)
        context.line_to(x + 4, y + 4)
        context.move_to(x - 4, y + 4)
        context.line_to(x + 4, y - 4)
        context.stroke()

    def paint_image_pin_button(self, context, cell, pinned: bool):
        x0, y0 = self.get_image_offset()

        x = x0 + cell.x + cell.w - 30
        y = y0 + cell.y + 12

        context.arc(x, y, 8, 0, 6.2832)
        if pinned:
            context.set_source_rgb(0.0, 0.0, 0.8)
        else:
            context.set_source_rgb(0.0, 0.8, 0.0)
        context.fill()
        context.arc(x, y, 8, 0, 6.2832)
        context.set_source_rgb(0.0, 0.0, 0.0)
        context.set_line_width(1)
        context.move_to(x - 4, y - 4)
        context.line_to(x + 4, y + 4)
        context.move_to(x - 4, y + 4)
        context.line_to(x + 4, y - 4)
        context.stroke()

    def draw(self, widget, context):
        if self.image is not None:
            x0, y0 = self.get_image_offset()
            context.set_source_surface(self.image, x0, y0)
            context.paint()

            if self.mode == self.FLYING:
                cell = self.collage.page.get_cell_at_position(self.x, self.y)
                if cell:
                    self.paint_image_border(context, cell)

                    if self.parent.left_index is not None:
                        if widget.name == "LeftPage":
                            _current_page = self.parent.current_yearbook.pages[self.parent.left_index]
                        else:
                            _current_page = self.parent.current_yearbook.pages[self.parent.right_index]

                        if cell.photo.filename not in _current_page.get_parent_pinned_photos():
                            # Allow deleting only when the image is not pinned by any parent.
                            self.paint_image_delete_button(context, cell)

                    if self.parent.current_yearbook.child is None:
                        # only then we bother with pinning icons
                        # If image is pinned at same level
                        if cell.photo.filename in _current_page.pinned_photos:
                            self.paint_image_pin_button(context, cell, pinned=True)
                        elif cell.photo.filename in _current_page.get_parent_pinned_photos():
                            # Do not show any pinning options
                            pass
                        else:
                            self.paint_image_pin_button(context, cell, pinned=False)


            elif self.mode == self.SWAPPING_OR_MOVING:
                self.paint_image_border(context, self.swap_origin.cell, (3, 3))
                cell = self.collage.page.get_cell_at_position(self.x, self.y)
                if cell and cell != self.swap_origin.cell:
                    self.paint_image_border(context, cell, (3, 3))
        else:
            # Display the drag & drop image
            dnd_image = artwork.load_cairo_surface(artwork.ICON_DRAG_AND_DROP)
            context.set_source_surface(
                dnd_image,
                round((self.get_allocation().width -
                       dnd_image.get_width()) / 2.0),
                round((self.get_allocation().height -
                       dnd_image.get_height()) / 2.0))
            context.paint()

        return False

    def motion_notify_event(self, widget, event):
        self.x, self.y = self.get_pos_in_image(event.x, event.y)
        widget.queue_draw()

    def button_press_event(self, widget, event):
        if self.parent.current_yearbook is None:
            return

        if widget.name == "LeftPage":
            current_page = self.parent.current_yearbook.pages[self.parent.left_index]
        else:
            current_page = self.parent.current_yearbook.pages[self.parent.right_index]

        if self.mode == self.FLYING:
            x, y = self.get_pos_in_image(event.x, event.y)
            cell = self.collage.page.get_cell_at_position(x, y)
            if not cell:
                return
            # Has the user clicked the delete button?
            dist_delete = (cell.x + cell.w - 12 - x) ** 2 + (cell.y + 12 - y) ** 2
            dist_pinned = (cell.x + cell.w - 30 - x) ** 2 + (cell.y + 12 - y) ** 2
            if dist_delete <= 8 * 8:
                self.collage.photolist.remove(cell.photo)
                if cell.photo.filename in current_page.pinned_photos:
                    current_page.remove_pinned_photo(cell.photo)
                current_page.remove_from_photolist(cell.photo)

                if self.collage.photolist:
                    self.collage.make_page(self.parent.opts)
                    self.parent.render_from_new_collage(current_page, self.collage)
                else:
                    self.image = None
                    self.mode = self.INSENSITIVE
                    current_page.history_index = len(current_page.history)
                    self.parent.update_tool_buttons()

                # Let's update the flow images to have this image show up in the bottom
                self.parent.update_flow_box_with_images(current_page)

            elif dist_pinned <= 8 * 8:
                if cell.photo.filename in current_page.pinned_photos:
                    # Then we need to unpin
                    current_page.remove_pinned_photo(cell.photo)
                else:
                    current_page.pin_photo(cell.photo)

            # Otherwise, the user wants to swap this image with another
            else:
                self.swap_origin.x, self.swap_origin.y = x, y
                self.swap_origin.cell = cell
                self.mode = self.SWAPPING_OR_MOVING
        widget.queue_draw()

    def button_release_event(self, widget, event):
        if self.parent.current_yearbook is None:
            return

        if widget.name == "LeftPage":
            current_page = self.parent.current_yearbook.pages[self.parent.left_index]
        else:
            current_page = self.parent.current_yearbook.pages[self.parent.right_index]

        if self.mode == self.SWAPPING_OR_MOVING:
            self.swap_dest.x, self.swap_dest.y = \
                self.get_pos_in_image(event.x, event.y)
            self.swap_dest.cell = self.collage.page.get_cell_at_position(
                self.swap_dest.x, self.swap_dest.y)
            if self.swap_dest.cell \
                    and self.swap_origin.cell != self.swap_dest.cell:
                # different cell: SWAPPING
                self.collage.page.swap_photos(self.swap_origin.cell,
                                              self.swap_dest.cell)
                self.parent.render_from_new_collage(current_page, self.collage)
            elif self.swap_dest.cell:
                # same cell: MOVING
                move_x = (self.swap_origin.x - self.x) / self.swap_dest.cell.w
                move_y = (self.swap_origin.y - self.y) / self.swap_dest.cell.h
                self.swap_dest.cell.photo.move(move_x, move_y)
                self.parent.render_from_new_collage(current_page, self.collage)
            self.mode = self.FLYING
        widget.queue_draw()


class UserCollage:
    """Represents a user-defined collage

    A UserCollage contains a list of photos (referenced by filenames) and a
    collage.Page object describing their layout in a final poster.

    """

    def __init__(self, photolist: [Photo]):
        self.photolist: [Photo] = photolist
        self.page: collage.Page = None

    def make_page(self, opts):
        # Define the output image height / width ratio
        ratio = 1.0 * opts.out_h / opts.out_w

        # Compute a good number of columns. It depends on the ratio, the number
        # of images and the average ratio of these images. According to my
        # calculations, the number of column should be inversely proportional
        # to the square root of the output image ratio, and proportional to the
        # square root of the average input images ratio.
        avg_ratio = (sum(1.0 * photo.h / photo.w for photo in self.photolist) /
                     len(self.photolist))
        # Virtual number of images: since ~ 1 image over 3 is in a multi-cell
        # (i.e. takes two columns), it takes the space of 4 images.
        # So it's equivalent to 1/3 * 4 + 2/3 = 2 times the number of images.
        virtual_no_imgs = 2 * len(self.photolist)
        no_cols = int(round(math.sqrt(avg_ratio / ratio * virtual_no_imgs)))

        self.page = collage.Page(1.0, ratio, no_cols)
        random.shuffle(self.photolist)
        for photo in self.photolist:
            self.page.add_cell(photo)
        self.page.adjust()

    def duplicate(self):
        return UserCollage(copy.copy(self.photolist))


class MainWindow(Gtk.Window):
    TARGET_TYPE_TEXT = 1
    TARGET_TYPE_URI = 2

    @property
    def right_index(self):
        return self.left_index + 1

    def __init__(self):
        super().__init__(title=_("Yearbook Creator"))
        import getpass

        self.corpus_base_dir = os.path.join('/Users', getpass.getuser(), 'GoogleDrive')
        self.output_base_dir = os.path.join(self.corpus_base_dir, 'YearbookCreatorOut')
        self.yearbook_parameters = {'max_count': 12,
                                    'db_file_path': os.path.join(self.output_base_dir, 'RY.db'),
                                    'output_dir': os.path.join(self.output_base_dir, getpass.getuser()),
                                    'corpus_base_dir': self.corpus_base_dir}

        self.corpus_cache = {}
        self.tree_model_cache = {}

        self.current_yearbook: Yearbook = None
        self.corpus = None

        from data.sqllite.reader import get_tree_model, get_school_list
        self.school_combo = Gtk.ComboBoxText.new()
        school_list = get_school_list(self.yearbook_parameters['db_file_path'])
        for school in school_list:
            self.school_combo.append_text(school)

        self.school_combo.set_active(0)
        self.school_name = self.school_combo.get_active_text()
        self.set_current_corpus()
        self.left_index = 0

        self.img_preview_left = ImagePreviewArea(self, "LeftPage")
        self.img_preview_right = ImagePreviewArea(self, "RightPage")
        self.images_flow_box = Gtk.FlowBox()
        self.portraits_flow_box = Gtk.FlowBox()
        self.btn_settings = Gtk.Button()
        self.btn_regen_left = Gtk.Button(label=_("RegenerateLeft"))
        self.btn_regen_right = Gtk.Button(label=_("RegenerateRight"))
        self.btn_redo = Gtk.Button()
        self.lbl_history_index = Gtk.Label(" ")
        self.btn_undo = Gtk.Button()
        self.btn_prev_page = Gtk.Button(label=_("Prev page..."))
        self.lbl_right_page = Gtk.Label(" ")
        self.lbl_left_page = Gtk.Label(" ")
        self.btn_next_page = Gtk.Button(label=_("Next page..."))
        self.btn_publish_book = Gtk.Button(label=_("Publish"))

        # on initialization
        self.treeModel: Gtk.TreeStore = get_tree_model(self.yearbook_parameters, self.school_combo.get_active_text())
        self.tree_model_cache[self.school_combo.get_active_text()] = self.treeModel
        self.treeView = Gtk.TreeView(self.treeModel)
        tv_column = Gtk.TreeViewColumn('Roster')
        self.treeView.append_column(tv_column)
        self.treeView.expand_all()

        self.school_combo.connect("changed", self.on_school_combo_changed)

        cell = Gtk.CellRendererText()
        tv_column.pack_start(cell, True)
        tv_column.set_cell_data_func(cell, self.get_yearbook_string)
        tv_column.add_attribute(cell, 'text', 0)

        class Options:
            def __init__(self):
                self.border_w = 0.01
                self.border_c = "white"
                self.out_w = 2550
                self.out_h = 3300

        self.opts = Options()
        self.make_window()

    def get_yearbook_string(self, column, cell, model, iter, data):
        cell.set_property('text', model.get_value(iter, 0).__repr__())

    def make_window(self):
        self.set_border_width(10)

        box_window = Gtk.Box(spacing=10, orientation=Gtk.Orientation.VERTICAL)
        self.add(box_window)

        # -----------------------
        #  Input and output pan
        # -----------------------

        box = Gtk.Box(spacing=6, orientation=Gtk.Orientation.HORIZONTAL)
        box_window.pack_start(box, False, False, 0)

        box.pack_start(self.school_combo, False, False, 0)

        # -----------------------
        #  Tools pan
        # -----------------------
        box.pack_start(Gtk.SeparatorToolItem(), True, True, 0)
        self.btn_regen_left.connect("clicked",
                                    self.regenerate_layout)
        box.pack_start(self.btn_regen_left, False, False, 0)
        self.btn_regen_right.connect("clicked",
                            self.regenerate_layout)
        box.pack_start(self.btn_regen_right, False, False, 0)

        box.pack_start(Gtk.SeparatorToolItem(), True, True, 0)

        box.pack_start(self.btn_prev_page, False, False, 0)
        self.btn_prev_page.set_sensitive(False)
        self.btn_prev_page.connect("clicked", self.select_prev_page)

        box.pack_start(self.lbl_left_page, False, False, 0)
        box.pack_start(self.lbl_right_page, False, False, 0)
        box.pack_start(self.btn_next_page, True, True, 0)
        self.btn_next_page.connect("clicked", self.select_next_page)

        box.pack_start(self.btn_publish_book, True, True, 0)
        self.btn_publish_book.connect("clicked", self.publish_and_pickle)
        box.pack_start(Gtk.SeparatorToolItem(), True, True, 0)

        self.btn_settings.set_always_show_image(True)
        self.btn_settings.connect("clicked", self.set_settings)
        box.pack_end(self.btn_settings, False, False, 0)

        # --------------------------------------
        #  Tree View And Two Image Viewing Pans
        # --------------------------------------
        box = Gtk.Box(spacing=20)
        _scrolledWindow = Gtk.ScrolledWindow()
        _scrolledWindow.add(self.treeView)
        box.pack_start(_scrolledWindow, True, True, 0)
        self.treeView.get_selection().connect("changed", self.on_tree_selection_changed)

        targets = Gtk.TargetList.new([])
        targets.add_text_targets(MainWindow.TARGET_TYPE_TEXT)
        targets.add_uri_targets(MainWindow.TARGET_TYPE_URI)

        self.img_preview_left.connect("drag-data-received", self.on_drag)
        self.img_preview_left.drag_dest_set(Gtk.DestDefaults.ALL, [],
                                            Gdk.DragAction.COPY)
        self.img_preview_left.drag_dest_set_target_list(targets)

        box.pack_start(self.img_preview_left, True, True, 0)

        self.img_preview_right.connect("drag-data-received", self.on_drag)
        self.img_preview_right.drag_dest_set(Gtk.DestDefaults.ALL, [],
                                        Gdk.DragAction.COPY)
        self.img_preview_right.drag_dest_set_target_list(targets)
        box.pack_end(self.img_preview_right, True, True, 0)
        box.set_size_request(1200, 500)
        box_window.pack_start(box, True, True, 0)

        self.btn_undo.set_sensitive(False)
        self.btn_redo.set_sensitive(False)

        # --------------------------------------------
        #  Child portraits/selfie viewer
        # --------------------------------------------
        box = Gtk.Box(spacing=10)
        _scrolledWindow = Gtk.ScrolledWindow()
        _scrolledWindow.add(self.portraits_flow_box)
        _scrolledWindow.set_size_request(100, 300)
        box.pack_start(_scrolledWindow, True, True, 0)
        box_window.pack_start(box, True, True, 0)

        separator = Gtk.SeparatorToolItem()
        separator.set_size_request(1, 300)
        box.pack_start(separator, True, True, 0)

        # --------------------------------------------
        #  GTK Flow Box to view other candidate images
        # --------------------------------------------
        _scrolledWindow = Gtk.ScrolledWindow()
        _scrolledWindow.set_size_request(600, 300)
        _scrolledWindow.add(self.images_flow_box)
        box.pack_start(_scrolledWindow, True, True, 0)
        box_window.pack_start(box, True, True, 0)

    '''
    When the combo select box changes, we have to do the following
    1) Update the corpus that's selected for processing based on the new school
    2) Update the set of yearbooks, so update the yearbook tree model 
    '''

    def on_school_combo_changed(self, combo):

        self.school_name = self.school_combo.get_active_text()
        self.set_current_corpus()
        if self.school_name in self.tree_model_cache:
            _tree_model = self.tree_model_cache[self.school_name]
            self.treeView.set_model(_tree_model)
        else:
            _tree_model = get_tree_model(self.yearbook_parameters, self.school_combo.get_active_text())
            self.treeView.set_model(_tree_model)
            self.treeView.set_cursor(0)
            _tree_model.foreach(self.render_and_pickle_yearbook)

        self.treeModel = _tree_model  # Not sure if we need to maintain this reference
        self.treeView.expand_all()

    def set_current_corpus(self):
        if self.school_name in self.corpus_cache:
            self.corpus = self.corpus_cache[self.school_name]
        else:
            self.corpus = corpus_processor(self.school_name)
            self.corpus_cache[self.school_name] = self.corpus

    '''
    On a tree selection change, we have to 
    1) Update the yearbook reference
    2) Update the page displayed on that current yearbook
    3) Update the tool bar buttons
    4) Update other UI elements
    '''

    def on_tree_selection_changed(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            self.current_yearbook: Yearbook = model[treeiter][0]
            self.current_yearbook.print_yearbook_info()

        # Update the tool buttons
        self.set_current_corpus()
        self.update_ui_elements()
        self.update_child_portrait_images(self.current_yearbook)

    def update_child_portrait_images(self, yearbook: Yearbook):
        flowbox = self.portraits_flow_box
        flowbox.set_valign(Gtk.Align.START)
        flowbox.set_max_children_per_line(3)
        # Need to remove all previously added images
        [flowbox.remove(child) for child in flowbox.get_children()]

        print("Looking for pictures of %s" % yearbook.child)
        tag_list = ["Portraits", yearbook.grade, yearbook.classroom, yearbook.child]
        child_portraits = self.corpus.get_intersection_images(tag_list)[:3]

        for img in child_portraits:
            pixbuf = get_orientation_fixed_pixbuf(img)
            try:
                image = Gtk.Image.new_from_pixbuf(pixbuf)
                flowbox.add(image)
            except OSError:
                # raise BadPhoto(name)
                print("Skipping a selfie: %s" % img)
                continue

        self.show_all()

    def update_flow_box_with_images(self, page: Page):
        if not page.personalized:
            print("Load image as is, %s, %s" % (page.event_name, page.image))
            candidate_images = [page.image]
        else:
            tags = []
            tags.extend(page.tags.split(","))
            tags.append(page.event_name)

            candidate_images = self.corpus.get_intersection_images(tags)

        flowbox = self.images_flow_box
        flowbox.set_valign(Gtk.Align.START)
        flowbox.set_max_children_per_line(10)
        flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)

        # Need to remove all previously added images
        [flowbox.remove(child) for child in flowbox.get_children()]

        for img in candidate_images:

            # Lets not add the image to the viewer if it's on the page.
            # TODO: This need to account for all previous pages and be smarter than what it currently is
            if page.personalized and img in [photo.filename for photo in page.photo_list]:
                continue

            pixbuf = get_orientation_fixed_pixbuf(img)
            try:
                image = Gtk.Image.new_from_pixbuf(pixbuf)
                img_box = Gtk.EventBox()
                img_box.add(image)
                img_box.connect("button_press_event", self.invoke_add_image, img)
                flowbox.add(img_box)

            except OSError:
                # raise BadPhoto(name)
                print("Skipping a photo: %s" % img)
                continue

        self.show_all()

    def invoke_add_image(self, widget, event, img_name):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            print("double click, %s", img_name)
            self.update_photolist(self.current_yearbook.pages[self.left_index], [img_name])
            self.update_flow_box_with_images(self.current_yearbook.pages[self.left_index])
        elif event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            print("Right clicked")
            self.update_photolist(self.current_yearbook.pages[self.right_index], [img_name])
            self.update_flow_box_with_images(self.current_yearbook.pages[self.right_index])
        else:
            print("Image clicked %s " % event.button)
            print(event.button == 3)

    def update_photolist(self, page, new_images: [str], display: bool = True):
        photolist: [Photo] = []
        try:
            if page.history_index < len(page.history):
                photolist = copy.copy(
                    page.history[page.history_index].photolist)
            photolist.extend(render.build_photolist(new_images))

            if len(photolist) > 0:
                new_collage = UserCollage(photolist)
                new_collage.make_page(self.opts)
                if display:
                    self.render_from_new_collage(page, new_collage)
            else:
                self.update_tool_buttons()
        except render.BadPhoto as e:
            dialog = ErrorDialog(
                self, _("This image could not be opened:\n\"%(imgname)s\".")
                      % {"imgname": e.photoname})
            dialog.run()
            dialog.destroy()

        page.photo_list = photolist

    def select_page_at_index(self, index: int):
        self.left_index = index
        return self.current_yearbook.pages[index]

    def choose_images_for_page(self, page: Page, max_count=12) -> [str]:
        # Let's find the right ranker to delegate to
        ranker = RankerFactory.create_ranker(self.corpus, self.current_yearbook)
        print("Working on: (%s, %s, %s) with tags %s" % (page.image, page.event_name, page.number, page.tags))
        return ranker.get_candidate_images(self.current_yearbook, page, max_count)

    def on_drag(self, widget, drag_context, x, y, data, info, time):
        if info == MainWindow.TARGET_TYPE_TEXT:
            files = data.get_text().splitlines()
        elif info == MainWindow.TARGET_TYPE_URI:
            # Can only handle local URIs
            files = [f for f in data.get_uris() if f.startswith("file://")]

        for i in range(len(files)):
            if files[i].startswith("file://"):
                files[i] = urllib.parse.unquote(files[i][7:])
        self.update_photolist(self.current_yearbook.pages[self.left_index], files)
        self.update_flow_box_with_images(self.current_yearbook.pages[self.left_index])

    def render_and_pickle_yearbook(self, store: Gtk.TreeStore, treepath: Gtk.TreePath, treeiter: Gtk.TreeIter):
        _yearbook = store[treeiter][0]
        self.current_yearbook = _yearbook

        output_dir = self.yearbook_parameters['output_dir']
        pickle_path = os.path.join(
            get_pickle_path(output_dir, self.current_yearbook.school, self.current_yearbook.grade,
                            self.current_yearbook.classroom, self.current_yearbook.child), "file.pickle")
        print("operating on current yearbook : %s" % pickle_path)
        if os.path.exists(pickle_path):
            print("will be loaded from pickle file...")
            return

        print("*********First creation of this yearbook********")
        for page in self.current_yearbook.pages:
            self.render_preview(page, self.img_preview_left)

        self.publish_and_pickle(None)
        print("********Finished rendering pages for the yearbook********")

    def render_left_page(self, page):
        self.render_preview(page, self.img_preview_left)

    def render_right_page(self, page):
        self.render_preview(page, self.img_preview_right)

    def render_preview(self, yearbook_page: Page, img_preview_area: ImagePreviewArea):
        print("---Displaying %s " % yearbook_page.event_name)

        if len(yearbook_page.history) == 0:
            page_images = self.choose_images_for_page(yearbook_page)
            if page_images is None or len(page_images) == 0:
                # We need to find the parent yearbook and get that page here

                model, treeiter = self.treeView.get_selection().get_selected()
                parent_book: Yearbook = model.iter_parent(treeiter)
                print("Parent book -> %s" % parent_book.__repr__())
                parent_page: Page = parent_book.pages[yearbook_page.number-1]
                page_images = parent_page.photos_on_page

            first_photo_list = render.build_photolist(page_images)
            page_collage = UserCollage(first_photo_list)
            page_collage.make_page(self.opts)
            yearbook_page.photo_list = first_photo_list
            yearbook_page.history.append(page_collage)
            yearbook_page.history_index = len(yearbook_page.history) - 1
        elif yearbook_page.has_parent_pins_changed():
            new_images = yearbook_page.get_parent_pins_not_on_page()
            self.update_photolist(new_images)
        else:
            page_collage: UserCollage = yearbook_page.history[yearbook_page.history_index]

        # If the desired ratio changed in the meantime (e.g. from landscape to
        # portrait), it needs to be re-updated
        page_collage.page.target_ratio = 1.0 * self.opts.out_h / self.opts.out_w
        page_collage.page.adjust_cols_heights()

        # TODO:: Might be worth pulling these out and passing it in from the calling agent
        w = img_preview_area.get_allocation().width
        h = img_preview_area.get_allocation().height

        page_collage.page.scale_to_fit(w, h)

        # Display a "please wait" dialog and do the job.
        comp_dialog = ComputingDialog(self)

        def on_update(img, fraction_complete):
            img_preview_area.set_collage(img, page_collage)
            comp_dialog.update(fraction_complete)

        def on_complete(img, out_file):
            img_preview_area.set_collage(img, page_collage)
            comp_dialog.destroy()

        def on_fail(exception):
            dialog = ErrorDialog(self, "{}:\n\n{}".format(
                _("An error occurred while rendering image:"), exception))
            comp_dialog.destroy()
            dialog.run()
            dialog.destroy()

        out_file = os.path.join(get_jpg_path(self.yearbook_parameters['output_dir'],
                                             self.current_yearbook.school, self.current_yearbook.grade,
                                             self.current_yearbook.classroom, self.current_yearbook.child),
                                str(yearbook_page.number) + ".jpg")

        t = render.RenderingTask(
            yearbook_page,
            page_collage.page,
            output_file=out_file,
            border_width=self.opts.border_w * max(page_collage.page.w,
                                                  page_collage.page.h),
            border_color=self.opts.border_c,
            on_update=gtk_run_in_main_thread(on_update),
            on_complete=gtk_run_in_main_thread(on_complete),
            on_fail=gtk_run_in_main_thread(on_fail))
        t.start()

        response = comp_dialog.run()
        if response == Gtk.ResponseType.CANCEL:
            t.abort()
            comp_dialog.destroy()

    def render_from_new_collage(self, page: Page, _collage):
        page.history.append(_collage)
        page.history_index = len(page.history) - 1
        self.update_tool_buttons()
        if page.number % 2 == 0:
            self.render_preview(page, self.img_preview_right)
        else:
            self.render_preview(page, self.img_preview_left)

    def regenerate_layout(self, button):
        if button.get_label().endswith("Right"):
            page = self.current_yearbook.pages[self.right_index]
        else:
            page = self.current_yearbook.pages[self.left_index]

        new_collage = page.history[page.history_index].duplicate()
        new_collage.make_page(self.opts)
        self.render_from_new_collage(page, new_collage)

    def select_prev_layout(self, button, page):
        page.history_index -= 1
        self.update_tool_buttons()
        if page.number % 2 == 0:
            self.render_preview(page, self.img_preview_right)
        else:
            self.render_preview(page, self.img_preview_left)

    def publish_and_pickle(self, button):
        self.publish_pdf(button)
        self.pickle_book(button)

    def pickle_book(self, button):
        from pathlib import Path
        import pickle
        import os

        output_dir = self.yearbook_parameters['output_dir']
        pickle_path = get_pickle_path(output_dir, self.current_yearbook.school, self.current_yearbook.grade,
                                      self.current_yearbook.classroom, self.current_yearbook.child)
        pickle_filename = os.path.join(pickle_path, "file.pickle")
        path1 = Path(pickle_filename)
        # Create the parent directories if they don't exist
        os.makedirs(path1.parent, exist_ok=True)

        # Important to open the file in binary mode
        with open(pickle_filename, 'wb') as f:
            pickle.dump(self.current_yearbook.pickle_yearbook, f)

        print("Saved pickled yearbook here: ", pickle_filename)

    def publish_pdf(self, button):
        from PIL import Image
        output_dir = self.yearbook_parameters['output_dir']

        pil_images = [
            Image.open(os.path.join(get_jpg_path(output_dir, self.current_yearbook.school, self.current_yearbook.grade,
                                                 self.current_yearbook.classroom, self.current_yearbook.child),
                                    str(page.number) + ".jpg")) for page in self.current_yearbook.pages]

        pdf_path = os.path.join(get_pdf_path(output_dir, self.current_yearbook.school, self.current_yearbook.grade,
                                             self.current_yearbook.classroom, self.current_yearbook.child),
                                "yearbook.pdf")
        pil_images[0].save(pdf_path, save_all=True,
                           append_images=pil_images[1:])
        print("Finished creating PDF version... ", pdf_path)

    def select_next_page(self, button):
        # Increment to the next left page
        self.left_index += 2
        self.update_ui_elements()
        print("NextClick - ")

    def select_prev_page(self, button):
        self.left_index -= 2
        self.update_ui_elements()
        print("PrevClick - ")

    def update_ui_elements(self):
        print("left index %s, right index %s" % (self.left_index, self.right_index))

        if self.left_index < 0:
            self.left_index = 0

        # Reset the prev and next buttons
        self.btn_prev_page.set_sensitive(self.left_index > 0)
        self.btn_next_page.set_sensitive(self.right_index < len(self.current_yearbook.pages)-1)

        left_page = self.current_yearbook.pages[self.left_index]
        right_page = self.current_yearbook.pages[self.right_index]
        self.render_left_page(left_page)
        self.render_right_page(right_page)
        self.update_flow_box_with_images(left_page)
        self.update_label_text()

    def set_settings(self, button):
        dialog = SettingsDialog(self)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            dialog.apply_opts(self.opts)
            dialog.destroy()

            if self.current_yearbook:
                page = self.current_yearbook.pages[self.left_index]
                if page.history:
                    if page.number % 2 == 0:
                        self.render_preview(page, self.img_preview_right)
                    else:
                        self.render_preview(page, self.img_preview_left)
        else:
            dialog.destroy()

    def update_label_text(self):
        if self.left_index < 0:
            # reset the index
            self.left_index = 0

        _left = self.current_yearbook.pages[self.left_index]
        _right = self.current_yearbook.pages[self.right_index]

        self.lbl_left_page.set_label(str(_left.number) + ":" + _left.event_name)
        self.lbl_right_page.set_label(str(_right.number) + ":" + _right.event_name)

    def update_tool_buttons(self):
        if self.current_yearbook is None:
            return

        left_page = self.current_yearbook.pages[self.left_index]
        right_page = self.current_yearbook.pages[self.right_index]

        self.btn_undo.set_sensitive(left_page.history_index > 0)
        self.btn_redo.set_sensitive(left_page.history_index < len(left_page.history) - 1)
        if left_page.history_index < len(left_page.history):
            self.lbl_history_index.set_label(str(left_page.history_index + 1))
        else:
            self.lbl_history_index.set_label(" ")
        self.btn_regen_left.set_sensitive(
            left_page.history_index < len(left_page.history))
        self.btn_regen_right.set_sensitive(
            right_page.history_index < len(right_page.history))


class ComputingDialog(Gtk.Dialog):
    """Simple "please wait" dialog, with a "cancel" button"""

    def __init__(self, parent):
        super().__init__(
            _("Please wait"), parent, 0, (Gtk.STOCK_CANCEL,
                                          Gtk.ResponseType.CANCEL))
        self.set_default_size(300, -1)
        self.set_border_width(10)

        box = self.get_content_area()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.add(vbox)

        label = Gtk.Label(_("Performing image computation..."))
        vbox.pack_start(label, True, True, 0)

        self.progressbar = Gtk.ProgressBar()
        self.progressbar.set_fraction(0)
        vbox.pack_start(self.progressbar, True, True, 0)

        self.show_all()

    def update(self, fraction):
        self.progressbar.set_fraction(fraction)


class ErrorDialog(Gtk.Dialog):
    def __init__(self, parent, message):
        super().__init__(_("Error"), parent, 0,
                         (Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self.set_border_width(10)
        box = self.get_content_area()
        box.add(Gtk.Label(message))
        self.show_all()


class PreviewFileChooserDialog(Gtk.FileChooserDialog):
    PREVIEW_MAX_SIZE = 256

    def __init__(self, **kw):
        super().__init__(**kw)

        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)

        set_open_image_filters(self)

        self._preview = Gtk.Image()
        # Don't let preview size down horizontally for skinny images, cause
        # that looks distracting
        self._preview.set_size_request(
            PreviewFileChooserDialog.PREVIEW_MAX_SIZE, -1)
        self.set_preview_widget(self._preview)
        self.set_use_preview_label(False)
        self.connect("update-preview", self.update_preview_cb)

    def update_preview_cb(self, file_chooser):
        filename = self.get_preview_filename()
        if filename is None or os.path.isdir(filename):
            self.set_preview_widget_active(False)
            return
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                filename,
                PreviewFileChooserDialog.PREVIEW_MAX_SIZE,
                PreviewFileChooserDialog.PREVIEW_MAX_SIZE)
            self._preview.set_from_pixbuf(pixbuf)
        except Exception as e:
            print(e)
            self.set_preview_widget_active(False)
            return
        self.set_preview_widget_active(True)


def main():
    # Enable threading. Without that, threads hang!
    GObject.threads_init()

    win = MainWindow()
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()

    # If arguments are given, treat them as input images
    # if len(sys.argv) > 1:
    #    win.update_photolist(sys.argv[1:])
    win.treeModel.foreach(win.render_and_pickle_yearbook)

    Gtk.main()
    win.treeView.set_cursor(0)
