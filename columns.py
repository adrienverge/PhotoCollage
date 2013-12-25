#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Adrien Vergé

__author__ = "Adrien Vergé"
__copyright__ = "Copyright 2013, Adrien Vergé"
__license__ = "GPL"
__version__ = "1.0"

"""
Based on LightBox:
http://blog.vjeux.com/2012/image/image-layout-algorithm-lightbox.html
"""

import random
from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image
import wand.exceptions

class Photo:

	def __init__(self, w, h):
		self.real_w = self.w = w
		self.real_h = self.h = h

		self.spacings = []

	def ratio(self):
		return self.w / self.h

	#def draw_borders(self, canvas, x):
	def draw_borders(self, canvas):
		x = self.x
		y = self.y
		with Drawing() as draw:
			draw.line((x, y), (x + self.w - 1, y))
			draw.line((x, y), (x, y + self.h - 1))
			draw.line((x, y + self.h - 1), (x + self.w - 1, y + self.h - 1))
			draw.line((x + self.w - 1, y), (x + self.w - 1, y + self.h - 1))
			draw.line((x, y), (x + self.w - 1, y + self.h - 1))
			draw.line((x, y + self.h - 1), (x + self.w - 1, y))
			draw(canvas)

	def smaller_photo(self, w, h):
		return w * h

class Spacing(Photo):

	def __init__(self, img, x, y):

		self.img_ref = img
		self.x = x
		self.y = y

		super(Spacing, self).__init__(img.w, img.h)

	#def draw_borders(self, canvas, x):
	def draw_borders(self, canvas):
		pass

class Column:

	def __init__(self, x, w):

		self.imglist = []
		self.x = x
		self.w = w
		self.h = 0

	def append(self, img):

		img.x = self.x
		img.y = self.h

		img.w = self.w
		img.h = int(self.w * img.real_h / img.real_w)

		self.imglist.append(img)
		self.h += img.h

	#def draw_borders(self, canvas, x):
	def draw_borders(self, canvas):
		for img in self.imglist:
			img.draw_borders(canvas)

	def eat_space(self, H):
		space = H - self.h
		if space == 0:
			return

		# Group "movable" zones together, spacings being non-movable
		groups = []
		groups.append({"imglist": []})
		groups[-1]["y"] = 0
		for img in self.imglist:
			if not isinstance(img, Spacing):
				groups[-1]["imglist"].append(img)
			else:
				groups[-1]["h"] = img.y - groups[-1]["y"]
				groups.append({"imglist": []})
				groups[-1]["y"] = img.y + img.h
		groups[-1]["h"] = H - groups[-1]["y"]
		#groups[-1]["h"] = self.h - groups[-1]["y"]

		#for img in self.imglist:
		for group in groups:
			if len(group) == 0:
				continue
			print("groupe de %d" % len(group["imglist"]))
			y = group["y"]
			h = group["h"]
			g_h = sum(i.h for i in group["imglist"])
			for img in group["imglist"]:
				img.y = y
				img.h = int(img.h * h / g_h)
				for s in img.spacings:
					s.y = img.y
					s.h = img.h
				img.x += (img.w - int(img.h * img.real_w / img.real_h)) / 2
				img.w = int(img.h * img.real_w / img.real_h)
				y += img.h
		# TODO: remettre
		# self.h = H

class Page:

	def __init__(self, w, no_cols):
		self.w = w
		self.no_cols = no_cols
		self.cols = []
		x = 0
		for i in range(no_cols):
			self.cols.append(Column(x, int(self.w / self.no_cols)))
			x += int(self.w / self.no_cols)

	def next_col_index(self):
		cur_min = 2**31
		index = None
		for i in range(self.no_cols):
			if self.cols[i].h < cur_min:
				cur_min = self.cols[i].h
				index = i
		return index

	def next_col(self):
		return self.cols[self.next_col_index()]

	def worth_multicol(self):
		"""
		for i in range(self.no_cols - 1):
			c1 = self.cols[i]
			c2 = self.cols[i + 1]
			if c1.h == c2.h:
				return [i, i + 1]
		return None
		"""
		i = self.next_col_index()
		for j in range(max(0, i - 1), min(self.no_cols, i + 2)):
			if j == i:
				continue
			c0 = self.cols[i]
			c1 = self.cols[j]
			if (c1.h > .9 * c0.h) and (c1.h < 1.1 * c0.h):
				return sorted([i, j])

	def append(self, img):

		multicol = self.worth_multicol()
		if multicol and img.ratio() > 1 and random.randint(0, 1):
			img.x = self.cols[multicol[0]].x
			img.y = max([self.cols[i].h for i in multicol])
			img.w = 0
			for i in multicol:
				img.w += self.cols[i].w
			img.h = int(img.w * img.real_h / img.real_w)
			for i in multicol:
				if i == multicol[0]:
					self.cols[i].imglist.append(img)
				else:
					s = Spacing(img, self.cols[i].x, self.cols[i].h)
					self.cols[i].imglist.append(s)
					img.spacings.append(s)
				self.cols[i].h = img.y + img.h # every column is set at the longest
		else:
			c = self.next_col()
			c.append(img)

	def fill(self, imglist):
		for img in imglist:
			self.append(img)

	def draw_borders(self, canvas):
		for col in self.cols:
			col.draw_borders(canvas)
			with Drawing() as draw:
				draw.fill_color = Color("red")
				draw.line((col.x, 0), (col.x, col.h))
				draw(canvas)

	def get_height(self):
		return max([c.h for c in self.cols])

	def eat_space(self):

		# Step 1: set all columns at the same height
		H = int(sum([c.h for c in self.cols]) / self.no_cols)
		for c in self.cols:
			c.eat_space(H)

		# Step 2: arrange columns width to fit contents
		# TODO

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
		filename = dir + "/" + name
		with Image(filename=filename) as img:
			print("%d\t%d" % (img.width, img.height))
			ret.append(Photo(img.width, img.height))
	return ret

def fake_images():
	ret = [ Photo(1944,	2592), Photo(1944,	2592), Photo(2592,	1944),
			Photo(1944,	2592), Photo(1944,	2592), Photo(2592,	1944),
			Photo(1944,	2592), Photo(1944,	2592), Photo(1944,	2592),
			Photo(2592,	1944), Photo(1944,	2592), Photo(1944,	2592),
			Photo(2816,	2112), Photo(2816,	2112), Photo(2816,	2112),
			Photo(2816,	2112), Photo(2816,	2112), Photo(2816,	2112),
			Photo(2816,	2112), Photo(2816,	2112)]
	for i in range(len(ret)):
		ret[i].real_w = ret[i].w = int(ret[i].w * (.9 + .2 * random.random()))
		ret[i].real_h = ret[i].h = int(ret[i].h * (.9 + .2 * random.random()))
	return ret

def main():

	photolist = fake_images()
	photolist.extend(fake_images())
	random.shuffle(photolist)

	page = Page(600, 6)
	page.fill(photolist)
	print("Page height: %d" % page.get_height())

	canvas = Image(width=page.w, height=page.get_height(), background=Color("white"))
	page.draw_borders(canvas)
	canvas.save(filename="borders-0.png")

	page.eat_space()

	canvas = Image(width=page.w, height=page.get_height(), background=Color("white"))
	page.draw_borders(canvas)
	canvas.save(filename="borders.png")

if __name__ == "__main__":
	main()
