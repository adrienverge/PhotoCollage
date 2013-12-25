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

	def draw_borders(self, canvas):
		x = self.x
		y = self.y
		draw = PIL.ImageDraw.Draw(canvas)
		draw.line((x, y) + (x + self.w - 1, y), fill="black")
		draw.line((x, y) + (x, y + self.h - 1), fill="black")
		draw.line((x, y + self.h - 1) + (x + self.w - 1, y + self.h - 1), fill="black")
		draw.line((x + self.w - 1, y) + (x + self.w - 1, y + self.h - 1), fill="black")
		draw.line((x, y) + (x + self.w - 1, y + self.h - 1), fill="gray")
		draw.line((x, y + self.h - 1) + (x + self.w - 1, y), fill="gray")

class PhotoExtent(Photo):

	def __init__(self, img, x, y):

		self.img_ref = img

		super(PhotoExtent, self).__init__(img.w, img.h, x, y)

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
		img.h = round(self.w * img.real_h / img.real_w)

		self.imglist.append(img)
		self.h += img.h

	def draw_borders(self, canvas):
		for img in self.imglist:
			img.draw_borders(canvas)

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

		for group in groups:
			if len(group["imglist"]) == 0:
				continue

			y = group["y"]
			alpha = group["h"] / sum(i.h for i in group["imglist"]) # enlargement
			for img in group["imglist"]:
				img.y = y
				img.h = round(img.h * alpha)
				for s in img.spacings:
					s.y = img.y
					s.h = img.h
				img.x += (img.w - round(img.h * img.real_w / img.real_h)) / 2
				img.w = round(img.h * img.real_w / img.real_h)
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
			mini = min(mini, round(min(exts)))
		if len(spcs) > 0:
			mini = min(mini, round(min(spcs)))
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

	def lost_space(self):

		lost = 0

		# With current implementation, image can only overflow on left and right
		for img in self.imglist:
			if isinstance(img, PhotoExtent):
				if img.img_ref.x + img.img_ref.w > self.x + self.w:
					lost += ((img.img_ref.x + img.img_ref.w) - (self.x + self.w)) / img.img_ref.w
			else:
				if img.x < self.x:
					lost += (self.x - img.x) / img.w

		return lost

class Page:

	def __init__(self, w, no_cols):
		self.w = w
		self.no_cols = no_cols
		self.cols = []

		x = 0
		col_w = round(self.w / self.no_cols)
		for i in range(no_cols):
			self.cols.append(Column(x, col_w))
			x += col_w

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
		if multicol and img.w / img.h > 1 and random.randint(0, 1):
			img.x = self.cols[multicol[0]].x
			img.y = max([self.cols[i].h for i in multicol])
			img.w = 0
			for i in multicol:
				img.w += self.cols[i].w
			img.h = round(img.w * img.real_h / img.real_w)
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
			c = self.next_col()
			c.append(img)

	def fill(self, imglist):
		for img in imglist:
			self.append(img)

	def draw_borders(self, canvas):
		for col in self.cols:
			col.draw_borders(canvas)
			draw = PIL.ImageDraw.Draw(canvas)
			draw.line((col.x, 0) + (col.x, col.h), fill="red")

	def get_width(self):
		return sum(c.w for c in self.cols)

	def get_height(self):
		return max(c.h for c in self.cols)

	def eat_space(self):

		# Step 1: set all columns at the same height
		H = round(sum([c.h for c in self.cols]) / self.no_cols)
		for c in self.cols:
			c.adjust_height(H)

	def eat_space2(self):
		# Step 2: arrange columns width to fit contents
		x = 0
		for c in self.cols:
			c.x = x
			c.adjust_width()
			x += c.w

	def wasted_space(self):
		return sum(c.wasted_space() for c in self.cols) / (self.get_width() * self.get_height())

	def lost_space(self):
		return sum(c.lost_space() for c in self.cols) / sum(len(c.imglist) for c in self.cols)

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

def main():

	#photolist = read_images()
	photolist = fake_images()
	random.shuffle(photolist)

	tries = []
	for i in range(100):
		page = Page(600, int(math.sqrt(len(photolist))))
		page.fill(copy.deepcopy(photolist))
		page.eat_space()
		page.eat_space2()
		if page.wasted_space() < 0.001:
			tries.append(page)

	tries.sort(key=lambda t: t.lost_space())

	page = tries[0]
	print("wasted space: %.2f%% + %.2f%%" % (100*page.wasted_space(), 100*page.lost_space()))
	canvas = PIL.Image.new("RGB", (page.get_width(), page.get_height()), "white")
	page.draw_borders(canvas)
	canvas.save("borders-2.png")

	page = tries[-1]
	print("wasted space: %.2f%% + %.2f%%" % (100*page.wasted_space(), 100*page.lost_space()))
	canvas = PIL.Image.new("RGB", (page.get_width(), page.get_height()), "white")
	page.draw_borders(canvas)
	canvas.save("borders-1.png")

	return

	page = Page(600, 6)
	page.fill(photolist)
	print("Page height: %d" % page.get_height())
	print("wasted space: %.2f%% + %.2f%%" % (100*page.wasted_space(), 100*page.lost_space()))

	canvas = PIL.Image.new("RGB", (page.get_width(), page.get_height()), "white")
	page.draw_borders(canvas)
	canvas.save("borders-0.png")

	page.eat_space()
	print("wasted space: %.2f%% + %.2f%%" % (100*page.wasted_space(), 100*page.lost_space()))

	canvas = PIL.Image.new("RGB", (page.get_width(), page.get_height()), "white")
	page.draw_borders(canvas)
	canvas.save("borders-1.png")

	page.eat_space2()
	print("wasted space: %.2f%% + %.2f%%" % (100*page.wasted_space(), 100*page.lost_space()))

	canvas = PIL.Image.new("RGB", (page.get_width(), page.get_height()), "white")
	page.draw_borders(canvas)
	canvas.save("borders-2.png")

if __name__ == "__main__":
	main()
