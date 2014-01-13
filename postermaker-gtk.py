#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Adrien Vergé

__author__ = "Adrien Vergé"
__copyright__ = "Copyright 2013, Adrien Vergé"
__license__ = "GPL"
__version__ = "1.0"

from gi.repository import Gtk, Gdk, GdkPixbuf, GObject
import io
from multiprocessing import Process, Pipe
import PIL.Image
from threading import Thread, Lock

from libpostermaker import *

def pil_img_to_raw(src_img):
	# Save image to a temporary buffer
	buf = io.BytesIO()
	src_img.save(buf, 'ppm')
	contents = buf.getvalue()
	buf.close()
	return contents

def gtk_img_from_raw(dest_img, contents):
	# Fill pixbuf from this buffer
	l = GdkPixbuf.PixbufLoader.new_with_type('pnm')
	l.write(contents)
	dest_img.set_from_pixbuf(l.get_pixbuf())
	l.close()

class PosterMakerWindow(Gtk.Window):

	def __init__(self):
		self.photolist = []

		self.make_window()

	def make_window(self):
		Gtk.Window.__init__(self, title="PosterMaker")

		self.set_border_width(10)

		box_window = Gtk.Box(spacing=10)
		self.add(box_window)

		# -----------
		#  First pan
		# -----------

		box_settings = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
		box_window.pack_start(box_settings, False, False, 0)

		self.btn_choose_images = Gtk.Button(label="Choose images")
		self.btn_choose_images.connect("clicked", self.choose_images)
		box_settings.pack_start(self.btn_choose_images, False, False, 0)

		self.lbl_images = Gtk.Label("0 images loaded")
		box_settings.pack_start(self.lbl_images, False, False, 0)

		label = Gtk.Label("Number of columns:", xalign=0)
		box_settings.pack_start(label, False, False, 0)

		self.spn_nocols = Gtk.SpinButton()
		self.spn_nocols.set_adjustment(Gtk.Adjustment(1, 1, 100, 1, 10, 0))
		self.spn_nocols.set_numeric(True)
		self.spn_nocols.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID)
		box_settings.pack_start(self.spn_nocols, False, False, 0)

		label = Gtk.Label("Border width (in percent):", xalign=0)
		box_settings.pack_start(label, False, False, 0)

		self.spn_border = Gtk.SpinButton()
		self.spn_border.set_adjustment(Gtk.Adjustment(2, 0, 100, 1, 10, 0))
		self.spn_border.set_numeric(True)
		self.spn_border.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID)
		box_settings.pack_start(self.spn_border, False, False, 0)

		label = Gtk.Label("Border color:", xalign=0)
		box_settings.pack_start(label, False, False, 0)

		self.cmb_bordercolor = Gtk.ComboBoxText()
		self.cmb_bordercolor.insert(0, "black", "black")
		self.cmb_bordercolor.insert(1, "white", "white")
		self.cmb_bordercolor.set_active(0)
		box_settings.pack_start(self.cmb_bordercolor, False, False, 0)

		label = Gtk.Label("Poster width (in pixels):", xalign=0)
		box_settings.pack_start(label, False, False, 0)

		self.spn_outw = Gtk.SpinButton()
		self.spn_outw.set_adjustment(Gtk.Adjustment(1000, 1, 100000, 1, 100, 0))
		self.spn_outw.set_numeric(True)
		self.spn_outw.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID)
		box_settings.pack_start(self.spn_outw, False, False, 0)

		# ------------
		#  Second pan
		# ------------

		box_skeleton = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
		box_window.pack_start(box_skeleton, True, True, 0)

		self.btn_skeleton = Gtk.Button(label="Generate a new layout")
		self.btn_skeleton.connect("clicked", self.make_skeleton)
		box_skeleton.pack_start(self.btn_skeleton, False, False, 0)

		self.img_skeleton = Gtk.Image()
		parse, color = Gdk.Color.parse("#888888")
		self.img_skeleton.modify_bg(Gtk.StateType.NORMAL, color)
		self.img_skeleton.set_size_request(300, 300)
		box_skeleton.pack_start(self.img_skeleton, True, True, 0)

		# -----------
		#  Third pan
		# -----------

		box_preview = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
		box_window.pack_start(box_preview, True, True, 0)

		self.btn_preview = Gtk.Button(label="Preview poster")
		self.btn_preview.connect("clicked", self.make_preview)
		box_preview.pack_start(self.btn_preview, False, False, 0)

		self.img_preview = Gtk.Image()
		parse, color = Gdk.Color.parse("#888888")
		self.img_preview.modify_bg(Gtk.StateType.NORMAL, color)
		self.img_preview.set_size_request(300, 300)
		box_preview.pack_start(self.img_preview, True, True, 0)

		self.btn_save = Gtk.Button(label="Save full-resolution poster...")
		self.btn_save.connect("clicked", self.save_poster)
		box_preview.pack_end(self.btn_save, False, False, 0)

		self.btn_skeleton.set_sensitive(False)
		self.btn_preview.set_sensitive(False)
		self.btn_save.set_sensitive(False)

	def choose_images(self, button):
		dialog = Gtk.FileChooserDialog("Choose images", button.get_toplevel(),
									   Gtk.FileChooserAction.OPEN,
									   select_multiple=True)
		dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
		dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)

		filefilter = Gtk.FileFilter()
		filefilter.add_pixbuf_formats()
		dialog.set_filter(filefilter)

		if dialog.run() == Gtk.ResponseType.OK:
			self.photolist = build_photolist(dialog.get_filenames())
			self.lbl_images.set_text("%d images loaded" % len(self.photolist))

			self.btn_preview.set_sensitive(False)
			self.btn_save.set_sensitive(False)
			if len(self.photolist) > 0:
				self.spn_nocols.set_value(round(math.sqrt(len(self.photolist))))

				self.make_skeleton(button)
				self.btn_skeleton.set_sensitive(True)

		dialog.destroy()

	def make_skeleton(self, button):
		random.shuffle(self.photolist)

		no_cols = self.spn_nocols.get_value_as_int()

		self.page = Page(1.0, no_cols)
		self.page.fill(copy.deepcopy(self.photolist))
		self.page.eat_space()
		self.page.eat_space2()

		w = self.img_skeleton.get_allocation().width
		h = self.img_skeleton.get_allocation().height
		enlargement = self.page.scale_to_fit(w, h)

		opts = PrintOptions(enlargement, PrintOptions.RENDER_SKELETON,
							PrintOptions.QUALITY_FAST)
		img = self.page.print(opts)

		gtk_img_from_raw(self.img_skeleton, pil_img_to_raw(img))

		self.btn_preview.set_sensitive(True)
		self.btn_save.set_sensitive(True)

	def get_border_width(self):
		return self.spn_border.get_value_as_int()

	def get_border_color(self):
		iter = self.cmb_bordercolor.get_active_iter()
		model = self.cmb_bordercolor.get_model()
		return model[iter][1]

	def make_preview(self, button):
		w = self.img_preview.get_allocation().width
		h = self.img_preview.get_allocation().height
		enlargement = self.page.scale_to_fit(w, h)

		opts = PrintOptions(enlargement, PrintOptions.RENDER_REAL,
							PrintOptions.QUALITY_FAST)
		opts.set_border(self.get_border_width(), self.get_border_color())

		def big_job(conn):
			"""
			This is the heavy work that will be executed in another process.
			It sends its result to a pipe.
			"""
			img = self.page.print(opts)

			conn.send(pil_img_to_raw(img))
			conn.close()

		def finish_job(conn):
			"""
			This is the final, lightweight work of displaying the image.
			It gets the heavy work result from the pipe.
			"""
			try:
				gtk_img_from_raw(self.img_preview, conn.recv())
			except EOFError:
				pass

		self.do_computing(big_job, finish_job)

	def save_poster(self, button):
		dialog = Gtk.FileChooserDialog("Save file", button.get_toplevel(),
									   Gtk.FileChooserAction.SAVE)
		dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
		dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
		dialog.set_do_overwrite_confirmation(True)

		filefilter = Gtk.FileFilter()
		filefilter.add_pixbuf_formats()
		dialog.set_filter(filefilter)

		savefile = None

		if dialog.run() == Gtk.ResponseType.OK:
			w = self.spn_outw.get_value_as_int()
			enlargement = w / self.page.get_width()

			opts = PrintOptions(enlargement, PrintOptions.RENDER_REAL,
								PrintOptions.QUALITY_BEST)
			opts.set_border(self.get_border_width(), self.get_border_color())

			savefile = dialog.get_filename()

		dialog.destroy()

		if not savefile:
			return

		def big_job(conn):
			"""
			This is the heavy work that will be executed in another process.
			"""
			img = self.page.print(opts)
			img.save(savefile)

			conn.close()

		def finish_job(conn):
			"""
			Nothing to do once the big job is done.
			"""
			pass

		self.do_computing(big_job, finish_job)

	def do_computing(self, big_job, finish_job):
		"""
		Displays a "please wait" dialog and do the job.

		This function is a bit tricky. It will create a new thread, to avoid
		freezing the GUI. It will also create a new subprocess, to take
		advantage of multi-core processors (and also because PIL seems to
		have problems with threads).

		The lock is here for synchronization: the thread must wait for the
		"please wait" dialog to appear, to make sure it will not destroy it
		before it is created.
		"""
		lock = Lock()
		lock.acquire()

		compdialog = ComputingDialog(self, lock)

		rd_conn, wr_conn = Pipe(False)
		process = Process(target=big_job, args=(wr_conn,))

		def thread_job(window):
			lock.acquire()

			process.start()
			finish_job(rd_conn)
			process.join()

			compdialog.destroy()

		thread = Thread(target=thread_job, args=(self,))
		thread.start()

		response = compdialog.run()
		if response == Gtk.ResponseType.CANCEL:
			wr_conn.close()
			process.terminate()

class ComputingDialog(Gtk.Dialog):

	def __init__(self, parent, lock):
		Gtk.Dialog.__init__(self, "Please wait", parent, 0,
							(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

		self.set_default_size(300, -1)
		self.set_border_width(10)

		box = self.get_content_area()
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
		box.add(vbox)

		label = Gtk.Label("Performing image computation...")
		vbox.pack_start(label, True, True, 0)

		self.progressbar = Gtk.ProgressBar()
		self.progressbar.pulse()
		vbox.pack_start(self.progressbar, True, True, 0)

		self.show_all()

		self.timeout_id = GObject.timeout_add(50, self.on_timeout, None)

		lock.release()

	def on_timeout(self, user_data):
		self.progressbar.pulse()

		# Return True so that it continues to get called
		return True

def main():
	win = PosterMakerWindow()
	win.connect("delete-event", Gtk.main_quit)
	win.show_all()
	Gtk.main()

if __name__ == '__main__':
	main()
