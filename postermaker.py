#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Adrien Vergé

__author__ = "Adrien Vergé"
__copyright__ = "Copyright 2013, Adrien Vergé"
__license__ = "GPL"
__version__ = "1.0"

"""
The design is based on LightBox, as presented in [1].

[1]: http://blog.vjeux.com/2012/image/image-layout-algorithm-lightbox.html

-------------------------
|                       |
|                       |
|        Page           |  The "Page" object represents the whole page that
|                       |  will give the final assembled image.
|                       |
-------------------------

-------------------------
|       |       |       |
|       |Column |       |
|       |       |Column |  A page is divided into columns.
|Column |       |       |
|       |       |       |
-------------------------

-------------------------
| Photo | Photo     x<--|-------- PhotoExtent
|-------|               |
| Photo |---------------|  Each column contains photos. When a photo is located
|-------| Photo |       |  in several columns, its "extended" flag is set, and
| Photo |       | Photo |  a "PhotoExtent" object is added to the column on the
-------------------------  right.

The layout placing process can be divided in three phases.

Phase A: Fill columns with photos.
	Photos are added to columns, one by one, until they are no more photos.
	Each new photo is put in the smallest column, so as to have balanced
	columns.  If two columns have approximately the same height, a photo can be
	"extended" to fit two columns. In this case, the "Photo" object is put in
	the first column, and the second column takes a "PhotoExtent" object to
	save the taken space.

Phase B: Set all columns to same height.
	A global common height is computed for all columns, and every of them is
	stressed or extended to this common length.  This can result in a decrease
	or increase in columns' width.

Phase C: Adapt columns' width.
	Since every column images may have different widths, each column new width
	is set to the smallest width amongst its images.

This process makes images with holes and cropped images, whose importance can
be measured with the "wasted_space" and "hidden_space" functions.  A simple way
to get a good layout is to generate many and keep the one with the smallest of
these values.

"""

import copy
import math
import PIL.Image
import PIL.ImageDraw
import random

class Photo:

	def __init__(self, w, h, x=0, y=0):
		self.real_w = self.w = w
		self.real_h = self.h = h

		self.x = x
		self.y = y

		self.extended = False
		self.spacings = []

	def scale(self, scale):
		self.print_x = scale * self.x
		self.print_y = scale * self.y
		self.print_w = scale * self.w
		self.print_h = scale * self.h

	def draw_preview(self, canvas):
		xy = (self.print_x, self.print_y)
		xY = (self.print_x, self.print_y + self.print_h - 1)
		Xy = (self.print_x + self.print_w - 1, self.print_y)
		XY = (self.print_x + self.print_w - 1, self.print_y + self.print_h - 1)

		draw = PIL.ImageDraw.Draw(canvas)
		draw.line(xy + Xy, fill="black")
		draw.line(xy + xY, fill="black")
		draw.line(xY + XY, fill="black")
		draw.line(Xy + XY, fill="black")
		draw.line(xy + XY, fill="gray")
		draw.line(xY + Xy, fill="gray")

class PhotoExtent(Photo):

	def __init__(self, img, x, y):
		self.img_ref = img

		super(PhotoExtent, self).__init__(img.w, img.h, x, y)

	def draw_preview(self, canvas):
		pass

