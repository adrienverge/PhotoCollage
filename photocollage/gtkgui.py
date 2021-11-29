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

from data.pickle.utils import store_yearbook
from photocollage import APP_NAME, artwork, collage, render
from photocollage.render import PIL_SUPPORTED_EXTS as EXTS
from photocollage.dialogs.ConfigSelectorDialog import ConfigSelectorDialog
from photocollage.dialogs.SettingsDialog import SettingsDialog

from data.readers.default import corpus_processor
from yearbook.Yearbook import create_yearbook_from_db
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


class UserCollage:
    """Represents a user-defined collage

    A UserCollage contains a list of photos (referenced by filenames) and a
    collage.Page object describing their layout in a final poster.

    """

    def __init__(self, photolist):
        self.photolist = photolist
        self.page = None

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

    def __init__(self):
        super().__init__(title=_("Yearbook Creator"))
        self.yearbook_configurator = Gtk.Button(label=_("Yearbook Settings..."))
        self.yearbook = None
        self.btn_choose_images = Gtk.Button(label=_("Add images..."))
        self.img_preview = ImagePreviewArea(self)
        self.images_flow_box = Gtk.FlowBox()
        self.btn_settings = Gtk.Button()
        self.btn_new_layout = Gtk.Button(label=_("Regenerate"))
        self.btn_redo = Gtk.Button()
        self.lbl_history_index = Gtk.Label(" ")
        self.btn_undo = Gtk.Button()
        self.btn_previous_page = Gtk.Button(label=_("Prev page..."))
        self.lbl_event_name = Gtk.Label(" ")
        self.lbl_page_number = Gtk.Label(" ")
        self.btn_next_page = Gtk.Button(label=_("Next page..."))
        self.btn_publish_book = Gtk.Button(label=_("Publish"))
        self.current_page_index = 0
        self.yearbook_parameters = {'max_count': 12,
                                    'corpus_dir': '/Users/ashah/GoogleDrive/Rilee4thGrade',
                                    'db_file_path': '/Users/ashah/GoogleDrive/Rilee4thGrade/RY.db',
                                    'processed_corpus_file': '/Users/ashah/GoogleDrive/Rilee4thGrade/processedCorpus_rilee_recognizer.out',
                                    'output_dir': '/Users/ashah/Downloads/VargasElementary'}

        self.corpus = corpus_processor(self.yearbook_parameters["processed_corpus_file"])

        # Maybe this gets moved into yearbook-parameters, or we need a reference to the current child
        # since that can be selected from the tree.
        self.child = "Rilee"

        from data.sqllite.reader import get_tree_model
        self.treeView = Gtk.TreeView(get_tree_model(self.yearbook_parameters['db_file_path']))
        self.tv_column = Gtk.TreeViewColumn('Roster')
        self.treeView.append_column(self.tv_column)
        self.treeView.expand_all()

        self.cell = Gtk.CellRendererText()
        self.tv_column.pack_start(self.cell, True)
        self.tv_column.add_attribute(self.cell, 'text', 0)

        class Options:
            def __init__(self):
                self.border_w = 0.02
                self.border_c = "white"
                self.out_w = 2550
                self.out_h = 3300

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

        self.yearbook_configurator.connect("clicked", self.setup_yearbook_config)
        box.pack_start(self.yearbook_configurator, False, False, 0)

        self.btn_choose_images.set_image(Gtk.Image.new_from_stock(
            Gtk.STOCK_OPEN, Gtk.IconSize.LARGE_TOOLBAR))
        self.btn_choose_images.set_always_show_image(True)
        self.btn_choose_images.connect("clicked", self.choose_images)
        box.pack_start(self.btn_choose_images, False, False, 0)

        # -----------------------
        #  Tools pan
        # -----------------------

        box.pack_start(Gtk.SeparatorToolItem(), True, True, 0)

        self.btn_undo.set_image(Gtk.Image.new_from_stock(
            Gtk.STOCK_UNDO, Gtk.IconSize.LARGE_TOOLBAR))
        self.btn_undo.connect("clicked", self.select_prev_layout)
        box.pack_start(self.btn_undo, False, False, 0)
        box.pack_start(self.lbl_history_index, False, False, 0)
        self.btn_redo.set_image(Gtk.Image.new_from_stock(
            Gtk.STOCK_REDO, Gtk.IconSize.LARGE_TOOLBAR))
        self.btn_redo.connect("clicked", self.select_next_layout)
        box.pack_start(self.btn_redo, False, False, 0)
        self.btn_new_layout.set_image(Gtk.Image.new_from_stock(
            Gtk.STOCK_REFRESH, Gtk.IconSize.LARGE_TOOLBAR))
        self.btn_new_layout.set_always_show_image(True)
        self.btn_new_layout.connect("clicked",
                                    self.regenerate_layout)
        box.pack_start(self.btn_new_layout, False, False, 0)

        box.pack_start(Gtk.SeparatorToolItem(), True, True, 0)

        box.pack_start(self.btn_previous_page, False, False, 0)
        self.btn_previous_page.connect("clicked", self.select_prev_page)

        box.pack_start(self.lbl_page_number, False, False, 0)
        box.pack_start(self.lbl_event_name, False, False, 0)
        box.pack_start(self.btn_next_page, True, True, 0)
        self.btn_next_page.connect("clicked", self.select_next_page)

        box.pack_start(self.btn_publish_book, True, True, 0)
        self.btn_publish_book.connect("clicked", self.publish_book)
        box.pack_start(Gtk.SeparatorToolItem(), True, True, 0)

        self.btn_settings.set_image(Gtk.Image.new_from_stock(
            Gtk.STOCK_PREFERENCES, Gtk.IconSize.LARGE_TOOLBAR))
        self.btn_settings.set_always_show_image(True)
        self.btn_settings.connect("clicked", self.set_settings)
        box.pack_end(self.btn_settings, False, False, 0)

        # -------------------
        #  Tree View
        # -------------------
        box = Gtk.Box(spacing=10)
        _scrolledWindow = Gtk.ScrolledWindow()
        _scrolledWindow.add(self.treeView)
        box_window.pack_start(box, True, True, 0)
        box.pack_start(_scrolledWindow, True, True, 0)
        self.treeView.get_selection().connect("changed", self.on_tree_selection_changed)

        # -------------------
        #  Image preview pan
        # -------------------

        # box = Gtk.Box(spacing=10)
        # box_window.pack_start(box, True, True, 0)

        self.img_preview.set_size_request(600, 400)
        self.img_preview.connect("drag-data-received", self.on_drag)
        self.img_preview.drag_dest_set(Gtk.DestDefaults.ALL, [],
                                       Gdk.DragAction.COPY)
        targets = Gtk.TargetList.new([])
        targets.add_text_targets(MainWindow.TARGET_TYPE_TEXT)
        targets.add_uri_targets(MainWindow.TARGET_TYPE_URI)
        self.img_preview.drag_dest_set_target_list(targets)

        box.pack_start(self.img_preview, True, True, 0)

        self.btn_undo.set_sensitive(False)
        self.btn_redo.set_sensitive(False)

        # --------------------------------------------
        #  GTK Flow Box to view other candidate images
        # --------------------------------------------
        box = Gtk.Box(spacing=10)
        _scrolledWindow = Gtk.ScrolledWindow()
        box_window.pack_start(box, True, True, 0)
        self.images_flow_box.set_size_request(600, 200)
        _scrolledWindow.add(self.images_flow_box)
        box.pack_start(_scrolledWindow, True, True, 0)

    def on_tree_selection_changed(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            str_loc = model.get_string_from_iter(treeiter).split(':')[0]
            new_tree_iter = model.get_iter_from_string(str_loc)
            school_name = model[new_tree_iter][0]
            child_name = model[treeiter][0]
            print("You belong to: ", school_name)
            print("You are: ", model[treeiter][0])

            print("Check for pickle file")
            pickle_path = os.path.join(self.yearbook_parameters["output_dir"], ".pickle", school_name, child_name + ".pickle")
            if os.path.exists(pickle_path):
                print("Pickle file exists and we can load the yearbook from there")
                from yearbook.Yearbook import create_yearbook_from_pickle
                self.yearbook = create_yearbook_from_pickle(pickle_path)
                print("Successfully loaded a yearbook from pickle file")

            # Once we know the school name, we should be able to retrieve the album details
            # TODO:: This check needs to incorporate whether the yearbook belongs to the selection.
            # For the time being we're going to deal with only 1 yearbook
            if self.yearbook is None:
                yearbook = create_yearbook_from_db(self.yearbook_parameters["db_file_path"], school_name)
                for current_page in yearbook.pages:

                    # TODO: Add intelligence here since we should be able to refine the images to pick
                    # based on page information
                    all_page_images = self.choose_page_images_for_child(current_page, child_name, max_count=100)

                    # Need to use a small set of these images to create the initial collage
                    self.update_photolist(current_page, all_page_images[:12], display=True)
                    print("Finished updating the photo list for page, %s", current_page.event_name)

                # Let's update the yearbook on selection to display
                self.yearbook = yearbook

                # TODO:: Remove this save, for testing, let's save the pickle file here and try to load on next startup
                store_yearbook(self.yearbook, pickle_path)
                print("Saved yearbook here: ", pickle_path)

            # Reset page to first
            _current_page = self.select_page_at_index(index=0)
            if _current_page.history:
                self.render_preview(_current_page)
            # Update the tool buttons
            self.update_tool_buttons()
            self.update_page_buttons()

    def update_flow_box_with_images(self, page: Page):
        corpus_dir = self.yearbook_parameters["corpus_dir"]
        if not page.personalized:
            print("Load image as is, %s, %s" % (page.event_name, page.image))
            event_images = [page.image]
        else:
            event_images = self.corpus.get_filenames_for_event_images(page.event_name, corpus_dir)

        # scrolled = Gtk.ScrolledWindow()
        # scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        flowbox = self.images_flow_box
        flowbox.set_valign(Gtk.Align.START)
        flowbox.set_max_children_per_line(10)
        flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)

        # Need to remove all previously added images
        [flowbox.remove(child) for child in flowbox.get_children()]

        for img in event_images:

            # Lets not add the image to the viewer if it's on the page.
            if img in [photo.filename for photo in page.photo_list]:
                print("Skip displaying this image...")
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

        # scrolled.add(flowbox)
        # self.add(scrolled)
        self.show_all()

    def invoke_add_image(self, widget, event, img_name):
        print("clicked image ")
        print(widget)
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            print("double click, %s", img_name)
            self.update_photolist(self.yearbook.pages[self.current_page_index], [img_name])
            self.update_flow_box_with_images(self.yearbook.pages[self.current_page_index])
        else:
            print("single click")

    def update_photolist(self, page, new_images, display: bool = True):
        photolist = []
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

        self.current_page_index = index
        self.select_next_page(self.btn_next_page)

        return self.yearbook.pages[index]

    def setup_yearbook_config(self, button):
        dialog = ConfigSelectorDialog(self)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.yearbook_parameters = dialog.config_parameters
            self.corpus = corpus_processor(self.yearbook_parameters["processed_corpus_file"])

            # Read the config file
            # TODO:: This school name needs to come from a combo box on the UI once the database file is provided
            self.yearbook = create_yearbook_from_db(self.yearbook_parameters["config_file"], "Rilee4thGrade", "")
            # Reset page to first
            _current_page = self.select_page_at_index(index=0)

            dialog.destroy()
            if _current_page.history:
                self.render_preview(_current_page)
        else:
            dialog.destroy()

    def choose_page_images_for_child(self, page, child, max_count=12):
        corpus_dir = self.yearbook_parameters["corpus_dir"]

        if not page.personalized:
            print("Load image as is, %s, %s" % (page.event_name, page.image))
            images = [page.image]
        else:
            print("Working on: (%s, %s, %s)" % (page.image, page.event_name, page.number))
            images = self.corpus.get_filenames_child_images_for_event(child, page.event_name, corpus_dir)

        return images[:max_count]

    def choose_images(self, button):
        dialog = PreviewFileChooserDialog(title=_("Choose images"),
                                          parent=button.get_toplevel(),
                                          action=Gtk.FileChooserAction.OPEN,
                                          select_multiple=True,
                                          modal=True)

        if dialog.run() == Gtk.ResponseType.OK:
            files = dialog.get_filenames()
            dialog.destroy()
            self.update_photolist(self.yearbook.pages[self.current_page_index], files)
            self.update_flow_box_with_images(self.yearbook.pages[self.current_page_index])
        else:
            dialog.destroy()

    def on_drag(self, widget, drag_context, x, y, data, info, time):
        if info == MainWindow.TARGET_TYPE_TEXT:
            files = data.get_text().splitlines()
        elif info == MainWindow.TARGET_TYPE_URI:
            # Can only handle local URIs
            files = [f for f in data.get_uris() if f.startswith("file://")]

        for i in range(len(files)):
            if files[i].startswith("file://"):
                files[i] = urllib.parse.unquote(files[i][7:])
        self.update_photolist(self.yearbook.pages[self.current_page_index], files)
        self.update_flow_box_with_images(self.yearbook.pages[self.current_page_index])

    def render_preview(self, yearbook_page: Page):
        try:
            page_collage: UserCollage = yearbook_page.history[yearbook_page.history_index]
        except IndexError:
            page_images = self.choose_page_images_for_child(yearbook_page, self.child)
            self.update_photolist(yearbook_page, page_images)
            self.update_flow_box_with_images(yearbook_page)

        # If the desired ratio changed in the meantime (e.g. from landscape to
        # portrait), it needs to be re-updated
        page_collage.page.target_ratio = 1.0 * self.opts.out_h / self.opts.out_w
        page_collage.page.adjust_cols_heights()

        w = self.img_preview.get_allocation().width
        h = self.img_preview.get_allocation().height
        page_collage.page.scale_to_fit(w, h)

        # Display a "please wait" dialog and do the job.
        comp_dialog = ComputingDialog(self)

        def on_update(img, fraction_complete):
            self.img_preview.set_collage(img, page_collage)
            comp_dialog.update(fraction_complete)

        def on_complete(img, out_file):
            self.img_preview.set_collage(img, page_collage)
            comp_dialog.destroy()

        def on_fail(exception):
            dialog = ErrorDialog(self, "{}:\n\n{}".format(
                _("An error occurred while rendering image:"), exception))
            comp_dialog.destroy()
            dialog.run()
            dialog.destroy()

        out_file = os.path.join(self.yearbook_parameters['output_dir'], str(yearbook_page.number) + ".jpg")

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

    def render_from_new_collage(self, page, _collage):
        page.history.append(_collage)
        page.history_index = len(page.history) - 1
        self.update_tool_buttons()
        self.render_preview(page)

    def regenerate_layout(self, button):
        page = self.yearbook.pages[self.current_page_index]
        new_collage = page.history[page.history_index].duplicate()
        new_collage.make_page(self.opts)
        self.render_from_new_collage(page, new_collage)

    def select_prev_layout(self, button, page):
        page.history_index -= 1
        self.update_tool_buttons()
        self.render_preview(page)

    def select_next_layout(self, button, page):
        page.history_index += 1
        self.update_tool_buttons()
        self.render_preview(page)

    def publish_book(self, button):
        from PIL import Image
        print("Publishing....")
        output_dir = self.yearbook_parameters['output_dir']

        # if we can't retrieve it from the object, lets try to get it from the directory
        pil_images = [Image.open(os.path.join(output_dir, str(page.number) + ".jpg")) for page in self.yearbook.pages]
        print("Will look for images starting with ", pil_images[0])
        pdf_path = os.path.join(output_dir, self.child + "_version0.pdf")
        pil_images[0].save(pdf_path, save_all=True,
                           append_images=pil_images[1:])
        print("Finished creating PDF version... ", pdf_path)

    def publish_book_old(self, button):
        output_dir = self.yearbook_parameters['output_dir']

        all_pages = []
        # Display a "please wait" dialog and do the job.
        comp_dialog = ComputingDialog(self)
        count_completed = 0

        def on_update(img, fraction_complete):
            comp_dialog.update(fraction_complete)

        def on_complete(img, out_file_name):
            comp_dialog.update(0)
            print("Finished creating img %s", out_file_name)
            all_pages.append(out_file_name)
            if len(all_pages) == len(self.yearbook.pages):
                print("Time to destroy this dialog, and save the final file")
                all_final_images = [page.final_img for page in self.yearbook.pages]
                all_final_images[0].save(os.path.join(output_dir, self.child + "_version0.pdf"), save_all=True,
                                         append_images=all_final_images[1:])
                comp_dialog.destroy()

                return

        print("Will create a yearbook with page count: ", str(len(self.yearbook.pages)))
        for yearbook_page in self.yearbook.pages:
            out_file = os.path.join(self.yearbook_parameters['output_dir'], str(yearbook_page.number) + ".jpg")
            page_collage = yearbook_page.history[yearbook_page.history_index]
            enlargement = float(self.opts.out_w) / page_collage.page.w
            page_collage.page.scale(enlargement)

            t = render.RenderingTask(
                yearbook_page,
                page_collage.page,
                output_file=out_file,
                border_width=self.opts.border_w * max(page_collage.page.w,
                                                      page_collage.page.h),
                border_color=self.opts.border_c,
                on_update=gtk_run_in_main_thread(on_update),
                on_complete=gtk_run_in_main_thread(on_complete),
                on_fail=None)

            t.start()

        # Lets read the page images again and write it to a pdf
        # final_pages = []
        # for yearbook_page in self.yearbook.pages:
        #    final_pages.append(yearbook_page.final_img)

        # now let's write this thing to a PDF file
        print("Finished creating the final PDF file...")
        # final_pages[0].save(os.path.join(output_dir, self.child + "_version0.pdf"), save_all=True,
        #                    append_images=final_pages[1:])

    def select_next_page(self, button):
        old_page: Page = self.yearbook.pages[self.current_page_index]
        used_images = [photo.filename for photo in old_page.history[old_page.history_index].photolist]

        self.current_page_index += 1
        self.update_page_buttons()
        current_page = self.yearbook.pages[self.current_page_index]
        if not current_page.history:
            max_count = self.yearbook_parameters['max_count']
            new_page_images = self.choose_page_images_for_child(current_page, self.child)
            remaining_images = [x for x in new_page_images if x not in used_images][:max_count]
            self.update_photolist(current_page, remaining_images)

        self.render_preview(current_page)
        self.update_flow_box_with_images(current_page)

    def select_prev_page(self, button):
        self.current_page_index -= 1
        self.update_page_buttons()
        current_page = self.yearbook.pages[self.current_page_index]
        self.render_preview(current_page)
        self.update_flow_box_with_images(current_page)

    def set_settings(self, button):
        dialog = SettingsDialog(self)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            dialog.apply_opts(self.opts)
            dialog.destroy()

            if self.yearbook:
                page = self.yearbook.pages[self.current_page_index]
                if page.history:
                    self.render_preview(page)
        else:
            dialog.destroy()

    def update_page_buttons(self):
        self.btn_previous_page.set_sensitive(self.current_page_index > 0)
        self.btn_next_page.set_sensitive(self.current_page_index < len(self.yearbook.pages) - 1)

        if self.current_page_index < 0:
            self.lbl_event_name.set_label("")
            self.lbl_page_number.set_label("")
        else:
            self.lbl_event_name.set_label(self.yearbook.pages[self.current_page_index].event_name)
            self.lbl_page_number.set_label(str(self.yearbook.pages[self.current_page_index].number))

    def update_tool_buttons(self):
        if self.yearbook is None:
            return

        page = self.yearbook.pages[self.current_page_index]
        self.btn_undo.set_sensitive(page.history_index > 0)
        self.btn_redo.set_sensitive(page.history_index < len(page.history) - 1)
        if page.history_index < len(page.history):
            self.lbl_history_index.set_label(str(page.history_index + 1))
        else:
            self.lbl_history_index.set_label(" ")
        self.btn_new_layout.set_sensitive(
            page.history_index < len(page.history))


