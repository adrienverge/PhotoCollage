#!/usr/bin/env python3

from gi.repository import Gtk, Gdk, GdkPixbuf
import io
import PIL.Image

from libpostermaker import *

def pil_img_to_gtk_img(src_img, dest_img):
	# Save image to a temporary buffer
	buf = io.BytesIO()
	src_img.save(buf, 'ppm')
	contents = buf.getvalue()
	buf.close()

	# Fill pixbuf from this buffer
	l = GdkPixbuf.PixbufLoader.new_with_type('pnm')
	l.write(contents)
	dest_img.set_from_pixbuf(l.get_pixbuf())
	l.close()

class MyWindow(Gtk.Window):

	def __init__(self):
		self.photolist = []

		self.make_window()

	def make_window(self):
		Gtk.Window.__init__(self, title="PosterMaker")

		self.set_border_width(10)

		box_window = Gtk.Box(spacing=6)
		self.add(box_window)

		# -----------
		#  First pan
		# -----------

		box_settings = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
		box_window.pack_start(box_settings, False, False, 0)

		self.btn_choose_images = Gtk.Button(label="Choose images")
		self.btn_choose_images.connect("clicked", self.choose_images)
		box_settings.pack_start(self.btn_choose_images, False, False, 0)

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
		dialog = Gtk.FileChooserDialog("Choose images", button.get_toplevel(), Gtk.FileChooserAction.OPEN, select_multiple=True)
		dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
		dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)

		filefilter = Gtk.FileFilter()
		filefilter.add_pixbuf_formats()
		dialog.set_filter(filefilter)

		if dialog.run() == Gtk.ResponseType.OK:
			self.photolist = build_photolist(dialog.get_filenames())

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

		img = self.page.print(self.page.scale_to_fit(w, h), None, True)

		pil_img_to_gtk_img(img, self.img_skeleton)

		self.btn_preview.set_sensitive(True)
		self.btn_save.set_sensitive(True)

	def make_preview(self, button):
		# get border width
		border = {"width": self.spn_border.get_value_as_int()}

		# get border color
		iter = self.cmb_bordercolor.get_active_iter()
		model = self.cmb_bordercolor.get_model()
		border["color"] = model[iter][1]

		w = self.img_preview.get_allocation().width
		h = self.img_preview.get_allocation().height

		img = self.page.print(self.page.scale_to_fit(w, h), border, False, True)

		pil_img_to_gtk_img(img, self.img_preview)

	def save_poster(self, button):
		dialog = Gtk.FileChooserDialog("Save file", button.get_toplevel(), Gtk.FileChooserAction.SAVE)
		dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
		dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
		dialog.set_do_overwrite_confirmation(True)

		filefilter = Gtk.FileFilter()
		filefilter.add_pixbuf_formats()
		dialog.set_filter(filefilter)

		if dialog.run() == Gtk.ResponseType.OK:
			border_w = self.spn_border.get_value_as_int()
			w = 1000
			h = 1000

			img = self.page.print(self.page.scale_to_fit(w, h), border_w, False, False)

			print(dialog.get_filename())
			
			img.save(dialog.get_filename())

		dialog.destroy()

win = MyWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
