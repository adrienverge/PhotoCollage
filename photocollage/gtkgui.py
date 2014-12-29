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

import gettext
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject
from io import BytesIO
import math
import os.path

from photocollage import APP_NAME, collage, render
from photocollage.render import PIL_SUPPORTED_EXTS as EXTS


gettext.textdomain(APP_NAME)
_ = gettext.gettext
_n = gettext.ngettext
# xgettext --keyword=_n:1,2 -o photocollage.pot `find . -name '*.py'`
# cp photocollage.pot locale/fr/LC_MESSAGES/photocollage.po
# msgfmt -o locale/fr/LC_MESSAGES/photocollage.mo \
#        locale/fr/LC_MESSAGES/photocollage.po


def pil_img_to_raw(src_img):
    # Save image to a temporary buffer
    buf = BytesIO()
    src_img.save(buf, "ppm")
    contents = buf.getvalue()
    buf.close()
    return contents


def gtk_img_from_raw(dest_img, contents):
    # Fill pixbuf from this buffer
    l = GdkPixbuf.PixbufLoader.new_with_type("pnm")
    l.write(contents)
    l.close()
    dest_img.set_from_pixbuf(l.get_pixbuf())


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

        class Options:
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

        # TODO: Open a dialog to ask the output image resolution
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
        self.btn_less_cols.set_image(Gtk.Image.new_from_stock(
            Gtk.STOCK_GOTO_BOTTOM, Gtk.IconSize.LARGE_TOOLBAR))
        self.btn_less_cols.connect("clicked", self.less_cols)
        box.pack_start(self.btn_less_cols, False, False, 0)
        self.btn_more_cols = Gtk.Button()
        self.btn_more_cols.set_image(Gtk.Image.new_from_stock(
            Gtk.STOCK_GOTO_LAST, Gtk.IconSize.LARGE_TOOLBAR))
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

        self.img_preview = Gtk.Image()
        parse, color = Gdk.Color.parse("#888888")
        self.img_preview.modify_bg(Gtk.StateType.NORMAL, color)
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
            gtk_img_from_raw(self.img_preview, pil_img_to_raw(ret))

        def on_finish(ret):
            gtk_img_from_raw(self.img_preview, pil_img_to_raw(ret))
            compdialog.destroy()
            self.btn_save.set_sensitive(True)

        def on_fail(ret):
            dialog = ErrorDialog(
                self, _("An error occurred while rendering image."))
            compdialog.destroy()
            dialog.run()
            dialog.destroy()
            self.btn_save.set_sensitive(False)

        t = render.RenderingTask(page,
                                 border_width=self.opts.border_w * page.w,
                                 border_color=self.opts.border_c,
                                 interactive=True,
                                 on_update=gtk_run_in_main_thread(on_update),
                                 on_finish=gtk_run_in_main_thread(on_finish),
                                 on_fail=gtk_run_in_main_thread(on_fail))
        t.start()

        response = compdialog.run()
        if response == Gtk.ResponseType.CANCEL:
            t.abort()

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

        enlargement = self.opts.out_w / page.w
        page.scale(enlargement)

        dialog = Gtk.FileChooserDialog(_("Save file"), button.get_toplevel(),
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

        def on_finish(ret):
            compdialog.destroy()

        def on_fail(ret):
            dialog = ErrorDialog(
                self, _("An error occurred while rendering image."))
            compdialog.destroy()
            dialog.run()
            dialog.destroy()

        t = render.RenderingTask(page,
                                 border_width=self.opts.border_w * page.w,
                                 border_color=self.opts.border_c,
                                 output_file=savefile,
                                 on_finish=gtk_run_in_main_thread(on_finish),
                                 on_fail=gtk_run_in_main_thread(on_fail))
        t.start()

        response = compdialog.run()
        if response == Gtk.ResponseType.CANCEL:
            t.abort()

    def update_tool_buttons(self):
        self.btn_undo.set_sensitive(self.current_layout > 0)
        self.btn_redo.set_sensitive(
            self.current_layout < len(self.layout_histo) - 1)
        self.lbl_current_layout.set_label(str(self.current_layout + 1))
        self.btn_new_layout.set_sensitive(True)
        self.btn_less_cols.set_sensitive(self.opts.no_cols > 1)
        self.btn_more_cols.set_sensitive(True)


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

        self.spn_border = Gtk.Entry(text=str(100.0 * parent.opts.border_w))
        box.pack_start(self.spn_border, False, False, 0)

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

        box = Gtk.Box(spacing=6)
        vbox.pack_start(box, False, False, 0)

        label = Gtk.Label(_("Poster width (in pixels):"), xalign=0)
        box.pack_start(label, True, True, 0)

        self.spn_outw = Gtk.SpinButton()
        self.spn_outw.set_adjustment(Gtk.Adjustment(parent.opts.out_w,
                                                    1, 100000, 1, 100, 0))
        self.spn_outw.set_numeric(True)
        self.spn_outw.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID)
        box.pack_start(self.spn_outw, False, False, 0)

        self.show_all()

    def apply_opts(self, opts):
        try:
            opts.border_w = float(self.spn_border.get_text()) / 100.0
        except ValueError:
            pass
        iter = self.cmb_bordercolor.get_active_iter()
        opts.border_c = self.cmb_bordercolor.get_model()[iter][1]
        opts.out_w = self.spn_outw.get_value_as_int()


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
