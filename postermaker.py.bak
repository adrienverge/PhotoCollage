#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Adrien Vergé

__author__ = "Adrien Vergé"
__copyright__ = "Copyright 2013, Adrien Vergé"
__license__ = "GPL"
__version__ = "1.0"

import argparse
import math
import random
from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image
import wand.exceptions

class AlbumImage:
	def __init__(self, filename):
		with Image(filename=filename) as self.img:
			self.filename = filename
			self.width = self.img.width
			self.height = self.img.height

	def ratio(self):
		return self.width / self.height

	def outputimg(self, w, h):
		img = Image(filename=self.filename)
		destratio = w / h
		if self.ratio() > destratio:
			newwidth = int(destratio * self.height)
			img.crop(int((self.width - newwidth)/2), 0,
					 width=newwidth, height=self.height)
		elif self.ratio() < destratio:
			newheight = int(self.width / destratio)
			img.crop(0, int((self.height - newheight)/2),
					 width=self.width, height=newheight)
		img.resize(w, h)
		return img

class AlbumSplit:
	def __init__(self, w, h, a0, a1):
		self.w = w
		self.h = h
		self.kids = [a0, a1]

	def ratio(self):
		return self.w / self.h

	def outputimg(self):
		canvas = Image(width=self.w, height=self.h)

		newwidth2 = self.child_w()
		newheight2 = self.child_h()

		if isinstance(self.kids[0], AlbumImage):
			img0 = self.kids[0].outputimg(newwidth2, newheight2)
		else:
			img0 = self.kids[0].outputimg()

		if isinstance(self.kids[1], AlbumImage):
			img1 = self.kids[1].outputimg(newwidth2, newheight2)
		else:
			img1 = self.kids[1].outputimg()

		canvas.composite(img0, left=0, top=0)
		canvas.composite(img1, left=self.child_2x(), top=self.child_2y())

		return canvas

class AlbumHSplit(AlbumSplit):
	def child_w(self):
		return int(self.w/2)
	def child_h(self):
		return self.h
	def child_2x(self):
		return int(self.w/2)
	def child_2y(self):
		return 0

class AlbumVSplit(AlbumSplit):
	def child_w(self):
		return self.w
	def child_h(self):
		return int(self.h/2)
	def child_2x(self):
		return 0
	def child_2y(self):
		return int(self.h/2)

class Album:
	def __init__(self, w, h, content=None):
		self.w = w
		self.h = h
		# content can be either an AlbumImage or an AlbumSplit
		self.content = content

	def add_imgs(self, imglist):
		if len(imglist) == 1:
			self.content = imglist[0]
		elif len(imglist) == 2:
			self.content = AlbumVSplit(self.w, self.h, imglist[0], imglist[1])
		elif len(imglist) > 1:
			part0 = imglist[:int(len(imglist)/2)]
			part1 = imglist[int(len(imglist)/2):]
			a0 = Album()
			a0.add_imgs(part0)
			a1 = Album()
			a1.add_imgs(part1)
			self.content = AlbumVSplit(a0, a1)

	def outputimg(self):
		if isinstance(self.content, AlbumImage):
			return self.content.outputimg(self.w, self.h)
		else:
			return self.content.outputimg()

def mkalbum(w, h, imglist):
	bestratio = 4 / 3.0

	# tmp
	#imglist = [imglist[0], imglist[1]]
	W = w
	H = h

	portraitimgs = []
	paysageimgs = []
	for img in imglist:
		if img.ratio() < 1:
			portraitimgs.append(img)
		else:
			paysageimgs.append(img)
	por = len(portraitimgs)
	pay = len(paysageimgs)

	if w / h > 1:
		# -------------
		# |           |
		# |           |
		# |           |
		# -------------
		nb_portraits = por
		if por == 1 and pay % 2 == 0:
			pass

	album = Album(W, H)
	album.add_imgs(imglist)
	"""
	if len(imglist) == 1:
		album = Album(W, H, imglist[0])
	elif len(imglist) == 2:
		album = Album(W, H, AlbumHSplit(W, H, imglist[0], imglist[1]))
	elif len(imglist) == 3:
		part1 = imglist[1:]
		bottom = AlbumVSplit(int(W/2), H, imglist[1], imglist[2])
		album = Album(W, H, AlbumHSplit(W, H, imglist[0], bottom))
	elif len(imglist) == 4:
		left = AlbumVSplit(int(W/2), H, imglist[0], imglist[1])
		right = AlbumVSplit(int(W/2), H, imglist[2], imglist[3])
		album = Album(W, H, AlbumHSplit(W, H, left, right))
	else:
		raise Exception("%d images" % len(imglist))
	"""

	return album.outputimg()