class Column:

	def __init__(self, x, w):
		self.imglist = []
		self.x = x
		self.w = w
		self.h = 0

	# -------------------
	#  Phase B functions
	# -------------------

	def adjust_height(self, H):
		# Group "movable" zones together, spacings being non-movable
		groups = []
		groups.append({"imglist": []})
		groups[-1]["y"] = 0
		for img in self.imglist:
			if not isinstance(img, PhotoExtent):
				groups[-1]["imglist"].append(img)
			else:
				groups[-1]["h"] = img.y - groups[-1]["y"]
				groups.append({"imglist": []})
				groups[-1]["y"] = img.y + img.h
		groups[-1]["h"] = H - groups[-1]["y"]

		# Adjust height for each group independently
		for group in groups:
			if len(group["imglist"]) == 0:
				continue

			y = group["y"]
			alpha = group["h"] / sum(i.h for i in group["imglist"]) # enlargement
			for img in group["imglist"]:
				img.y = y
				img.h = img.h * alpha
				for s in img.spacings:
					s.y = img.y
					s.h = img.h
				img.x += (img.w - img.h * img.real_w / img.real_h) / 2
				img.w = img.h * img.real_w / img.real_h
				y += img.h

		self.h = H

	def get_width(self):
		"""Returns the width of the smallest image in this column"""
		imgs = list(img.w for img in self.imglist if not
					isinstance(img, PhotoExtent) and not img.extended)
		exts = list(img.w / 2 for img in self.imglist if
					not isinstance(img, PhotoExtent) and img.extended)
		spcs = list(img.img_ref.w / 2 for img in self.imglist if
					isinstance(img, PhotoExtent))
		mini = 2**32
		if len(imgs) > 0:
			mini = min(imgs)
		if len(exts) > 0:
			mini = min(mini, min(exts))
		if len(spcs) > 0:
			mini = min(mini, min(spcs))
		return mini

	def adjust_width(self):
		self.w = self.get_width()

		for img in self.imglist:
			if not isinstance(img, PhotoExtent) and not img.extended:
				img.x = self.x + (self.w - img.w) / 2
			elif not isinstance(img, PhotoExtent):
				img.x = self.x + (self.w - img.w) / 2
			else:
				img.img_ref.x += self.w / 2

	# -------------------
	#  Ranking functions
	# -------------------

	def wasted_space(self):
		waste = 0

		# Waste on left and right
		for img in self.imglist:
			if img.w < self.w:
				waste += img.h * (self.w - img.w)

		# Waste between non-adjacent images
		for i in range(len(self.imglist) - 1):
			img0 = self.imglist[i]
			img1 = self.imglist[i + 1]
			if img0.y + img0.h < img1.y:
				waste += self.w * (img1.y - (img0.y + img0.h))
		img0 = self.imglist[-1]
		if img0.y + img0.h < self.h:
			waste += self.w * (self.h - (img0.y + img0.h))

		return waste

	def hidden_space(self):
		hidden = 0

		# With current implementation, image can only overflow on left/right
		for img in self.imglist:
			if isinstance(img, PhotoExtent):
				if img.img_ref.x + img.img_ref.w > self.x + self.w:
					w = (img.img_ref.x + img.img_ref.w) - (self.x + self.w)
					hidden += w / img.img_ref.w
			else:
				if img.x < self.x:
					hidden += (self.x - img.x) / img.w

		return hidden

	# ---------------------
	#  Rendering functions
	# ---------------------

	def scale(self, scale):
		self.print_x = scale * self.x
		self.print_w = scale * self.w
		self.print_h = scale * self.h
		for img in self.imglist:
			img.scale(scale)

	def draw_preview(self, canvas):
		for img in self.imglist:
			img.draw_preview(canvas)

	def draw_borders(self, canvas, border):
		color = "blue"
		draw = PIL.ImageDraw.Draw(canvas)

		for img in self.imglist[1:]:
			xy = (self.print_x, img.print_y - border / 2)
			XY = (self.print_x + self.print_w, img.print_y + border / 2)
			draw.rectangle(xy + XY, color)

		if self.print_x > 0:
			for img in self.imglist:
				if not isinstance(img, PhotoExtent):
					xy = (self.print_x - border / 2, img.print_y)
					XY = (self.print_x + border / 2, img.print_y + img.print_h)
					draw.rectangle(xy + XY, color)

