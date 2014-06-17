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
from multiprocessing import Process, Pipe
import os.path
import PIL.Image
from threading import Thread

from .generator import *
from .version import APP_NAME, APP_VERSION

__author__ = "Adrien Vergé"
__copyright__ = "Copyright 2013, Adrien Vergé"
__license__ = "GPLv2+"
__version__ = APP_VERSION

if os.path.isdir("locale"):
	gettext.install(APP_NAME, "locale", names=["ngettext"])
else:
	gettext.install(APP_NAME, names=["ngettext"])
_n = ngettext
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
	dest_img.set_from_pixbuf(l.get_pixbuf())
	l.close()

def get_all_save_image_exts():
	all_types = dict(list(PIL_SUPPORTED_EXTS_RW.items()) + \
					 list(PIL_SUPPORTED_EXTS_WO.items()))
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

	all_types = dict(list(PIL_SUPPORTED_EXTS_RW.items()) + \
					 list(PIL_SUPPORTED_EXTS_RO.items()))
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
	all_types = dict(list(PIL_SUPPORTED_EXTS_RW.items()) + \
					 list(PIL_SUPPORTED_EXTS_WO.items()))
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

class PhotoCollageWindow(Gtk.Window):

	def __init__(self):
		self.photolist = []
		self.skel_histo = []
		self.current_skel = -1

		class Options:
			def __init__(self):
				self.no_cols = 1
				self.border_w = 2
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
		#  Input and options pan
		# -----------------------

		box = Gtk.Box(spacing=6, orientation=Gtk.Orientation.HORIZONTAL)
		box_window.pack_start(box, False, False, 0)

		self.btn_choose_images = Gtk.Button(label=_("Choose input images..."))
		self.btn_choose_images.connect("clicked", self.choose_images)
		box.pack_start(self.btn_choose_images, False, False, 0)

		self.lbl_images = Gtk.Label(_("no image loaded"), xalign=0.1)
		box.pack_start(self.lbl_images, True, True, 0)

		self.btn_opts = Gtk.Button(label=_("Options..."))
		self.btn_opts.connect("clicked", self.set_options)
		box.pack_start(self.btn_opts, False, False, 0)

		# -----------------------
		#  Computing buttons pan
		# -----------------------

		box = Gtk.Box(spacing=6)
		box_window.pack_start(box, False, False, 0)

		self.btn_skeleton = Gtk.Button(label=_("Generate a new layout"))
		self.btn_skeleton.connect("clicked", self.make_skeleton)
		box.pack_start(self.btn_skeleton, True, True, 0)

		self.btn_preview = Gtk.Button(label=_("Preview poster"))
		self.btn_preview.connect("clicked", self.make_preview)
		box.pack_start(self.btn_preview, True, True, 0)

		# TODO: Open a dialog to ask the output image resolution
		self.btn_save = Gtk.Button(label=_("Save full-resolution poster..."))
		self.btn_save.connect("clicked", self.save_poster)
		box.pack_end(self.btn_save, True, True, 0)

		# -------------
		#  History pan
		# -------------
		box = Gtk.Box(spacing=6)
		box_window.pack_start(box, False, False, 0)

		self.btn_prev_skel = Gtk.Button(label=_("<"))
		self.btn_prev_skel.connect("clicked", self.show_prev_skel)
		box.pack_start(self.btn_prev_skel, False, False, 0)

		self.lbl_histo = Gtk.Label(_("no history"), xalign=0.1)
		box.pack_start(self.lbl_histo, False, False, 0)

		self.btn_next_skel = Gtk.Button(label=_(">"))
		self.btn_next_skel.connect("clicked", self.show_next_skel)
		box.pack_start(self.btn_next_skel, False, False, 0)

		self.btn_clear_histo = Gtk.Button(label=_("Clear history"))
		self.btn_clear_histo.connect("clicked", self.clear_skel_histo)
		box.pack_end(self.btn_clear_histo, False, False, 0)

		# -------------------
		#  Image preview pan
		# -------------------

		box = Gtk.Box(spacing=10)
		box_window.pack_start(box, True, True, 0)

		self.img_skeleton = Gtk.Image()
		parse, color = Gdk.Color.parse("#888888")
		self.img_skeleton.modify_bg(Gtk.StateType.NORMAL, color)
		self.img_skeleton.set_size_request(300, 300)
		box.pack_start(self.img_skeleton, True, True, 0)

		self.img_preview = Gtk.Image()
		parse, color = Gdk.Color.parse("#888888")
		self.img_preview.modify_bg(Gtk.StateType.NORMAL, color)
		self.img_preview.set_size_request(300, 300)
		box.pack_start(self.img_preview, True, True, 0)

		self.btn_skeleton.set_sensitive(False)
		self.btn_preview.set_sensitive(False)
		self.btn_save.set_sensitive(False)
		self.btn_prev_skel.set_sensitive(False)
		self.btn_next_skel.set_sensitive(False)
		self.btn_clear_histo.set_sensitive(False)

	def choose_images(self, button):
		dialog = Gtk.FileChooserDialog(_("Choose images"), button.get_toplevel(),
									   Gtk.FileChooserAction.OPEN,
									   select_multiple=True)
		dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
		dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)

		set_open_image_filters(dialog)

		if dialog.run() == Gtk.ResponseType.OK:
			self.photolist = build_photolist(dialog.get_filenames())
			n = len(self.photolist)
			if n > 0:
				self.lbl_images.set_text(
					_n("%(num)d image loaded", "%(num)d images loaded", n)
					% {"num": n})
			else:
				self.lbl_images.set_text(_("no image loaded"))

			self.btn_skeleton.set_sensitive(False)
			self.btn_preview.set_sensitive(False)
			self.btn_save.set_sensitive(False)
			if n > 0:
				self.opts.no_cols = int(round(math.sqrt(len(self.photolist))))

				self.make_skeleton(button)
				self.btn_skeleton.set_sensitive(True)

		dialog.destroy()

	def set_options(self, button):
		dialog = OptionsDialog(self)
		response = dialog.run()

		if response == Gtk.ResponseType.OK:
			dialog.apply_opts(self.opts)

		dialog.destroy()

	def make_skeleton(self, button):
		page = Page(self.photolist, 1.0, self.opts.no_cols)
		page.fill()
		page.eat_space()
		page.eat_space2()

		self.skel_histo.append(page)
		self.current_skel = len(self.skel_histo) - 1

		self.show_skeleton(page)

		self.update_histo_pan()
		self.btn_preview.set_sensitive(True)
		self.btn_save.set_sensitive(True)

	def show_skeleton(self, page):
		w = self.img_skeleton.get_allocation().width
		h = self.img_skeleton.get_allocation().height
		enlargement = page.scale_to_fit(w, h)

		opts = PrintOptions(enlargement, PrintOptions.RENDER_SKELETON,
							PrintOptions.QUALITY_FAST)
		img = page.render(opts)

		gtk_img_from_raw(self.img_skeleton, pil_img_to_raw(img))


	def make_preview(self, button):
		w = self.img_preview.get_allocation().width
		h = self.img_preview.get_allocation().height
		page = self.skel_histo[self.current_skel]
		enlargement = page.scale_to_fit(w, h)

		opts = PrintOptions(enlargement, PrintOptions.RENDER_REAL,
							PrintOptions.QUALITY_FAST)
		opts.set_border(self.opts.border_w, self.opts.border_c)

		# Display a "please wait" dialog and do the job.

		compdialog = ComputingDialog(self)

		def big_job():
			img = page.render(opts)
			return pil_img_to_raw(img)

		def on_finish(ret):
			if ret != None:
				gtk_img_from_raw(self.img_preview, ret)
			compdialog.destroy()

		t = WorkingThread(big_job, on_finish)
		t.start()

		response = compdialog.run()
		if response == Gtk.ResponseType.CANCEL:
			t.stop_process()

	def save_poster(self, button):
		dialog = Gtk.FileChooserDialog(_("Save file"), button.get_toplevel(),
									   Gtk.FileChooserAction.SAVE)
		dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
		dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
		dialog.set_do_overwrite_confirmation(True)

		set_save_image_filters(dialog)

		savefile = None

		page = self.skel_histo[self.current_skel]
		if dialog.run() == Gtk.ResponseType.OK:
			enlargement = self.opts.out_w / page.get_width()

			opts = PrintOptions(enlargement, PrintOptions.RENDER_REAL,
								PrintOptions.QUALITY_BEST)
			opts.set_border(self.opts.border_w, self.opts.border_c)

			savefile = dialog.get_filename()
			base, ext = os.path.splitext(savefile)
			if ext == "" or not ext[1:].lower() in get_all_save_image_exts():
				savefile += ".jpg"

		dialog.destroy()

		if not savefile:
			return

		# Display a "please wait" dialog and do the job.

		compdialog = ComputingDialog(self)

		def big_job():
			img = page.render(opts)
			img.save(savefile)

		def on_finish(ret):
			compdialog.destroy()

		t = WorkingThread(big_job, on_finish)
		t.start()

		response = compdialog.run()
		if response == Gtk.ResponseType.CANCEL:
			t.stop_process()

	def show_prev_skel(self, button):
		if self.current_skel > 0:
			self.current_skel -= 1
			self.show_skeleton(self.skel_histo[self.current_skel])
			self.update_lbl_images()
			self.update_histo_pan()

	def show_next_skel(self, button):
		if self.current_skel < len(self.skel_histo) - 1:
			self.current_skel += 1
			self.show_skeleton(self.skel_histo[self.current_skel])
			self.update_lbl_images()
			self.update_histo_pan()

	def clear_skel_histo(self, button):
		# keep current skeleton
		self.skel_histo = [self.skel_histo[self.current_skel]]
		self.current_skel = 0
		self.show_skeleton(self.skel_histo[self.current_skel])
		self.update_histo_pan()

	def update_lbl_images(self):
		n = len(self.skel_histo[self.current_skel].photo_list)
		self.lbl_images.set_text(
			_n("%(num)d image loaded", "%(num)d images loaded", n)
			% {"num": n})

	def update_histo_pan(self):
		if len(self.skel_histo) == 0:
			self.lbl_histo.set_label(_("no history"))
			self.btn_prev_skel.set_sensitive(False)
			self.btn_next_skel.set_sensitive(False)
			self.btn_clear_histo.set_sensitive(False)
		else:
			self.lbl_histo.set_label(_("{0} of {1}").format(
				self.current_skel + 1,
				len(self.skel_histo)))
			self.btn_prev_skel.set_sensitive(self.current_skel > 0)
			self.btn_next_skel.set_sensitive(self.current_skel < len(self.skel_histo) - 1)
			self.btn_clear_histo.set_sensitive(len(self.skel_histo) > 1)