class PageImage():

	def __str__(self):
		return "<Image>"

	def draw_borders(self, img, w, h, x, y):
		pass

class Page:

	def __init__(self, scale, content=None):
		self.scale = scale
		self.content = content

	def bigger_scale(self):
		if isinstance(self.content, PageSplit):
			s0 = self.content.part0.bigger_scale()
			s1 = self.content.part1.bigger_scale()
			if s0 >= s1:
				return s0
			return s1
		return self.scale

	def lower_scale(self):
		if isinstance(self.content, PageSplit):
			s0 = self.content.part0.lower_scale()
			s1 = self.content.part1.lower_scale()
			if s0 <= s1:
				return s0
			return s1
		return self.scale

			# -------------------
			# |        |        |
			# |        |        |
			# -------------------
			# |        |        |
			# |        |        |
			# -------------------

			# -------------------
			# |     |     |     |
			# -------------------
			# |     |     |     |
			# -------------------
			# |     |     |     |
			# -------------------

	def __str__(self):
		s = " [scale=%.2f]:" % self.scale
		pre = " "
		for line in str(self.content).split("\n"):
			s += pre + line
			pre = "\n  "
		return s

	def draw_borders(self, img, w, h, x, y):
		if isinstance(self.content, PageSplit):
			self.content.draw_borders(img, w, h, x, y)

class PaysagePage(Page):

	def __str__(self):
		return "PaysagePage" + super(self.__class__, self).__str__()

class PortraitPage(Page):

	def __str__(self):
		return "PortraitPage" + super(self.__class__, self).__str__()

class PageSplit:
	def __init__(self, part0, part1, splitoffset):
		self.part0 = part0
		self.part1 = part1
		self.splitoffset = splitoffset

	def __str__(self):
		return "\n" + str(self.part0) + "\n" + str(self.part1)

class PageHSplit(PageSplit):

	def __str__(self):
		return "-- PageHSplit --" + super(self.__class__, self).__str__()

	def draw_borders(self, img, w, h, x, y):
		w0 = w * self.splitoffset
		w1 = w * (1 - self.splitoffset)
		self.part0.draw_borders(img, w0, h, x, y)
		self.part1.draw_borders(img, w1, h, x + w0, y)
		with Drawing() as draw:
			draw.line((x + w0, y), (x + w0, y + h))
			draw(img)

class PageVSplit(PageSplit):

	def __str__(self):
		return "-- PageVSplit --" + super(self.__class__, self).__str__()

	def draw_borders(self, img, w, h, x, y):
		h0 = h * self.splitoffset
		h1 = h * (1 - self.splitoffset)
		self.part0.draw_borders(img, w, h0, x, y)
		self.part1.draw_borders(img, w, h1, x, y + h0)
		with Drawing() as draw:
			draw.line((x, y + h0), (x + w, y + h0))
			draw(img)

cache = {}
array_possibles = (
	(0, 2), (0, 5), (0, 8), (0, 11), (0, 14),
	(1, 0), (1, 3), (1, 6), (1, 9), (1, 12),
	(2, 1), (2, 4), (2, 7), (2, 10), (2, 13),
	(3, 2), (3, 5), (3, 8), (3, 11), (4, 0),
	(4, 3), (4, 6), (4, 9), (5, 1), (5, 4),
	(5, 7), (5, 10), (6, 2), (6, 5), (6, 8),
	(7, 0), (7, 3), (7, 6), (8, 1), (8, 4),
	(8, 7), (9, 2), (9, 5), (10, 0), (10, 3),
	(11, 1), (11, 4), (12, 2), (13, 0), (14, 1)
)

global_smallest = 0
global_biggest = 0

