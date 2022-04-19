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
import shutil
from io import BytesIO
import math
import os.path
import random
import urllib

import PIL
import cairo
import gi
from PIL import Image
from gi.repository.Gtk import TreeStore

from data.model.ModelCreator import get_tree_model
from data.pickle.utils import get_pickle_path, get_jpg_path
from data.rankers import RankerFactory
from images.ImageWindow import ImageWindow
from photocollage import APP_NAME, artwork, collage, render
from photocollage.collage import Photo
from photocollage.render import PIL_SUPPORTED_EXTS as EXTS, TEXT_FONT
from photocollage.dialogs.SettingsDialog import SettingsDialog

from data.readers.default import corpus_processor
from publish.OrderDetails import OrderDetails
from publish.cover.CoverCreatorFactory import get_cover_settings, CoverSettings
from publish.lulu import create_order_payload, get_header

from util.google.drive.util import get_url_from_file_id, upload_with_item_check, get_file_id_from_url, upload_to_folder
from util.utils import get_unique_list_insertion_order
from yearbook.Yearbook import Yearbook, get_tag_list_for_page, pickle_yearbook
from yearbook.Yearbook import Page

from images.utils import get_orientation_fixed_pixbuf

gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')

from gi.repository import Gtk, Gdk, GObject, GdkPixbuf  # noqa: E402, I100
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch, cm

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
                if self.parent.curr_page_index is not None:
                    if widget.name == "LeftPage":
                        _current_page = self.parent.current_yearbook.pages[self.parent.prev_page_index]
                    else:
                        _current_page = self.parent.current_yearbook.pages[self.parent.curr_page_index]
                    if _current_page.is_locked():
                        return

                cell = self.collage.page.get_cell_at_position(self.x, self.y)
                if cell:
                    self.paint_image_border(context, cell)

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
            current_page = self.parent.current_yearbook.pages[self.parent.curr_page_index]
            options = self.parent.left_opts
        else:
            current_page = self.parent.current_yearbook.pages[self.parent.next_page_index]
            options = self.parent.right_opts

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
                    self.collage.make_page(options)
                    self.parent.render_from_new_collage(current_page, self.collage)
                else:
                    self.image = None
                    self.mode = self.INSENSITIVE
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
            current_page = self.parent.current_yearbook.pages[self.parent.curr_page_index]
        else:
            current_page = self.parent.current_yearbook.pages[self.parent.next_page_index]

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

    def __init__(self, photolist: [Photo], collage_page: collage.Page = None):
        self.photolist: [Photo] = photolist
        self.page: collage.Page = collage_page

    def make_page(self, opts, shuffle=False):
        # Define the output image height / width ratio
        ratio = 1.0 * opts.out_h / opts.out_w
        # Compute a good number of columns. It depends on the ratio, the number
        # of images and the average ratio of these images. According to my
        # calculations, the number of column should be inversely proportional
        # to the square root of the output image ratio, and proportional to the
        # square root of the average input images ratio.
        avg_ratio = (sum(1.0 * photo.h / photo.w for photo in self.photolist) /
                     max(len(self.photolist), 1))
        # Virtual number of images: since ~ 1 image over 3 is in a multi-cell
        # (i.e. takes two columns), it takes the space of 4 images.
        # So it's equivalent to 1/3 * 4 + 2/3 = 2 times the number of images.
        virtual_no_imgs = 2 * len(self.photolist)
        no_cols = int(round(math.sqrt(avg_ratio / ratio * virtual_no_imgs)))

        self.page = collage.Page(1.0, ratio, no_cols)

        if shuffle:
            random.shuffle(self.photolist)

        for photo in self.photolist:
            self.page.add_cell(photo)
        self.page.adjust()

    def duplicate(self):
        return UserCollage(copy.copy(self.photolist))

    def duplicate_with_layout(self):
        return UserCollage(copy.copy(self.photolist), copy.deepcopy(self.page))


def get_yearbook_string(column, cell, model, iter, data):
    cell.set_property('text', model.get_value(iter, 0).__repr__())


class Options:
    def __init__(self, left_page: bool = True):
        self.border_w = 0.01
        self.border_c = "black"
        # Dimensions for Book trim size, US Letter, 8.5 x 11 inches at 300 ppi
        # Making the width the same, and height of right page is smaller than left by 100 pixels
        # for adding the label
        if not left_page:
            self.out_h = 3225
        else:
            _, h = TEXT_FONT.getsize("A")
            self.out_h = 3225 - h
        self.out_w = 2475


def create_pdf_from_images(pdf_path, images):
    canvas = Canvas(pdf_path, pagesize=(8.75 * inch, 11.25 * inch))

    for image in images:
        canvas.drawImage(image, 0, 0,
                         width=8.75 * inch, height=11.25 * inch, preserveAspectRatio=True)
        canvas.showPage()
    canvas.save()
    print("Finished saving PDF file %s" % pdf_path)


def update_flag_for_page(page: Page, button, flag: str):
    print("Updating flag=%s page for %s in state %s" % (flag, page.number, button.get_active()))
    page.update_flag(flag, button.get_active())


def pin_all_photos_on_page(page: Page, img_preview: ImagePreviewArea):
    try:
        for column in img_preview.collage.page.cols:
            for cell in column.cells:
                page.pin_photo(cell.photo)
    except:
        pass