class OptionsDialog(Gtk.Dialog):

	def __init__(self, parent):
		Gtk.Dialog.__init__(self, _("Options"), parent, 0,
							(Gtk.STOCK_OK, Gtk.ResponseType.OK,
							 Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

		self.set_border_width(10)

		box = self.get_content_area()
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
		box.add(vbox)

		box = Gtk.Box(spacing=6)
		vbox.pack_start(box, False, False, 0)

		label = Gtk.Label(_("Number of columns:"), xalign=0)
		box.pack_start(label, True, True, 0)

		self.spn_nocols = Gtk.SpinButton()
		self.spn_nocols.set_adjustment(Gtk.Adjustment(parent.opts.no_cols,
													  1, 100, 1, 10, 0))
		self.spn_nocols.set_numeric(True)
		self.spn_nocols.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID)
		box.pack_start(self.spn_nocols, False, False, 0)

		box = Gtk.Box(spacing=6)
		vbox.pack_start(box, False, False, 0)

		label = Gtk.Label(_("Border width (in percent):"), xalign=0)
		box.pack_start(label, True, True, 0)

		self.spn_border = Gtk.SpinButton()
		self.spn_border.set_adjustment(Gtk.Adjustment(parent.opts.border_w,
													  0, 100, 1, 10, 0))
		self.spn_border.set_numeric(True)
		self.spn_border.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID)
		box.pack_start(self.spn_border, False, False, 0)

		box = Gtk.Box(spacing=6)
		vbox.pack_start(box, False, False, 0)

		label = Gtk.Label(_("Border color:"), xalign=0)
		box.pack_start(label, True, True, 0)

		colors = (
			(0, "black", _("black")),
			(1, "white", _("white"))
		)
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
		opts.no_cols = self.spn_nocols.get_value_as_int()
		opts.border_w = self.spn_border.get_value_as_int()
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