def find_arrangements(pagetype, scale, n_pay, n_por):
	"""Returns a list of Pages that match"""

	global cache
	global global_smallest, global_biggest
	global array_possibles

	#if scale < global_smallest:
		#return []
		#print("global_smallest = %f" % global_smallest)
		#print("global_biggest = %f" % global_biggest)
		#print("scale = %f" % scale)
		#return []

	if n_pay <= 16 and n_por <= 16:
		if (pagetype == PaysagePage and (n_pay, n_por) not in array_possibles) \
		    or (pagetype == PortraitPage and (n_por, n_pay) not in array_possibles):
			return []

	if pagetype == PaysagePage:
		cacheid = (int(1.0/scale) << 16) | (n_por << 8) | n_pay
	else:
		cacheid = (int(1.0/scale) << 16) | (n_pay << 8) | n_por

	#if cacheid in cache:
	#	return []

	ret = []
	
	if n_pay == 1 and n_por == 0:
		if pagetype == PaysagePage:
			page = PaysagePage(scale)
			page.content = PageImage()
			ret.append(page)
	elif n_pay == 0 and n_por == 1:
		if pagetype == PortraitPage:
			page = PortraitPage(scale)
			page.content = PageImage()
			ret.append(page)
	elif n_pay == 2 and n_por == 0:
		if pagetype == PortraitPage:
			page = PortraitPage(scale)
			top = PaysagePage(scale/2)
			bottom = PaysagePage(scale/2)
			top.content = PageImage()
			bottom.content = PageImage()
			page.content = PageVSplit(top, bottom, 0.5)
			ret.append(page)
	elif n_pay == 0 and n_por == 2:
		if pagetype == PaysagePage:
			page = PaysagePage(scale)
			left = PortraitPage(scale/2)
			right = PortraitPage(scale/2)
			left.content = PageImage()
			right.content = PageImage()
			page.content = PageHSplit(left, right, 0.5)
			ret.append(page)
	elif n_pay + n_por > 2:
		if pagetype == PaysagePage:
			subpagetype = PortraitPage
			subsplittype = PageHSplit
		else:
			subpagetype = PaysagePage
			subsplittype = PageVSplit
		for i in range(0, math.ceil(n_pay/2) + 1):
			for j in range(0, math.ceil(n_por/2) + 1):
				if (i == 0 and j == 0) or (i == n_pay and j == n_por):
					continue
				ar_left = find_arrangements(subpagetype, scale/2, i, j)
				ar_right = find_arrangements(subpagetype, scale/2, n_pay - i, n_por - j)
				for al in ar_left:
					for ar in ar_right:
						page = subpagetype(scale)
						page.content = subsplittype(al, ar, 0.5)
						ret.append(page)

	if len(ret) == 0:
		cache[cacheid] = True

	return ret

def cut_in_small_pieces(n_pay, n_por):
	"""Cuts a big number of images into small chunks of less than 16 images"""

	possibles = {}
	n = len(array_possibles)
	for a in range(0, n):
		for b in range(a+1, n):
			for c in range(b+1, n):
				for d in range(c+1, n):
					pay, por = (0, 0)
					pa, po = array_possibles[a]
					pay += pa
					por += po
					pa, po = array_possibles[b]
					pay += pa
					por += po
					possibles[((pay, por))] = True
					pa, po = array_possibles[c]
					pay += pa
					por += po
					pa, po = array_possibles[d]
					pay += pa
					por += po
					possibles[((pay, por))] = True
	for pa in range(0, 65):
		for po in range(0, 65-pa):
			print("%d\t%d\t" % (pa, po), end="")
			if (pa, po) in possibles:
				print("ok", end="")
			print("")

def algo():

	global cache, global_smallest, global_biggest

	"""
	for n_pay in range(0, 16):
		for n_por in range(0, 16 - n_pay):
			li = find_arrangements(PaysagePage, 1.0, n_pay, n_por)
			if li:
				print("%2dx%2d: %d results" % (n_pay, n_por, len(li)))

	return
	"""

	n_pay = 10
	n_por = 3

	global_smallest = 1.0 / 2 / (n_pay + n_por)
	global_biggest = 1.0 * 2 / (n_pay + n_por)

	li = find_arrangements(PaysagePage, 1.0, n_pay, n_por)

	if not li:
		for a in cache:
			print("%d\t%d" % (a&0xff, (a>>8)&0xff))
		print("no result")
		return

	best_lower_scale = 0.0
	worst_lower_scale = 1.0
	for l in li:
		if l.lower_scale() > best_lower_scale:
			best_lower_scale = l.lower_scale()
			best = l
		if l.lower_scale() < worst_lower_scale:
			worst_lower_scale = l.lower_scale()
			worst = l

	print("Printing one of the worst arrangement :")
	print(worst)
	print("scale range [%.2f, %.2f]" % (worst.lower_scale(), worst.bigger_scale()))

	print("Printing one of the best arrangement :")
	print(best)
	print("scale range [%.2f, %.2f]" % (best.lower_scale(), best.bigger_scale()))

	w = 400
	h = 300
	bg = Color("white")
	img = Image(width=w, height=h, background=bg)
	best.draw_borders(img, w, h, 0, 0)
	img.save(filename="borders.jpg")