class ImagePreviewArea(Gtk.DrawingArea):
    """Area to display the poster preview and react to user actions"""
    INSENSITIVE, FLYING, SWAPPING_OR_MOVING = range(3)

    def __init__(self, parent):
        super().__init__()
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

    def draw(self, widget, context):
        if self.image is not None:
            x0, y0 = self.get_image_offset()
            context.set_source_surface(self.image, x0, y0)
            context.paint()

            if self.mode == self.FLYING:
                cell = self.collage.page.get_cell_at_position(self.x, self.y)
                if cell:
                    self.paint_image_border(context, cell)
                    self.paint_image_delete_button(context, cell)
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
        if self.parent.yearbook is None:
            return

        current_page = self.parent.yearbook.pages[self.parent.current_page_index]
        if self.mode == self.FLYING:
            x, y = self.get_pos_in_image(event.x, event.y)
            cell = self.collage.page.get_cell_at_position(x, y)
            if not cell:
                return
            # Has the user clicked the delete button?
            dist = (cell.x + cell.w - 12 - x) ** 2 + (cell.y + 12 - y) ** 2
            if dist <= 8 * 8:
                self.collage.photolist.remove(cell.photo)
                if self.collage.photolist:
                    self.collage.make_page(self.parent.opts)
                    self.parent.render_from_new_collage(current_page, self.collage)
                else:
                    self.image = None
                    self.mode = self.INSENSITIVE
                    current_page.history_index = len(current_page.history)
                    self.parent.update_tool_buttons()
            # Otherwise, the user wants to swap this image with another
            else:
                self.swap_origin.x, self.swap_origin.y = x, y
                self.swap_origin.cell = cell
                self.mode = self.SWAPPING_OR_MOVING
        widget.queue_draw()

    def button_release_event(self, widget, event):
        if self.parent.yearbook is None:
            return

        current_page = self.parent.yearbook.pages[self.parent.current_page_index]
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

    Gtk.main()