class WorkingThread(Thread):
	"""WorkingThread and WorkingProcess provide the ability to defer a heavy
	task to another process, while keeping the GUI responsive.  Because of the
	GIL, threads in python aren't really threads, so we need to spawn a new
	process.  Besides, creating a new process make it possible to stop an
	already began calculation by killing the process.

	Launching an asynchronous task is done by creating a WorkingThread with two
	arguments.  The first one is the heavy function, that will be executed in
	another process, and that should return its output.  The second function
	will be executed when the first one terminates, and should take the first
	one's return value as input.

	"""
	def __init__(self, func, func_done):
		Thread.__init__(self)

		self.func = func
		self.func_done = func_done

		self.rd_conn, self.wr_conn = Pipe(False)
		self.valid_output = True
		self.p = WorkingProcess(self.func, self.rd_conn, self.wr_conn)

	def run(self):
		self.p.start()
		self.wr_conn.close()

		try:
			func_ret = self.rd_conn.recv()
			if not self.valid_output:
				# In case the process was terminated abruptly
				func_ret = None
		except EOFError:
			# In case the process was terminated abruptly
			func_ret = None
		finally:
			GObject.idle_add(self.func_done, func_ret)

		self.rd_conn.close()

	def stop_process(self):
		self.valid_output = False
		self.p.terminate()

class WorkingProcess(Process):
	"""WorkingProcess just executes the function it is given, after closing the
	unused pipe ends.

	"""
	def __init__(self, func, rd_conn, wr_conn):
		Process.__init__(self)

		self.func = func
		self.rd_conn = rd_conn
		self.wr_conn = wr_conn

	def run(self):
		self.rd_conn.close()
		self.wr_conn.send(self.func())
		self.wr_conn.close()

def main():
	# Enable threading. Without that, threads hang!
	GObject.threads_init()

	win = PhotoCollageWindow()
	win.connect("delete-event", Gtk.main_quit)
	win.show_all()
	Gtk.main()