def main():

	algo()

	return

	parser = argparse.ArgumentParser(description='Robot to post ads on Kijiji.')
	parser.add_argument('d', metavar='WIDTHxHEIGHT', help='images to join with the ad')
	parser.add_argument('o', metavar='OUTPUT', help='images to join with the ad')
	parser.add_argument('i', metavar='IMG.JPG', help='file containing the POST vars', nargs='+')

	args = parser.parse_args()

	w, h = args.d.split("x")
	w = int(w)
	h = int(h)

	filelist = args.i
	imglist = []

	for filename in filelist:
		ai = AlbumImage(filename)
		imglist.append(ai)

	random.shuffle(imglist)

	img = mkalbum(w, h, imglist)

	img.save(filename=args.o)

	return

	"""photos = []

	#if len(args.i) > 4:
	#	raise Exception("too many images")

	for imgfile in args.i:
		#try:
		with Image(filename=imgfile) as img:
			ratio = img.width / img.height
			photos.append({ 'filename': imgfile, 'ratio': ratio })
		#except wand.exceptions.MissingDelegateError:
		#	pass
	"""

	"""
	no_paysage = 0
	no_portrait = 0
	for photo in photos:
		if photo["ratio"] > 1:
			no_paysage += 1
		else:
			print(photo["ratio"])
			print(photo)
			no_portrait += 1
		#print(photo)
	print("%d paysages, %d portrait" % (no_paysage, no_portrait))
	"""

#	imglist = []
#	for p in photos:
#		imglist.append(p["filename"])
	#compose("vert6.jpg", 1800, 1200, ["verticales/20120916_122654.jpg", "verticales/IMG_0049.JPG"])

	recto = imglist[:int(len(imglist)/2)]
	verso = imglist[int(len(imglist)/2):]
	print("len(recto) = %d" % len(recto))

	t1 = recto[:int(len(recto)/3)]
	t2 = recto[int(len(recto)/3):int(2*len(recto)/3)]
	t3 = recto[int(2*len(recto)/3):]
	print("len t1 = %d" % len(t1))
	print("len t2 = %d" % len(t2))
	print("len t3 = %d" % len(t3))
	compose("/tmp/recto-t1.jpg", int(canvassize[0]/3), canvassize[1], t1)
	compose("/tmp/recto-t2.jpg", int(canvassize[0]/3), canvassize[1], t2)
	compose("/tmp/recto-t3.jpg", int(canvassize[0]/3), canvassize[1], t3)

	canvas = Image(width=canvassize[0], height=canvassize[1])
	t1 = Image(filename="/tmp/recto-t1.jpg")
	canvas.composite(t1, left=0, top=0)
	t2 = Image(filename="/tmp/recto-t2.jpg")
	canvas.composite(t2, left=int(canvassize[0]/3), top=0)
	t3 = Image(filename="/tmp/recto-t3.jpg")
	canvas.composite(t3, left=int(2*canvassize[0]/3), top=0)
	canvas.save(filename="recto.jpg")

	print("len(verso) = %d" % len(recto))

	t1 = verso[:int(len(verso)/3)]
	t2 = verso[int(len(verso)/3):int(2*len(verso)/3)]
	t3 = verso[int(2*len(verso)/3):]
	print("len t1 = %d" % len(t1))
	print("len t2 = %d" % len(t2))
	print("len t3 = %d" % len(t3))
	compose("/tmp/verso-t1.jpg", int(canvassize[0]/3), canvassize[1], t1)
	compose("/tmp/verso-t2.jpg", int(canvassize[0]/3), canvassize[1], t2)
	compose("/tmp/verso-t3.jpg", int(canvassize[0]/3), canvassize[1], t3)

	canvas = Image(width=canvassize[0], height=canvassize[1])
	t1 = Image(filename="/tmp/verso-t1.jpg")
	canvas.composite(t1, left=0, top=0)
	t2 = Image(filename="/tmp/verso-t2.jpg")
	canvas.composite(t2, left=int(canvassize[0]/3), top=0)
	t3 = Image(filename="/tmp/verso-t3.jpg")
	canvas.composite(t3, left=int(2*canvassize[0]/3), top=0)
	canvas.save(filename="verso.jpg")

	#compose(args.o, canvassize[0], canvassize[1], ["/tmp/recto.jpg", "/tmp/verso.jpg"])

if __name__ == "__main__":
	main()
