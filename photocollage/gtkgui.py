# -*- coding: utf-8 -*-
"""
Copyright (C) 2013 Adrien Vergé

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

import cairo
import copy
import gettext
from gi.repository import Gtk, Gdk, GObject
from io import BytesIO
import math
import os.path
import sys

from photocollage import APP_NAME, artwork, collage, render
from photocollage.render import PIL_SUPPORTED_EXTS as EXTS


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
    all = []
    for type in all_types:
        for ext in all_types[type]:
            all.append(ext)

    return all


def set_open_image_filters(dialog):
    """Set our own filter because Gtk.FileFilter.add_pixbuf_formats() contains
    formats not supported by PIL.

    """
    # Do not show the filter to the user, just limit selectable files
    imgfilter = Gtk.FileFilter()
    imgfilter.set_name(_("All supported image formats"))

    all_types = dict(list(EXTS.RW.items()) + list(EXTS.RO.items()))
    for type in all_types:
        for ext in all_types[type]:
            imgfilter.add_pattern("*." + ext)
            imgfilter.add_pattern("*." + ext.upper())

    dialog.add_filter(imgfilter)
    dialog.set_filter(imgfilter)


def set_save_image_filters(dialog):
    """Set our own filter because Gtk.FileFilter.add_pixbuf_formats() contains
    formats not supported by PIL.

    """
    all_types = dict(list(EXTS.RW.items()) + list(EXTS.WO.items()))
    filters = []

    filters.append(Gtk.FileFilter())
    flt = filters[-1]
    flt.set_name(_("All supported image formats"))
    for ext in get_all_save_image_exts():
        flt.add_pattern("*." + ext)
        flt.add_pattern("*." + ext.upper())
    dialog.add_filter(flt)
    dialog.set_filter(flt)

    for type in all_types:
        filters.append(Gtk.FileFilter())
        flt = filters[-1]
        name = _("%s image") % type
        name += " (." + ", .".join(all_types[type]) + ")"
        flt.set_name(name)
        for ext in all_types[type]:
            flt.add_pattern("*." + ext)
            flt.add_pattern("*." + ext.upper())
        dialog.add_filter(flt)


def gtk_run_in_main_thread(fn):
    def my_fn(*args, **kwargs):
        GObject.idle_add(fn, *args, **kwargs)
    return my_fn


class PhotoCollageWindow(Gtk.Window):
    def __init__(self):
        super(PhotoCollageWindow, self).__init__(title=_("PhotoCollage"))
        self.layout_histo = []
        self.current_layout = -1

        class Options(object):
            def __init__(self):
                self.no_cols = 1
                self.border_w = 0.02
                self.border_c = "black"
                self.out_w = 2000

        self.opts = Options()

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

        self.btn_choose_images = Gtk.Button(label=_("Input images..."))
        self.btn_choose_images.set_image(Gtk.Image.new_from_stock(
            Gtk.STOCK_OPEN, Gtk.IconSize.LARGE_TOOLBAR))
        self.btn_choose_images.set_always_show_image(True)
        self.btn_choose_images.connect("clicked", self.choose_images)
        box.pack_start(self.btn_choose_images, False, False, 0)

        self.lbl_images = Gtk.Label(_("no image loaded"))
        box.pack_start(self.lbl_images, False, False, 0)

        self.btn_save = Gtk.Button(label=_("Save poster..."))
        self.btn_save.set_image(Gtk.Image.new_from_stock(
            Gtk.STOCK_SAVE_AS, Gtk.IconSize.LARGE_TOOLBAR))
        self.btn_save.set_always_show_image(True)
        self.btn_save.connect("clicked", self.save_poster)
        box.pack_end(self.btn_save, False, False, 0)

        # -----------------------
        #  Tools pan
        # -----------------------

        box = Gtk.Box(spacing=6)
        box_window.pack_start(box, False, False, 0)

        self.btn_undo = Gtk.Button()
        self.btn_undo.set_image(Gtk.Image.new_from_stock(
            Gtk.STOCK_UNDO, Gtk.IconSize.LARGE_TOOLBAR))
        self.btn_undo.connect("clicked", self.select_prev_layout)
        box.pack_start(self.btn_undo, False, False, 0)
        self.lbl_current_layout = Gtk.Label(" ")
        box.pack_start(self.lbl_current_layout, False, False, 0)
        self.btn_redo = Gtk.Button()
        self.btn_redo.set_image(Gtk.Image.new_from_stock(
            Gtk.STOCK_REDO, Gtk.IconSize.LARGE_TOOLBAR))
        self.btn_redo.connect("clicked", self.select_next_layout)
        box.pack_start(self.btn_redo, False, False, 0)
        self.btn_new_layout = Gtk.Button(label=_("Regenerate"))
        self.btn_new_layout.set_image(Gtk.Image.new_from_stock(
            Gtk.STOCK_REFRESH, Gtk.IconSize.LARGE_TOOLBAR))
        self.btn_new_layout.set_always_show_image(True)
        self.btn_new_layout.connect("clicked", self.regenerate_layout)
        box.pack_start(self.btn_new_layout, False, False, 0)

        box.pack_start(Gtk.SeparatorToolItem(), True, True, 0)

        self.btn_less_cols = Gtk.Button()
        self.btn_less_cols.set_image(Gtk.Image.new_from_pixbuf(
            artwork.load_pixbuf(artwork.ICON_EXPAND_VERTICALLY)))
        self.btn_less_cols.connect("clicked", self.less_cols)
        box.pack_start(self.btn_less_cols, False, False, 0)
        self.btn_more_cols = Gtk.Button()
        self.btn_more_cols.set_image(Gtk.Image.new_from_pixbuf(
            artwork.load_pixbuf(artwork.ICON_EXPAND_HORIZONTALLY)))
        self.btn_more_cols.connect("clicked", self.more_cols)
        box.pack_start(self.btn_more_cols, False, False, 0)

        box.pack_start(Gtk.SeparatorToolItem(), True, True, 0)

        self.btn_border = Gtk.Button(label=_("Border..."))
        self.btn_border.set_image(Gtk.Image.new_from_stock(
            Gtk.STOCK_SELECT_COLOR, Gtk.IconSize.LARGE_TOOLBAR))
        self.btn_border.set_always_show_image(True)
        self.btn_border.connect("clicked", self.set_border_options)
        box.pack_end(self.btn_border, False, False, 0)

        # -------------------
        #  Image preview pan
        # -------------------

        box = Gtk.Box(spacing=10)
        box_window.pack_start(box, True, True, 0)

        self.img_preview = ImagePreviewArea(self)
        self.img_preview.set_size_request(600, 400)
        self.img_preview.connect("drag-data-received", self.on_drag)
        self.img_preview.drag_dest_set(Gtk.DestDefaults.ALL, [],
                                       Gdk.DragAction.COPY)
        self.img_preview.drag_dest_add_text_targets()
        box.pack_start(self.img_preview, True, True, 0)

        self.btn_save.set_sensitive(False)

        self.btn_undo.set_sensitive(False)
        self.btn_redo.set_sensitive(False)

        self.update_photolist([])

    def update_photolist(self, source_images):
        try:
            self.photolist = render.build_photolist(source_images)

            n = len(self.photolist)
            if n > 0:
                self.lbl_images.set_text(_n("%(num)d image loaded",
                                            "%(num)d images loaded", n)
                                         % {"num": n})
                self.opts.no_cols = int(round(
                    1.5 * math.sqrt(len(self.photolist))))
                self.regenerate_layout()
            else:
                self.lbl_images.set_text(_("no image loaded"))
                self.update_tool_buttons()
        except render.BadPhoto as e:
            dialog = ErrorDialog(
                self, _("This image could not be opened:\n\"%(imgname)s\".")
                % {"imgname": e.photoname})
            dialog.run()
            dialog.destroy()

    def choose_images(self, button):
        dialog = Gtk.FileChooserDialog(_("Choose images"),
                                       button.get_toplevel(),
                                       Gtk.FileChooserAction.OPEN,
                                       select_multiple=True)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)

        set_open_image_filters(dialog)

        if dialog.run() == Gtk.ResponseType.OK:
            files = dialog.get_filenames()
            dialog.destroy()
            self.update_photolist(files)
        else:
            dialog.destroy()

    def on_drag(self, widget, drag_context, x, y, data, info, time):
        files = data.get_text().splitlines()
        for i in range(len(files)):
            if files[i].startswith("file://"):
                files[i] = files[i][7:]
        self.update_photolist(files)

    def render_preview(self):
        page = self.layout_histo[self.current_layout]

        w = self.img_preview.get_allocation().width
        h = self.img_preview.get_allocation().height
        page.scale_to_fit(w, h)

        # Display a "please wait" dialog and do the job.
        compdialog = ComputingDialog(self)

        def on_update(img, fraction_complete):
            self.img_preview.set_image(img, page)
            compdialog.update(fraction_complete)

        def on_complete(img):
            self.img_preview.set_image(img, page)
            compdialog.destroy()
            self.btn_save.set_sensitive(True)

        def on_fail():
            dialog = ErrorDialog(
                self, _("An error occurred while rendering image."))
            compdialog.destroy()
            dialog.run()
            dialog.destroy()
            self.btn_save.set_sensitive(False)

        t = render.InteractiveRenderingTask(
            page,
            border_width=self.opts.border_w * max(page.w, page.h),
            border_color=self.opts.border_c,
            on_update=gtk_run_in_main_thread(on_update),
            on_complete=gtk_run_in_main_thread(on_complete),
            on_fail=gtk_run_in_main_thread(on_fail))
        t.start()

        response = compdialog.run()
        if response == Gtk.ResponseType.CANCEL:
            t.abort()
            compdialog.destroy()

    def generate_from_page(self, page):
        self.layout_histo.append(page)
        self.current_layout = len(self.layout_histo) - 1
        self.update_tool_buttons()
        self.render_preview()

    def regenerate_layout(self, button=None):
        page = collage.Page(1.0, self.opts.no_cols)
        for photo in self.photolist:
            page.add_cell(photo)
        page.adjust()

        self.generate_from_page(page)

    def select_prev_layout(self, button):
        self.current_layout -= 1
        self.update_tool_buttons()
        self.render_preview()

    def select_next_layout(self, button):
        self.current_layout += 1
        self.update_tool_buttons()
        self.render_preview()

    def less_cols(self, button):
        self.opts.no_cols = max(1, self.opts.no_cols - 1)
        self.regenerate_layout()

    def more_cols(self, button):
        self.opts.no_cols += 1
        self.regenerate_layout()

    def set_border_options(self, button):
        dialog = BorderOptionsDialog(self)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            dialog.apply_opts(self.opts)
            dialog.destroy()
            if self.layout_histo:
                self.render_preview()
        else:
            dialog.destroy()

    def save_poster(self, button):
        page = self.layout_histo[self.current_layout]

        dialog = SaveImageDialog(self, self.opts, page.ratio)
        if dialog.run() != Gtk.ResponseType.OK:
            dialog.destroy()
            return
        self.opts.out_w = dialog.get_poster_width()
        dialog.destroy()

        enlargement = float(self.opts.out_w) / page.w
        page.scale(enlargement)

        dialog = Gtk.FileChooserDialog(_("Save image"), button.get_toplevel(),
                                       Gtk.FileChooserAction.SAVE)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        dialog.set_do_overwrite_confirmation(True)
        set_save_image_filters(dialog)
        if dialog.run() != Gtk.ResponseType.OK:
            dialog.destroy()
            return
        savefile = dialog.get_filename()
        base, ext = os.path.splitext(savefile)
        if ext == "" or not ext[1:].lower() in get_all_save_image_exts():
            savefile += ".jpg"
        dialog.destroy()

        # Display a "please wait" dialog and do the job.
        compdialog = PulsingComputingDialog(self)

        def on_complete():
            compdialog.destroy()

        def on_fail():
            dialog = ErrorDialog(
                self, _("An error occurred while rendering image."))
            compdialog.destroy()
            dialog.run()
            dialog.destroy()

        t = render.BatchRenderingTask(
            savefile, page,
            border_width=self.opts.border_w * max(page.w, page.h),
            border_color=self.opts.border_c,
            on_complete=gtk_run_in_main_thread(on_complete),
            on_fail=gtk_run_in_main_thread(on_fail))
        t.start()

        response = compdialog.run()
        if response == Gtk.ResponseType.CANCEL:
            t.abort()
            compdialog.destroy()

    def update_tool_buttons(self):
        self.btn_undo.set_sensitive(self.current_layout > 0)
        self.btn_redo.set_sensitive(
            self.current_layout < len(self.layout_histo) - 1)
        if self.current_layout >= 0:
            self.lbl_current_layout.set_label(str(self.current_layout + 1))
        self.btn_new_layout.set_sensitive(self.current_layout >= 0)
        self.btn_less_cols.set_sensitive(self.current_layout >= 0
                                         and self.opts.no_cols > 1)
        self.btn_more_cols.set_sensitive(self.current_layout >= 0)


class ImagePreviewArea(Gtk.DrawingArea):
    """Area to display the poster preview and react to user actions"""
    INSENSITIVE, FLYING, SWAPING = range(3)

    def __init__(self, parent):
        super(ImagePreviewArea, self).__init__()
        self.parent = parent

        parse, color = Gdk.Color.parse("#888888")
        self.modify_bg(Gtk.StateType.NORMAL, color)

        # http://www.pygtk.org/pygtk2tutorial/sec-EventHandling.html
        # https://developer.gnome.org/gdk3/stable/gdk3-Events.html#GdkEventMask
        self.connect("draw", self.draw)
        self.connect("motion-notify-event", self.motion_notify_event)
        self.connect("leave-notify-event", self.motion_notify_event)
        self.connect("button-press-event", self.button_press_event)
        self.connect("button-release-event", self.button_release_event)
        self.set_events(Gdk.EventMask.EXPOSURE_MASK
                        | Gdk.EventMask.LEAVE_NOTIFY_MASK
                        | Gdk.EventMask.BUTTON_PRESS_MASK
                        | Gdk.EventMask.BUTTON_RELEASE_MASK
                        | Gdk.EventMask.POINTER_MOTION_MASK)

        self.image = None
        self.mode = self.INSENSITIVE

        class SwapEnd(object):
            def __init__(self, cell=None, x=0, y=0):
                self.cell = cell
                self.x = x
                self.y = y

        self.x, self.y = 0, 0
        self.swap_origin = SwapEnd()
        self.swap_dest = SwapEnd()

    def set_image(self, image, page):
        self.image = pil_image_to_cairo_surface(image)
        # The Page object must be copied deep. Otherwise, swaping photos in a
        # new page would also affect the original page (in history). The deep
        # copy is done here (not in button_release_event) because references
        # to cells are gathered in other functions, so that making the copy
        # at the end would invalidate these references.
        self.page = copy.deepcopy(page)
        self.mode = self.FLYING
        self.queue_draw()

    def get_image_offset(self):
        return (round((self.get_allocation().width
                       - self.image.get_width()) / 2.0),
                round((self.get_allocation().height
                       - self.image.get_height()) / 2.0))

    def get_pos_in_image(self, x, y):
        if self.image is not None:
            x0, y0 = self.get_image_offset()
            return (int(round(x - x0)), int(round(y - y0)))
        return (int(round(x)), int(round(y)))

    def paint_image_border(self, context, cell, dash=None):
        x0, y0 = self.get_image_offset()

        context.set_source_rgb(1.0, 1.0, 0.0)
        context.set_line_width(2)
        if dash is not None:
            context.set_dash(dash)
        context.rectangle(x0 + cell.x + 1, y0 + cell.y + 1,
                          cell.w - 2, cell.h - 2)
        context.stroke()

    def draw(self, widget, context):
        if self.image is not None:
            x0, y0 = self.get_image_offset()
            context.set_source_surface(self.image, x0, y0)
            context.paint()

            if self.mode == self.FLYING:
                cell = self.page.get_cell_at_position(self.x, self.y)
                if cell:
                    self.paint_image_border(context, cell)
            elif self.mode == self.SWAPING:
                self.paint_image_border(context, self.swap_origin.cell, (3, 3))
                cell = self.page.get_cell_at_position(self.x, self.y)
                if cell and cell != self.swap_origin.cell:
                    self.paint_image_border(context, cell, (3, 3))

        return False

    def motion_notify_event(self, widget, event):
        self.x, self.y = self.get_pos_in_image(event.x, event.y)
        widget.queue_draw()

    def button_press_event(self, widget, event):
        if self.mode == self.FLYING:
            self.swap_origin.x, self.swap_origin.y = \
                self.get_pos_in_image(event.x, event.y)
            self.swap_origin.cell = self.page.get_cell_at_position(
                self.swap_origin.x, self.swap_origin.y)
            if self.swap_origin.cell:
                self.mode = self.SWAPING
        widget.queue_draw()

    def button_release_event(self, widget, event):
        if self.mode == self.SWAPING:
            self.swap_dest.x, self.swap_dest.y = \
                self.get_pos_in_image(event.x, event.y)
            self.swap_dest.cell = self.page.get_cell_at_position(
                self.swap_dest.x, self.swap_dest.y)
            if self.swap_dest.cell \
                    and self.swap_origin.cell != self.swap_dest.cell:
                self.page.swap_photos(self.swap_origin.cell,
                                      self.swap_dest.cell)
                self.parent.generate_from_page(self.page)
            self.mode = self.FLYING
        widget.queue_draw()


class BorderOptionsDialog(Gtk.Dialog):
    def __init__(self, parent):
        super(BorderOptionsDialog, self).__init__(
            ("Border options"), parent, 0,
            (Gtk.STOCK_OK, Gtk.ResponseType.OK,
             Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        self.set_border_width(10)

        box = self.get_content_area()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.add(vbox)

        box = Gtk.Box(spacing=6)
        vbox.pack_start(box, False, False, 0)
        label = Gtk.Label(_("Border width (%):"), xalign=0)
        box.pack_start(label, True, True, 0)
        self.etr_border = Gtk.Entry(text=str(100.0 * parent.opts.border_w))
        self.etr_border.connect("changed", self.validate_float)
        self.etr_border.last_valid_text = self.etr_border.get_text()
        box.pack_start(self.etr_border, False, False, 0)

        box = Gtk.Box(spacing=6)
        vbox.pack_start(box, False, False, 0)
        label = Gtk.Label(_("Border color:"), xalign=0)
        box.pack_start(label, True, True, 0)
        colors = ((0, "black", _("black")),
                  (1, "white", _("white")))
        self.cmb_bordercolor = Gtk.ComboBoxText()
        for i, cid, clabel in colors:
            self.cmb_bordercolor.insert(i, cid, clabel)
            if cid == parent.opts.border_c:
                self.cmb_bordercolor.set_active(i)
        box.pack_start(self.cmb_bordercolor, False, False, 0)

        self.show_all()

    def validate_float(self, entry):
        entry_text = entry.get_text() or '0'
        try:
            float(entry_text)
            entry.last_valid_text = entry_text
        except ValueError:
            entry.set_text(entry.last_valid_text)

    def apply_opts(self, opts):
        opts.border_w = float(self.etr_border.get_text() or '0') / 100.0
        iter = self.cmb_bordercolor.get_active_iter()
        opts.border_c = self.cmb_bordercolor.get_model()[iter][1]


class SaveImageDialog(Gtk.Dialog):
    def __init__(self, parent, opts, ratio):
        super(SaveImageDialog, self).__init__(
            _("Save image"), parent, 0,
            (Gtk.STOCK_OK, Gtk.ResponseType.OK,
             Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        self.set_border_width(10)

        self.ratio = ratio

        box = self.get_content_area()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.add(vbox)

        box = Gtk.Box(spacing=6)
        vbox.pack_start(box, False, False, 0)
        box.pack_start(Gtk.Label(_("Poster width:"), xalign=0), True, True, 0)
        self.spn_outw = Gtk.SpinButton()
        self.spn_outw.set_adjustment(Gtk.Adjustment(0, 1, 100000, 1, 100, 0))
        self.spn_outw.set_value(opts.out_w)
        self.spn_outw.set_numeric(True)
        self.spn_outw.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID)
        self.spn_outw.connect("changed", self.update_height)
        box.pack_start(self.spn_outw, False, False, 0)
        box.pack_end(Gtk.Label(_("pixels"), xalign=0), False, False, 0)

        box = Gtk.Box(spacing=6)
        vbox.pack_start(box, False, False, 0)
        box.pack_start(Gtk.Label(_("Poster height:"), xalign=0), True, True, 0)
        self.spn_outh = Gtk.SpinButton()
        self.spn_outh.set_adjustment(Gtk.Adjustment(0, 1, 100000, 1, 100, 0))
        self.spn_outh.set_sensitive(False)
        box.pack_start(self.spn_outh, False, False, 0)
        box.pack_end(Gtk.Label(_("pixels"), xalign=0), False, False, 0)

        self.update_height()

        self.show_all()

    def update_height(self, entry=None):
        self.spn_outh.set_value(
            int(round(self.ratio * self.spn_outw.get_value_as_int())))

    def get_poster_width(self):
        return self.spn_outw.get_value_as_int()


class ComputingDialog(Gtk.Dialog):
    """Simple "please wait" dialog, with a "cancel" button."""
    def __init__(self, parent):
        super(ComputingDialog, self).__init__(
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


class PulsingComputingDialog(ComputingDialog):
    def __init__(self, parent):
        super(PulsingComputingDialog, self).__init__(parent)

        self.progressbar.pulse()

        self.timeout_id = GObject.timeout_add(50, self.on_timeout, None)

    def on_timeout(self, user_data):
        self.progressbar.pulse()
        return True  # return True so that it continues to get called


class ErrorDialog(Gtk.Dialog):
    def __init__(self, parent, message):
        super(ErrorDialog, self).__init__(_("Error"), parent, 0,
                                          (Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self.set_border_width(10)
        box = self.get_content_area()
        box.add(Gtk.Label(message))
        self.show_all()


def main():
    # Enable threading. Without that, threads hang!
    GObject.threads_init()

    win = PhotoCollageWindow()
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()

    # If arguments are given, treat them as input images
    if len(sys.argv) > 1:
        win.update_photolist(sys.argv[1:])

    Gtk.main()