class Page:

	def __init__(self, w, no_cols):
		self.w = w
		self.no_cols = no_cols
		self.cols = []

		x = 0
		col_w = self.w / self.no_cols
		for i in range(no_cols):
			self.cols.append(Column(x, col_w))
			x += col_w

	# -------------------
	#  Phase A functions
	# -------------------

	def next_col(self):
		cur_min = 2**31
		index = None
		for i in range(self.no_cols):
			if self.cols[i].h < cur_min:
				cur_min = self.cols[i].h
				index = i
		return index

	def worth_multicol(self):
		i = self.next_col()
		for j in range(max(0, i - 1), min(self.no_cols, i + 2)):
			if j == i:
				continue
			c0 = self.cols[i]
			c1 = self.cols[j]
			if (c1.h > .9 * c0.h) and (c1.h < 1.1 * c0.h):
				return sorted([i, j])

	def append(self, img):
		multicol = self.worth_multicol()
		if multicol and img.w / img.h > 1 and random.randint(0, 1):
			img.x = self.cols[multicol[0]].x
			img.y = max([self.cols[i].h for i in multicol])
			img.w = 0
			for i in multicol:
				img.w += self.cols[i].w
			img.h = img.w * img.real_h / img.real_w
			for i in multicol:
				if i == multicol[0]:
					img.extended = True
					self.cols[i].imglist.append(img)
				else:
					s = PhotoExtent(img, self.cols[i].x, self.cols[i].h)
					self.cols[i].imglist.append(s)
					img.spacings.append(s)
				self.cols[i].h = img.y + img.h # every column is set at the longest
		else:
			c = self.cols[self.next_col()]

			img.x = c.x
			img.y = c.h
			img.w = c.w
			img.h = c.w * img.real_h / img.real_w

			c.imglist.append(img)
			c.h += img.h

	def fill(self, imglist):
		for img in imglist:
			self.append(img)

	def get_width(self):
		return sum(c.w for c in self.cols)

	def get_height(self):
		return max(c.h for c in self.cols)

	# -------------------
	#  Phase B functions
	# -------------------

	def eat_space(self):
		H = sum([c.h for c in self.cols]) / self.no_cols
		for c in self.cols:
			c.adjust_height(H)

	# -------------------
	#  Phase C functions
	# -------------------

	def eat_space2(self):
		x = 0
		for c in self.cols:
			c.x = x
			c.adjust_width()
			x += c.w

	# -------------------
	#  Ranking functions
	# -------------------

	def wasted_space(self):
		return sum(c.wasted_space() for c in self.cols) / \
			   (self.get_width() * self.get_height())

	def hidden_space(self):
		return sum(c.hidden_space() for c in self.cols) / \
			   sum(len(c.imglist) for c in self.cols)

	# ---------------------
	#  Rendering functions
	# ---------------------

	def scale(self, scale):
		self.print_w = scale * self.get_width()
		self.print_h = scale * self.get_height()
		for col in self.cols:
			col.scale(scale)

	def draw_preview(self, canvas):
		for col in self.cols:
			col.draw_preview(canvas)

	def draw_borders(self, canvas, border):
		color = "blue"
		W = self.print_w
		H = self.print_h

		draw = PIL.ImageDraw.Draw(canvas)
		draw.rectangle((0, 0) + (border, H), color)
		draw.rectangle((W - border, 0) + (W, H), color)
		draw.rectangle((0, 0) + (W, border), color)
		draw.rectangle((0, H - border) + (W, H), color)

		for col in self.cols:
			col.draw_borders(canvas, border)

def read_images():
	ret = []
	dir = "/docs/archive/2013/12"
	list = ["IMG_20131201_111223.jpg", "IMG_20131201_111226.jpg",
			"IMG_20131201_155815.jpg", "IMG_20131201_155820.jpg",
			"IMG_20131202_094007.jpg", "IMG_20131202_112407.jpg",
			"IMG_20131202_122617.jpg", "IMG_20131202_122642.jpg",
			"IMG_20131202_122732.jpg", "IMG_20131207_162832.jpg",
			"IMG_20131207_200205.jpg", "IMG_20131207_200207.jpg",
			"IMG_2489.JPG", "IMG_2490.JPG",
			"IMG_2491.JPG", "IMG_2492.JPG",
			"IMG_2493.JPG", "IMG_2494.JPG",
			"IMG_2495.JPG", "IMG_2496.JPG"]
	for name in list:
		img = PIL.Image.open(dir + "/" + name)
		print("%d\t%d" % img.size)
		ret.append(Photo(*img.size))
	return ret

def fake_images():
	ret = []
	for i in range(random.randint(10, 60)):
		ret.append(Photo(1000, 1000 * (.5 + random.random())))
	return ret

def print_preview(filename, page, width, border):
	page.scale(width / page.get_width())
	canvas = PIL.Image.new("RGB", (int(page.print_w), int(page.print_h)), "white")
	page.draw_preview(canvas)
	page.draw_borders(canvas, border)
	canvas.save(filename)

def main():
	photolist = read_images()
	#photolist = fake_images()

	tries = []
	best_no_cols = int(math.sqrt(len(photolist)))
	for no_cols in range(max(1, best_no_cols - 1), best_no_cols + 3):
		for i in range(3):
			page = Page(1.0, no_cols)
			random.shuffle(photolist)
			page.fill(copy.deepcopy(photolist))
			page.eat_space()
			page.eat_space2()
			if page.wasted_space() < 0.001:
				tries.append(page)

	tries.sort(key=lambda t: t.hidden_space())

	page = tries[0]
	print("wasted space: %.2f%% + %.2f%%" % (100*page.wasted_space(), 100*page.hidden_space()))

	print_preview("borders-2.png", page, 600 * page.get_width() / page.get_height(), 6)

	page = tries[-1]
	print("wasted space: %.2f%% + %.2f%%" % (100*page.wasted_space(), 100*page.hidden_space()))
	print_preview("borders-1.png", page, 600 * page.get_width() / page.get_height(), 8)

if __name__ == "__main__":
	main()