def stitch_print_ready_cover(pdf_path: str, yearbook: Yearbook, cover_settings: CoverSettings):
    if cover_settings is None:
        return None

    dirname = os.path.dirname(pdf_path)
    base_name = os.path.basename(pdf_path)
    cover_path_pdf = os.path.join(dirname, base_name + "_cover.pdf")

    canvas_cover = Canvas(cover_path_pdf, pagesize=cover_settings.get_page_size())

    cover_img_dims = cover_settings.get_cover_img_dims()

    # First draw the back cover page
    top_left_back_cover = cover_settings.get_top_left_back_cover()
    canvas_cover.drawImage(yearbook.pages[-1].image, top_left_back_cover[0], top_left_back_cover[1],
                           width=cover_img_dims[0], height=cover_img_dims[1])

    # Then draw the front cover page
    top_left_front_cover = cover_settings.get_top_left_front_cover()

    canvas_cover.drawImage(yearbook.pages[0].image, top_left_front_cover[0],
                           top_left_front_cover[1],
                           width=cover_img_dims[0],
                           height=cover_img_dims[1])

    if yearbook.child is not None:
        # On the front cover we draw the text
        canvas_cover.setFont("Signika", 34)
        # TODO:: Have to do the math to figure out the name
        canvas_cover.drawString(14 * inch, 11.25 * inch, yearbook.child)

    canvas_cover.save()

    print("Finished writing pdf here %s " % cover_path_pdf)
    return cover_path_pdf


