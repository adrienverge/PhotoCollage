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
import gettext
from gi.repository import Gtk, Gdk, GObject
from io import BytesIO
import math
import os.path

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
        self.photolist = []
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
        Gtk.Window.__init__(self, title=_("PhotoCollage"))

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

        self.img_preview = ImagePreviewArea()
        self.img_preview.set_size_request(600, 400)
        box.pack_start(self.img_preview, True, True, 0)

        self.btn_save.set_sensitive(False)

        self.btn_undo.set_sensitive(False)
        self.btn_redo.set_sensitive(False)
        self.btn_new_layout.set_sensitive(False)
        self.btn_less_cols.set_sensitive(False)
        self.btn_more_cols.set_sensitive(False)

    def choose_images(self, button):
        dialog = Gtk.FileChooserDialog(_("Choose images"),
                                       button.get_toplevel(),
                                       Gtk.FileChooserAction.OPEN,
                                       select_multiple=True)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)

        set_open_image_filters(dialog)

        if dialog.run() == Gtk.ResponseType.OK:
            self.photolist = render.build_photolist(dialog.get_filenames())
            dialog.destroy()

            n = len(self.photolist)
            # self.lbl_images.set_text(str(n))
            if n > 0:
                self.lbl_images.set_text(
                    _n("%(num)d image loaded", "%(num)d images loaded", n)
                    % {"num": n})
            else:
                self.lbl_images.set_text(_("no image loaded"))

            if n > 0:
                self.opts.no_cols = int(round(
                    1.5 * math.sqrt(len(self.photolist))))

                self.regenerate_layout()
        else:
            dialog.destroy()

    def render_preview(self):
        page = self.layout_histo[self.current_layout]

        w = self.img_preview.get_allocation().width
        h = self.img_preview.get_allocation().height
        page.scale_to_fit(w, h)

        # Display a "please wait" dialog and do the job.
        compdialog = ComputingDialog(self)

        def on_update(ret):
            self.img_preview.image = pil_image_to_cairo_surface(ret)

        def on_complete(ret):
            self.img_preview.image = pil_image_to_cairo_surface(ret)
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

    def regenerate_layout(self, button=None):
        page = collage.Page(1.0, self.opts.no_cols)
        for photo in self.photolist:
            page.add_cell(photo)
        page.adjust()

        self.layout_histo.append(page)
        self.current_layout = len(self.layout_histo) - 1
        self.update_tool_buttons()
        self.render_preview()

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
        compdialog = ComputingDialog(self)

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
        self.lbl_current_layout.set_label(str(self.current_layout + 1))
        self.btn_new_layout.set_sensitive(True)
        self.btn_less_cols.set_sensitive(self.opts.no_cols > 1)
        self.btn_more_cols.set_sensitive(True)


class ImagePreviewArea(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()

        parse, color = Gdk.Color.parse("#888888")
        self.modify_bg(Gtk.StateType.NORMAL, color)

        self.image = None

        self.connect("draw", self.draw)

    def draw(self, widget, context):
        if self.image is not None:
            w0, h0 = self.get_allocation().width, self.get_allocation().height
            w1, h1 = self.image.get_width(), self.image.get_height()
            context.set_source_surface(self.image,
                                       round((w0 - w1) / 2.0),
                                       round((h0 - h1) / 2.0))
            context.paint()


class BorderOptionsDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, _("Border options"), parent, 0,
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
        Gtk.Dialog.__init__(self, _("Save image"), parent, 0,
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
        Gtk.Dialog.__init__(self, _("Please wait"), parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        self.set_default_size(300, -1)
        self.set_border_width(10)

        box = self.get_content_area()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.add(vbox)

        label = Gtk.Label(_("Performing image computation..."))
        vbox.pack_start(label, True, True, 0)

        self.progressbar = Gtk.ProgressBar()
        self.progressbar.pulse()
        vbox.pack_start(self.progressbar, True, True, 0)

        self.show_all()

        self.timeout_id = GObject.timeout_add(50, self.on_timeout, None)

    def on_timeout(self, user_data):
        self.progressbar.pulse()

        # Return True so that it continues to get called
        return True


class ErrorDialog(Gtk.Dialog):
    def __init__(self, parent, message):
        super().__init__(_("Error"), parent, 0,
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
    Gtk.main()