class MainWindow(Gtk.Window):
    treeModel: TreeStore
    TARGET_TYPE_TEXT = 1
    TARGET_TYPE_URI = 2

    @property
    def next_page_index(self):
        return self.curr_page_index + 1

    @property
    def prev_page_index(self):
        return self.curr_page_index - 1

    def __init__(self):
        super().__init__(title=_("Yearbook Creator"))
        import getpass

        self.corpus_base_dir = os.path.join('/Users', getpass.getuser(), 'GoogleDrive')
        self.output_base_dir = os.path.join('/Users', getpass.getuser(), 'YearbookCreatorOut')
        self.input_base_dir = os.path.join(self.corpus_base_dir, 'YearbookCreatorInput')
        self.yearbook_parameters = {'max_count': 12,
                                    'db_file_path': os.path.join(self.input_base_dir, 'RY.db'),
                                    'output_dir': os.path.join(self.output_base_dir, getpass.getuser()),
                                    'corpus_base_dir': self.corpus_base_dir}

        self.corpus_cache = {}
        self.tree_model_cache = {}

        self.current_yearbook: Yearbook = None
        self.order_items: [OrderDetails] = []
        self.corpus = None

        from data.sqllite.reader import get_school_list
        self.school_combo = Gtk.ComboBoxText.new()
        school_list = get_school_list(self.yearbook_parameters['db_file_path'])
        for school in school_list:
            self.school_combo.append_text(school)

        self.school_combo.set_active(0)
        self.school_name = self.school_combo.get_active_text()
        self.set_current_corpus()
        self.curr_page_index = 0

        self.img_preview_left = ImagePreviewArea(self, "LeftPage")
        self.img_preview_right = ImagePreviewArea(self, "RightPage")
        self.img_favorites_flow_box = Gtk.FlowBox()
        self.images_flow_box = Gtk.FlowBox()
        self.portraits_flow_box = Gtk.FlowBox()
        self.btn_settings = Gtk.Button()
        self.btn_clear_left = Gtk.Button(label="ClearLeft")
        self.btn_regen_left = Gtk.Button(label=_("RegenerateLeft"))
        self.btn_regen_right = Gtk.Button(label=_("RegenerateRight"))
        self.btn_clear_right = Gtk.Button(label="ClearRight")
        self.btn_redo = Gtk.Button()
        self.lbl_history_index = Gtk.Label(" ")
        self.btn_undo = Gtk.Button()
        self.btn_prev_page = Gtk.Button(label=_("Prev page..."))
        self.lbl_left_page = Gtk.Label(" ")
        self.page_num_text_entry = Gtk.Entry()
        self.page_num_text_entry.set_text("1")
        self.page_num_text_entry.set_max_length(2)
        self.lbl_right_page = Gtk.Label(" ")
        self.btn_next_page = Gtk.Button(label=_("Next page..."))
        self.btn_save_all_books = Gtk.Button(label=_("Save All"))
        self.btn_lock_page_left = Gtk.ToggleButton(label=_("Lock Left"))
        self.btn_lock_page_right = Gtk.ToggleButton(label=_("Lock Right"))
        self.btn_pin_page_left = Gtk.ToggleButton(label="Pin Page Left")
        self.btn_pin_page_right = Gtk.ToggleButton(label="Pin Page Right")

        self.btn_print_all_books = Gtk.Button(label=_("Print All@Lulu"))
        self.btn_submit_order = Gtk.Button(label=_("ORDER"))

        # on initialization
        self.treeModel: Gtk.TreeStore = get_tree_model(self.yearbook_parameters, self.school_combo.get_active_text())
        self.tree_model_cache[self.school_combo.get_active_text()] = self.treeModel
        self.treeView = Gtk.TreeView(self.treeModel)
        tv_column = Gtk.TreeViewColumn('Roster')
        self.treeView.append_column(tv_column)
        # self.treeView.expand_all()

        self.school_combo.connect("changed", self.on_school_combo_changed)

        cell = Gtk.CellRendererText()
        tv_column.pack_start(cell, True)
        tv_column.set_cell_data_func(cell, get_yearbook_string)
        tv_column.add_attribute(cell, 'text', 0)

        self.left_opts = Options(left_page=True)
        self.right_opts = Options(left_page=False)

        self.deleted_images = set()
        self.per_img_window = ImageWindow(self)
        self.make_window()

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
        self.btn_clear_left.connect("clicked",
                                    self.clear_layout)
        box.pack_start(self.btn_clear_left, False, False, 0)

        self.btn_regen_left.connect("clicked",
                                    self.regenerate_layout)
        box.pack_start(self.btn_regen_left, False, False, 0)
        self.btn_regen_right.connect("clicked",
                                     self.regenerate_layout)

        box.pack_start(self.btn_regen_right, False, False, 0)
        box.pack_start(self.btn_clear_right, False, False, 0)
        self.btn_clear_right.connect("clicked",
                                     self.clear_layout)
        box.pack_end(Gtk.SeparatorToolItem(), True, True, 0)

        # -----------------------
        #  Tools pan 2
        # -----------------------
        box = Gtk.Box(spacing=6, orientation=Gtk.Orientation.HORIZONTAL)
        box_window.pack_start(box, False, False, 0)

        box.pack_start(self.btn_prev_page, False, False, 0)
        self.btn_prev_page.set_sensitive(False)
        self.btn_prev_page.connect("clicked", self.select_prev_page)

        box.pack_start(self.lbl_left_page, False, False, 0)
        box.pack_start(self.page_num_text_entry, False, False, 0)
        box.pack_start(self.lbl_right_page, False, False, 0)
        box.pack_start(self.btn_next_page, True, True, 0)
        self.btn_next_page.connect("clicked", self.select_next_page)
        self.page_num_text_entry.connect("activate", self.page_num_nav)

        box.pack_start(self.btn_pin_page_left, True, True, 0)
        self.btn_pin_page_left.connect("clicked", self.pin_page_left)

        box.pack_start(self.btn_pin_page_right, True, True, 0)
        self.btn_pin_page_right.connect("clicked", self.pin_page_right)

        box.pack_start(self.btn_lock_page_left, True, True, 0)
        self.btn_lock_page_left.connect("clicked", self.lock_page_left)

        box.pack_start(self.btn_lock_page_right, True, True, 0)
        self.btn_lock_page_right.connect("clicked", self.lock_page_right)

        box.pack_start(self.btn_save_all_books, True, True, 0)
        self.btn_save_all_books.connect("clicked", self.pickle_all_books)

        box.pack_start(self.btn_print_all_books, True, True, 0)
        self.btn_print_all_books.connect("clicked", self.print_all_pdfs)
        box.pack_start(Gtk.SeparatorToolItem(), True, True, 0)

        self.btn_submit_order.set_sensitive(False)
        box.pack_start(self.btn_submit_order, True, True, 0)
        self.btn_submit_order.connect("clicked", self.submit_full_order)
        box.pack_start(Gtk.SeparatorToolItem(), True, True, 0)

        self.btn_settings.set_always_show_image(True)
        self.btn_settings.connect("clicked", self.set_settings)
        box.pack_end(self.btn_settings, False, False, 0)

        # --------------------------------------
        #  Tree View And Two Image Viewing Pans
        # --------------------------------------
        box = Gtk.Box(spacing=10)
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
        box = Gtk.Box(spacing=6)
        _scrolledWindow = Gtk.ScrolledWindow()
        _scrolledWindow.add(self.portraits_flow_box)
        _scrolledWindow.set_size_request(100, 300)
        box.pack_start(_scrolledWindow, True, True, 0)
        box_window.pack_start(box, True, True, 0)

        # --------------------------------------------
        #  GTK Flow Box to view other candidate images
        # --------------------------------------------
        _scrolledWindow = Gtk.ScrolledWindow()
        _scrolledWindow.set_size_request(600, 300)
        _scrolledWindow.add(self.images_flow_box)

        notebook = Gtk.Notebook()
        # Create Boxes
        page1 = Gtk.Box()
        page1.set_border_width(50)
        notebook.append_page(_scrolledWindow, Gtk.Label("Images"))

        _scrolledWindow = Gtk.ScrolledWindow()
        _scrolledWindow.set_size_request(600, 300)
        _scrolledWindow.add(self.img_favorites_flow_box)
        page2 = Gtk.Box()
        page2.set_border_width(50)
        notebook.append_page(_scrolledWindow, Gtk.Label("Favorites"))

        notebook.set_show_tabs(True)
        notebook.show()

        box.pack_start(notebook, True, True, 0)
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

        # Update the tool buttons
        self.set_current_corpus()
        self.update_ui_elements()
        self.update_child_portrait_images(self.current_yearbook)
        self.update_favorites_images()
        self.update_deleted_images()

    def get_child_portrait_images(self, yearbook: Yearbook):
        selfies_dir = os.path.join(self.corpus_base_dir, yearbook.school, "Selfies", yearbook.child)
        return [os.path.join(selfies_dir, img) for img in os.listdir(selfies_dir)]

    def page_num_nav(self, widget):
        new_page_num = int(self.page_num_text_entry.get_text())
        if new_page_num % 2 != 0:
            # If user entered an odd number
            self.curr_page_index = new_page_num - 1
        else:
            self.curr_page_index = new_page_num

        self.update_ui_elements()
        print("NextClick - ")

    def add_image_to_deleted(self, image):
        self.deleted_images.add(image)

    def update_deleted_images(self):
        deleted_images = os.listdir(self.get_deleted_images_folder())
        [self.deleted_images.add(os.path.join(self.get_deleted_images_folder(), img)) for img in deleted_images]

    def update_favorites_images(self):
        print("UPDATING FAVORITES")
        flowbox = self.img_favorites_flow_box
        [flowbox.remove(child) for child in flowbox.get_children()]
        flowbox.set_valign(Gtk.Align.START)
        flowbox.set_max_children_per_line(10)
        flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        fav_folder = self.get_favorites_folder()
        favorite_images = [os.path.join(fav_folder, img) for img in os.listdir(fav_folder)]

        for img_path in favorite_images:
            try:
                del_img_path = img_path.replace(fav_folder, self.get_deleted_images_folder())
                if del_img_path not in self.deleted_images:
                    pixbuf = get_orientation_fixed_pixbuf(img_path)
                    image = Gtk.Image.new_from_pixbuf(pixbuf)
                    img_box = Gtk.EventBox()
                    img_box.add(image)
                    img_box.connect("button_press_event", self.invoke_add_image, img_path, favorite_images)
                    flowbox.add(img_box)
            except OSError:
                # raise BadPhoto(name)
                print("Update favorites -- Skipping a photo: %s" % img_path)
                continue

        self.show_all()

    def update_child_portrait_images(self, yearbook: Yearbook):
        flowbox = self.portraits_flow_box
        flowbox.set_valign(Gtk.Align.START)
        flowbox.set_max_children_per_line(3)
        # Need to remove all previously added images
        [flowbox.remove(child) for child in flowbox.get_children()]

        if yearbook.child is not None:
            print("Looking for pictures of %s" % yearbook.child)
            child_portraits = self.get_child_portrait_images(yearbook)

            for img in child_portraits:
                if img.endswith("jpg") or img.endswith("png"):
                    try:
                        pixbuf = get_orientation_fixed_pixbuf(img)
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
            tag_list = get_tag_list_for_page(self.current_yearbook, page)
            tags = get_unique_list_insertion_order(tag_list)
            if self.current_yearbook.child is None:
                candidate_images = self.corpus.get_images_with_tags_strict(tags)
            else:
                candidate_images = self.corpus.get_images_for_child(tags, self.current_yearbook.child)

        # Let's only keep the unique images from this list
        candidate_images = get_unique_list_insertion_order(candidate_images)

        flowbox = self.images_flow_box
        flowbox.set_valign(Gtk.Align.START)
        flowbox.set_max_children_per_line(10)
        flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)

        # Need to remove all previously added images
        [flowbox.remove(child) for child in flowbox.get_children()]

        # Get a set of images used so far
        used_images_set = set()
        for pg in self.current_yearbook.pages:
            [used_images_set.add(photo.filename) for photo in pg.photo_list]

        for img in candidate_images:

            # Let's not add the image to the viewer if it's on the page.
            if img in used_images_set or img in self.deleted_images:
                continue

            try:
                pixbuf = get_orientation_fixed_pixbuf(img)
                if pixbuf is not None:
                    image = Gtk.Image.new_from_pixbuf(pixbuf)
                    img_box = Gtk.EventBox()
                    img_box.add(image)
                    img_box.connect("button_press_event", self.invoke_add_image, img, candidate_images)
                    flowbox.add(img_box)

            except OSError:
                # raise BadPhoto(name)
                print("FlowBox Skipping a photo: %s" % img)
                continue

        self.show_all()

    def is_left_page_locked(self):
        return self.current_yearbook.pages[self.prev_page_index].is_locked()

    def is_right_page_locked(self):
        return self.current_yearbook.pages[self.curr_page_index].is_locked()

    def add_image_to_left_pane(self, img_name):
        print("Updating left page, page index %s " % str(self.curr_page_index))
        self.update_photolist(self.current_yearbook.pages[self.curr_page_index], [img_name], self.left_opts)
        self.update_flow_box_with_images(self.current_yearbook.pages[self.curr_page_index])

    def add_image_to_right_pane(self, img_name):
        print("Updating right page, page index %s " % str(self.next_page_index))
        self.update_photolist(self.current_yearbook.pages[self.next_page_index], [img_name], self.right_opts)
        self.update_flow_box_with_images(self.current_yearbook.pages[self.next_page_index])

    def invoke_add_image(self, widget, event, img_name, images_list):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            if not self.current_yearbook.pages[self.curr_page_index].is_locked():
                self.add_image_to_left_pane(img_name)
        elif event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            if not self.current_yearbook.pages[self.next_page_index].is_locked():
                self.add_image_to_right_pane(img_name)
        else:
            self.per_img_window.update_images_list(images_list)
            self.per_img_window.update_image(img_name)
            self.per_img_window.show_all()

    def update_photolist(self, page: Page, new_images: [str], options: Options = None):
        photolist: [Photo] = []
        page.cleared = False
        try:
            if page.history_index < len(page.history):
                photolist = copy.copy(
                    page.history[page.history_index].photolist)
            photolist.extend(render.build_photolist(new_images))

            if len(photolist) > 0:
                new_collage = UserCollage(photolist)
                new_collage.make_page(options)
                page.update_flag("edited", True)
                print("*******UPDATING EDIT FLAG*********")
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

    def choose_images_for_page(self, page: Page, max_count=6) -> [str]:
        # Let's find the right ranker to delegate to
        ranker = RankerFactory.create_ranker(self.corpus, self.current_yearbook)
        print(
            "choose_images_for_page: (%s, %s, %s) with tags %s" % (page.image, page.event_name, page.number, page.tags))
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
        self.update_photolist(self.current_yearbook.pages[self.curr_page_index], files)
        self.update_flow_box_with_images(self.current_yearbook.pages[self.curr_page_index])

    def render_and_pickle_yearbook(self, store: Gtk.TreeStore, treepath: Gtk.TreePath, treeiter: Gtk.TreeIter):
        _yearbook = store[treeiter][0]
        self.current_yearbook = _yearbook

        output_dir = self.yearbook_parameters['output_dir']
        pickle_path = os.path.join(
            get_pickle_path(output_dir, self.current_yearbook.school,
                            self.current_yearbook.classroom, self.current_yearbook.child), "file.pickle")
        print("operating on current yearbook : %s" % pickle_path)
        if os.path.exists(pickle_path):
            print("will be loaded from pickle file...")
            return

        print("*********First creation of this yearbook********")
        self.current_yearbook.print_yearbook_info()
        for page in self.current_yearbook.pages:
            if page.number % 2 == 0:
                options = self.left_opts
            else:
                options = self.right_opts

            self.render_preview(page, self.img_preview_left, options)
        pickle_yearbook(_yearbook, output_dir)
        print("********Finished rendering pages for the yearbook********")

    def render_left_page(self, page):
        self.render_preview(page, self.img_preview_left, self.left_opts)

    def render_right_page(self, page):
        self.render_preview(page, self.img_preview_right, self.right_opts)

    # TODO:: Break into two methods, one that returns the images for the page and another one that does the render
    def render_preview(self, yearbook_page: Page, img_preview_area: ImagePreviewArea, options: Options):
        print("---Displaying %s %s" % (yearbook_page.event_name, str(yearbook_page.number)))

        rebuild = False
        pin_changed = False
        page_images = []

        if yearbook_page.cleared:
            img_preview_area.image = None
            return

        if yearbook_page.is_locked():
            print("Page %s is locked..." % yearbook_page.number)
            outfile = os.path.join(get_jpg_path(self.yearbook_parameters['output_dir'],
                                                self.current_yearbook.school,
                                                self.current_yearbook.classroom,
                                                self.current_yearbook.child),
                                   str(yearbook_page.number) + ".png")
            from PIL import ImageOps

            img_preview_area.image = pil_image_to_cairo_surface(
                ImageOps.grayscale(PIL.Image.open(outfile))
            )
            print("Finished displayed grayscale single image")
            return

        # If this page has never been edited,
        if not yearbook_page.is_edited():
            if self.current_yearbook.parent_yearbook is not None:
                try:
                    print("******We have a parent, let's retrieve from there,*****")
                    parent_page: Page = yearbook_page.parent_pages[-1]
                    page_collage: UserCollage = parent_page.history[-1].duplicate_with_layout()
                except IndexError:
                    # This is a custom page
                    print("////////////RETRIEVE CUSTOM IMAGES/////////////////////")
                    child_order_id = self.current_yearbook.orders[0].wix_order_id
                    custom_order_dir = os.path.join(self.corpus_base_dir, self.current_yearbook.school, 'CustomPhotos', child_order_id)
                    if os.path.exists(custom_order_dir):
                        page_images = [os.path.join(custom_order_dir, img) for img in os.listdir(custom_order_dir) if img.endswith("jpg") or img.endswith("jpeg") or img.endswith("png")]
                    else:
                        page_images = [os.path.join(self.corpus_base_dir, self.current_yearbook.school, "blank.png")]

                    [print(img) for img in page_images]

                    first_photo_list: [Photo] = render.build_photolist(page_images)
                    page_collage = UserCollage(first_photo_list)
                    page_collage.make_page(options)

                yearbook_page.photo_list: [Photo] = page_collage.photolist
                yearbook_page.history.append(page_collage)
            elif yearbook_page.history_index < 0:
                print("No parent exists, so we create from scratch")
                page_images = self.choose_images_for_page(yearbook_page)
                first_photo_list: [Photo] = render.build_photolist(page_images)

                [print(img.filename) for img in first_photo_list]

                page_collage = UserCollage(first_photo_list)
                page_collage.make_page(options)
                yearbook_page.photo_list = first_photo_list
                yearbook_page.history.append(page_collage)
        else:
            if yearbook_page.has_parent_pins_changed():
                new_images = yearbook_page.get_filenames_parent_pins_not_on_page()
                existing_images = yearbook_page.photos_on_page
                new_images.extend(existing_images)
                page_images = get_unique_list_insertion_order(new_images)
                pin_changed = True
                rebuild = True

            if yearbook_page.did_parent_delete():
                if pin_changed:
                    existing_images = page_images
                else:
                    existing_images = yearbook_page.photos_on_page

                parent_deleted_set = yearbook_page.get_parent_deleted_photos()
                # remove parent deleted images from existing set
                page_images = [img for img in existing_images if img not in parent_deleted_set]
                rebuild = True

            if rebuild:
                first_photo_list = render.build_photolist(page_images)
                page_collage = UserCollage(first_photo_list)
                page_collage.make_page(options)
                yearbook_page.photo_list = first_photo_list
                yearbook_page.history.append(page_collage)
            else:
                # If the images of the current page are the same as the parent
                # then we want to update and copy the most recent layout of the parent
                from yearbook.Corpus import intersection
                if self.current_yearbook.parent_yearbook is not None:
                    parent_page: Page = self.current_yearbook.parent_yearbook.pages[yearbook_page.number - 1]
                    if set(yearbook_page.photo_list) == set(parent_page.photo_list):
                        page_collage: UserCollage = parent_page.history[-1]
                        # Need to copy the parent layout in this case
                        yearbook_page.history.append(page_collage)
                    else:
                        pass

        page_collage: UserCollage = yearbook_page.history[yearbook_page.history_index]
        # If the desired ratio changed in the meantime (e.g. from landscape to
        # portrait), it needs to be re-updated
        page_collage.page.target_ratio = 1.0 * options.out_h / options.out_w
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
            yearbook_page.canvas = img
            comp_dialog.destroy()

        def on_fail(exception):
            dialog = ErrorDialog(self, "{}:\n\n{}".format(
                _("An error occurred while rendering image:"), exception))
            comp_dialog.destroy()
            dialog.run()
            dialog.destroy()

        out_file = os.path.join(get_jpg_path(self.yearbook_parameters['output_dir'],
                                             self.current_yearbook.school,
                                             self.current_yearbook.classroom, self.current_yearbook.child),
                                str(yearbook_page.number) + ".png")

        t = render.RenderingTask(
            yearbook_page,
            page_collage.page,
            output_file=out_file,
            border_width=options.border_w * max(page_collage.page.w,
                                                page_collage.page.h),
            border_color=options.border_c,
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
        self.update_tool_buttons()
        if page.number % 2 != 0:
            self.render_preview(page, self.img_preview_left, self.left_opts)
        else:
            self.render_preview(page, self.img_preview_right, self.right_opts)

    def clear_layout(self, button):
        if button.get_label().endswith("Right"):
            self.current_yearbook.pages[self.next_page_index].clear_all()
            self.img_preview_right.image = None
        else:
            self.current_yearbook.pages[self.curr_page_index].clear_all()
            self.img_preview_left.image = None

    def regenerate_layout(self, button):
        if button.get_label().endswith("Right"):
            page = self.current_yearbook.pages[self.next_page_index]
            options = self.right_opts
        else:
            page = self.current_yearbook.pages[self.curr_page_index]
            options = self.left_opts

        new_collage = page.history[page.history_index].duplicate()
        new_collage.make_page(options, shuffle=True)
        self.render_from_new_collage(page, new_collage)

    def stitch_print_images(self, yearbook: Yearbook):
        output_dir = self.yearbook_parameters['output_dir']

        page_collages = [
            page.history[page.history_index] for page in yearbook.pages]

        # We need to ignore the first page and the last page as they are the covers
        for page, page_collage in zip(yearbook.pages, page_collages):
            new_img_path = os.path.join(get_jpg_path(output_dir, yearbook.school,
                                                     yearbook.classroom, yearbook.child),
                                        str(page.number) + "_stitched.png")

            if page.personalized and page.number % 2 != 0:
                options = self.right_opts
            else:
                options = self.left_opts

            enlargement = float(options.out_w) / page_collage.page.w

            page_collage.page.scale(enlargement)

            # Display a "please wait" dialog and do the job.
            compdialog = ComputingDialog(self)

            def on_update(img, fraction_complete):
                compdialog.update(fraction_complete)

            def on_complete(img, out_file):
                compdialog.destroy()

            def on_fail(exception):
                dialog = ErrorDialog(self, "{}:\n\n{}".format(
                    _("An error occurred while rendering image:"), exception))
                compdialog.destroy()
                dialog.run()
                dialog.destroy()

            t = render.RenderingTask(
                page,
                page_collage.page,
                output_file=new_img_path,
                border_width=options.border_w * max(page_collage.page.w,
                                                    page_collage.page.h),
                border_color=options.border_c,
                on_update=gtk_run_in_main_thread(on_update),
                on_complete=gtk_run_in_main_thread(on_complete),
                on_fail=gtk_run_in_main_thread(on_fail),
                stitch_background=True)
            t.start()

            response = compdialog.run()
            if response == Gtk.ResponseType.CANCEL:
                t.abort()
                compdialog.destroy()

        os.makedirs(os.path.join(output_dir, "pdf_outputs"), exist_ok=True)

    def get_folder(self, folder_name):
        if self.current_yearbook is None or self.current_yearbook.school is None:
            return None

        folder = os.path.join(self.corpus_base_dir, self.current_yearbook.school, folder_name)
        if not os.path.exists(folder):
            os.makedirs(folder)

        return folder

    def get_favorites_folder(self):
        return self.get_folder("Favorites")

    def get_deleted_images_folder(self):
        return self.get_folder("Deleted")

    def print_all_pdfs(self, button):
        self.treeModel.foreach(self.create_pdfs)
        self.btn_submit_order.set_sensitive(True)

    def create_pdf_for_printing(self, yearbook: Yearbook, pdf_full_path: str, cover_format: str):

        if yearbook.parent_yearbook is None or yearbook.is_edited():
            # TODO:: REMOVE LATER WHEN IN FULL PRODUCTION
            if os.path.exists(pdf_full_path):
                return False

            self.stitch_print_images(yearbook)
            images = []
            if cover_format == 'Digital':
                pages = yearbook.pages
            else:
                pages = yearbook.pages[1:-1]

            for page in pages:
                images.append(os.path.join(get_jpg_path(self.yearbook_parameters['output_dir'],
                                                        yearbook.school,
                                                        yearbook.classroom,
                                                        yearbook.child),
                                           str(page.number) + "_stitched.png"))

            print("Creating PDF from images")
            create_pdf_from_images(pdf_full_path, images)
            return False
        else:
            print("Will copy the parent PDF here")
            # You should copy the parent file at the new PDF location
            parent_pdf_path = self.get_pdf_base_path(yearbook.parent_yearbook) + cover_format + ".pdf"

            if not os.path.exists(pdf_full_path):
                shutil.copyfile(parent_pdf_path, pdf_full_path)

            return True

    def get_pdf_base_path(self, yearbook):
        output_dir = self.yearbook_parameters['output_dir']
        if yearbook.classroom is None:
            pdf_path = os.path.join(output_dir, "pdf_outputs", yearbook.school)
        elif yearbook.child is None:
            pdf_path = os.path.join(output_dir, "pdf_outputs", yearbook.school + "_" + yearbook.classroom)
        else:
            pdf_path = os.path.join(output_dir, "pdf_outputs", yearbook.school + "_" + yearbook.classroom + "_"
                                    + yearbook.child)

        return pdf_path

    def create_pdfs(self, store: Gtk.TreeStore, treepath: Gtk.TreePath, treeiter: Gtk.TreeIter):
        _yearbook: Yearbook = store[treeiter][0]
        extension = ".pdf"
        pdf_base_path = self.get_pdf_base_path(_yearbook)

        cover_settings: CoverSettings = get_cover_settings("HardCover")
        stitch_print_ready_cover(pdf_base_path + "HardCover" + extension,
                                 _yearbook, cover_settings)

        cover_settings: CoverSettings = get_cover_settings("SoftCover")
        stitch_print_ready_cover(pdf_base_path + "SoftCover" + extension,
                                 _yearbook, cover_settings)

        pdf_full_path = pdf_base_path + "HardCover" + extension
        self.create_pdf_for_printing(_yearbook, pdf_full_path, "HardCover")

    def create_and_upload_pdfs(self, store: Gtk.TreeStore, treepath: Gtk.TreePath, treeiter: Gtk.TreeIter):
        _yearbook: Yearbook = store[treeiter][0]
        print("****************************************************************")
        print("UPLOADING FOR YEARBOOK %s " % _yearbook.print_yearbook_info())
        print("STEP 1: Create_print_pdf %s " % str(treepath.get_depth()))
        extension = ".pdf"
        pdf_base_path = self.get_pdf_base_path(_yearbook)

        if _yearbook.child is None:
            # Let's create three dummy orders
            # Hardcover, softcover and digital.
            order_hard_cover = OrderDetails("root", "HardCover")
            order_hard_cover.interior_pdf_url = get_url_from_file_id('1OukkFgfBhWFYUmPPFOL1hyHAQ3JYrIiW')

            order_soft_cover = OrderDetails("root", "SoftCover")
            order_soft_cover.interior_pdf_url = order_hard_cover.interior_pdf_url

            order_digital = OrderDetails("root", "Digital")
            order_digital.interior_pdf_url = get_url_from_file_id("1nLWav7G19LlOEapMOdNiEvq61tvbf_de")

            # Let's upload only the original PDF if required
            _yearbook.pickle_yearbook.orders = [order_digital, order_soft_cover, order_hard_cover]
            pickle_yearbook(_yearbook, self.yearbook_parameters['output_dir'])

        # If we have orders for this yearbook, then let's create the necessary PDFs
        for order in _yearbook.pickle_yearbook.orders:
            print("-----------------------------------%s----------------------------------" % order.cover_format)
            if order.lulu_job_id is None:
                print("We have no lulu print job for this order %s " % order.cover_format)
                # Find the cover setting to create
                cover_settings: CoverSettings = get_cover_settings(order.cover_format)
                # Upload new cover
                if cover_settings is not None:
                    print("STEP 2: Create_cover_pages with %s " % order.cover_format)
                    cover_path = stitch_print_ready_cover(pdf_base_path + order.cover_format + extension,
                                                          _yearbook, cover_settings)
                    # Upload the cover
                    order.cover_url = get_url_from_file_id(upload_with_item_check('1UWyYpHCUJ2lIUP0wOrTwtFeXYOXTd5x9',
                                                                                  cover_path,
                                                                                  get_file_id_from_url(
                                                                                      order.cover_url)))

                    print("STEP 2: Finished uploading cover file")
                else:
                    print("STEP 2: It's a digital file format, so no cover uploads")

                # Now create the interior book
                pdf_full_path = pdf_base_path + order.cover_format + extension
                print("STEP 3: Creating INTERNAL PDF File :------")

                reused = self.create_pdf_for_printing(_yearbook, pdf_full_path, order.cover_format)

                if reused:
                    # We have to get the parent pdf url
                    order.interior_pdf_url = _yearbook.parent_yearbook.get_interior_url(order.cover_format)
                    print("Reusing URL %s " % order.interior_pdf_url)
                else:
                    print("Uploading %s" % pdf_full_path)
                    order.interior_pdf_url = get_url_from_file_id(
                        upload_with_item_check('1UWyYpHCUJ2lIUP0wOrTwtFeXYOXTd5x9',
                                               pdf_full_path,
                                               get_file_id_from_url(
                                                   order.interior_pdf_url)))

            self.order_items.append(order)
            print("------------------------------------------------------------------------")

        # Let's pickle the yearbook. Now we have a track of uploaded items on Google Drive
        pickle_yearbook(_yearbook, self.yearbook_parameters['output_dir'])
        print("****************************************************************")

        return

    def submit_full_order(self, widget):
        self.treeModel.foreach(self.create_and_upload_pdfs)
        import json
        job_payload = create_order_payload(self.order_items, "RETHINK_YEARBOOKS")
        headers = get_header()
        # response = requests.request('POST', print_job_url, data=job_payload, headers=headers)

        # Now we need to parse the response, to make sure the order went through
        # response_json = json.loads(response.text)

        print(job_payload)
        return job_payload

    def pin_page_left(self, button):
        left_page = self.current_yearbook.pages[self.curr_page_index]
        update_flag_for_page(left_page, button, "pinned")
        if button.get_active():
            pin_all_photos_on_page(left_page, self.img_preview_left)

        self.render_left_page(left_page)

    def pin_page_right(self, button):
        right_page = self.current_yearbook.pages[self.next_page_index]
        update_flag_for_page(right_page, button, "pinned")
        if button.get_active():
            pin_all_photos_on_page(right_page, self.img_preview_right)

        self.render_right_page(right_page)

    def lock_page_left(self, button):
        left_page = self.current_yearbook.pages[self.curr_page_index]
        update_flag_for_page(left_page, button, "locked")
        self.render_left_page(left_page)

    def lock_page_right(self, button):
        right_page = self.current_yearbook.pages[self.next_page_index]
        update_flag_for_page(right_page, button, "locked")
        self.render_right_page(right_page)

    def pickle_book(self, store: Gtk.TreeStore, treepath: Gtk.TreePath, treeiter: Gtk.TreeIter):
        _yearbook = store[treeiter][0]
        pickle_yearbook(_yearbook, self.yearbook_parameters['output_dir'])

    def pickle_all_books(self, button):
        self.treeModel.foreach(self.pickle_book)

    def select_next_page(self, button):
        # Increment to the next left page
        self.curr_page_index += 2
        self.update_ui_elements()
        print("NextClick - ")

    def select_prev_page(self, button):
        self.curr_page_index -= 2
        self.update_ui_elements()
        print("PrevClick - ")

    def update_ui_elements(self):
        print("current index %s, next page index %s" % (self.curr_page_index, self.next_page_index))

        # Reset the prev and next buttons
        self.btn_prev_page.set_sensitive(self.curr_page_index > 0)
        if self.next_page_index > len(self.current_yearbook.pages):
            self.curr_page_index = 0

        try:
            left_page = self.current_yearbook.pages[self.curr_page_index]
            self.render_left_page(left_page)
        except IndexError:
            pass

        right_page = self.current_yearbook.pages[self.next_page_index]
        self.render_right_page(right_page)

        self.update_flow_box_with_images(left_page)
        self.update_favorites_images()

        self.update_label_text()
        self.btn_lock_page_left.set_active(left_page.is_locked())
        self.btn_lock_page_right.set_active(right_page.is_locked())

        self.btn_pin_page_left.set_active(left_page.is_pinned())
        self.btn_pin_page_right.set_active(right_page.is_pinned())

    def set_settings(self, button):
        dialog = SettingsDialog(self)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            dialog.apply_opts(self.left_opts)
            dialog.destroy()

            if self.current_yearbook:
                page = self.current_yearbook.pages[self.curr_page_index]
                if page.history:
                    if page.number % 2 != 0:
                        self.render_preview(page, self.img_preview_left)
                    else:
                        self.render_preview(page, self.img_preview_right)
        else:
            dialog.destroy()

    def update_label_text(self):

        try:
            _left = self.current_yearbook.pages[self.curr_page_index]
            _label_text = str(_left.number) + ":" + _left.event_name
            self.lbl_left_page.set_label(_label_text)
        except IndexError:
            self.lbl_left_page.set_label(str("-1"))

        _right = self.current_yearbook.pages[self.next_page_index]
        self.lbl_right_page.set_label(str(_right.number) + ":" + _right.event_name)
        self.page_num_text_entry.set_text(str(_right.number))

    def update_tool_buttons(self):
        if self.current_yearbook is None:
            return

        left_page = self.current_yearbook.pages[self.prev_page_index]
        right_page = self.current_yearbook.pages[self.curr_page_index]

        self.btn_undo.set_sensitive(left_page.history_index > 0)
        self.btn_redo.set_sensitive(left_page.history_index < len(left_page.history) - 1)
        if left_page.history_index < len(left_page.history):
            self.lbl_history_index.set_label(str(left_page.history_index + 1))
        else:
            self.lbl_history_index.set_label(" ")
        self.btn_regen_left.set_sensitive(
            left_page.history_index < len(left_page.history))
        self.btn_regen_right.set_sensitive(right_page.history_index < len(right_page.history))


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
