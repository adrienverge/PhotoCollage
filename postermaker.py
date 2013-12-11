#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Adrien Vergé

__author__ = "Adrien Vergé"
__copyright__ = "Copyright 2013, Adrien Vergé"
__license__ = "GPL"
__version__ = "1.0"

import random
from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image
import wand.exceptions

class Photo:

	def __init__(self, w, h):
		self.w = w
		self.h = h

	def draw_borders(self, img, w, h, x, y):
		pass

	def smaller_photo(self, w, h):
		return w * h

class HPhoto(Photo): # [ ]

	def __str__(self):
		return "Horizontal Photo"

	def flip(self):
		return VPhoto(self.h, self.w)

class VPhoto(Photo): # []

	def __str__(self):
		return "Vertical Photo"

	def flip(self):
		return HPhoto(self.h, self.w)

"""
class Canvas:

	def __init__(self, w, h, content=None):
		self.w = w
		self.h = h
		self.content = content

	def __str__(self):
		return str(self.content)

	def draw_borders(self, img, w, h, x, y):
		self.content.draw_borders( img, w, h, x, y)

	def smaller_photo(self):
		return self.content.smaller_photo()
"""

class Split:

	def __init__(self, splitoffset, k0=None, k1=None):
		self.splitoffset = splitoffset
		self.kids = [k0, k1]

	def add_kids(self, k0, k1):
		self.kids = [k0, k1]

	def __str__(self):
		s = ""
		pre = "\n "
		for line in str(self.kids[0]).split("\n"):
			s += pre + line
		for line in str(self.kids[1]).split("\n"):
			s += pre + line
		return s

class HSplit(Split): # |

	def __str__(self):
		return "-- HSplit --" + super(self.__class__, self).__str__()

	def draw_borders(self, img, w, h, x, y):
		w0 = w * self.splitoffset
		w1 = w * (1 - self.splitoffset)
		self.kids[0].draw_borders(img, w0, h, x, y)
		self.kids[1].draw_borders(img, w1, h, x + w0, y)
		with Drawing() as draw:
			draw.line((x + w0, y), (x + w0, y + h))
			draw(img)

	def flip(self):
		return VSplit(self.splitoffset, self.kids[0].flip(), self.kids[1].flip())

	def smaller_photo(self, w, h):
		w0 = w * self.splitoffset
		w1 = w * (1 - self.splitoffset)
		size0 = self.kids[0].smaller_photo(w0, h)
		size1 = self.kids[1].smaller_photo(w1, h)
		if size0 < size1:
			return size0
		return size1

class VSplit(Split): # -

	def __str__(self):
		return "-- VSplit --" + super(self.__class__, self).__str__()

	def draw_borders(self, img, w, h, x, y):
		h0 = h * self.splitoffset
		h1 = h * (1 - self.splitoffset)
		self.kids[0].draw_borders(img, w, h0, x, y)
		self.kids[1].draw_borders(img, w, h1, x, y + h0)
		with Drawing() as draw:
			draw.line((x, y + h0), (x + w, y + h0))
			draw(img)

	def flip(self):
		return HSplit(self.splitoffset, self.kids[0].flip(), self.kids[1].flip())

	def smaller_photo(self, w, h):
		h0 = h * self.splitoffset
		h1 = h * (1 - self.splitoffset)
		size0 = self.kids[0].smaller_photo(w, h0)
		size1 = self.kids[1].smaller_photo(w, h1)
		if size0 < size1:
			return size0
		return size1

cache = {}

"""
cache[ (2,2) ] = {
	(4,0): HSplit(),
	(2,1): HSplit(),
	(0,2): VSplit()
}
"""

def find_hcanvas_arrangements(w, h):

	global cache

	if (w, h) in cache:
		return cache[(w, h)]

	ret = {}

	if w == h:
		ret[(1, 0)] = HPhoto(w, h)
	elif 2 * w == h:
		ret[(0, 1)] = VPhoto(w, h)

	for i in range(1, w):
		p0 = find_hcanvas_arrangements(i, h)
		p1 = find_hcanvas_arrangements(w - i, h)
		for (h0, v0) in p0:
			for (h1, v1) in p1:
				if (h0+v0) >= (h1+v1)/3.0 and (h0+v0)/3.0 <= (h1+v1):
					newkey = (h0+h1, v0+v1)
					new = HSplit(float(i/w), p0[(h0, v0)], p1[(h1, v1)])
					#
					# TODO: random here to replace, sometimes
					#
					if (not newkey in ret) or \
					   new.smaller_photo(1, 1) > ret[newkey].smaller_photo(1, 1) or \
					   (new.smaller_photo(1, 1) == ret[newkey].smaller_photo(1, 1) and \
					    random.choice((True, False))):
						ret[newkey] = new

	for i in range(1, h):
		p0 = find_hcanvas_arrangements(w, i)
		p1 = find_hcanvas_arrangements(w, h - i)
		for (h0, v0) in p0:
			for (h1, v1) in p1:
				if (h0+v0) >= (h1+v1)/3.0 and (h0+v0)/3.0 <= (h1+v1):
					newkey = (h0+h1, v0+v1)
					new = VSplit(float(i/h), p0[(h0, v0)], p1[(h1, v1)])
					if (not newkey in ret) or \
					   new.smaller_photo(1, 1) > ret[newkey].smaller_photo(1, 1) or \
					   (new.smaller_photo(1, 1) == ret[newkey].smaller_photo(1, 1) and \
					    random.choice((True, False))):
						ret[newkey] = new

	cache[(w, h)] = ret

	return ret

def combine_arrangements(pay_list):
	"""
	-------      -------            -------------
	|     |      |  |  |            |     |  |  |
	|-----|   +  |  |--|  ->  flip( |-----|  |--| )
	|  |  |      |  |  |            |  |  |  |  |
	-------      -------            -------------
	"""
	tmp = {}
	for (hor0, ver0) in pay_list:
		canvas0 = pay_list[(hor0, ver0)].flip()
		#
		# TODO: ne pas itérer sur les mêmes objets plusieurs fois
		#
		for (hor1, ver1) in pay_list:
			canvas1 = pay_list[(hor1, ver1)].flip()
			newkey = (ver0 + ver1, hor0 + hor1)
			new = HSplit(0.5, canvas0, canvas1)
			if not newkey in tmp or \
			   new.smaller_photo(297, 210) > tmp[newkey].smaller_photo(297, 210) or \
			   (new.smaller_photo(297, 210) == tmp[newkey].smaller_photo(297, 210) and \
				random.choice((True, False))):
				tmp[newkey] = new
	pay_list.update(tmp)

	return pay_list

def get_arrangement(n_pay, n_por):

	# Find arrangements for 'paysage' pages
	pay_list = {}
	pay_list.update(find_hcanvas_arrangements(2, 2))
	pay_list.update(find_hcanvas_arrangements(3, 3))
	pay_list.update(find_hcanvas_arrangements(4, 4))

	timeout = 2
	while (n_pay, n_por) not in pay_list and \
	      (n_por, n_pay) not in pay_list and timeout > 0:
		pay_list = combine_arrangements(pay_list)
		timeout -= 1

	# Find arrangements for 'portrait' pages by symmetry
	por_list = {}
	for (hor, ver) in pay_list:
		por_list[(ver, hor)] = pay_list[(hor, ver)].flip()

	if (n_pay, n_por) in pay_list and (n_pay, n_por) in por_list:
		a_pay = pay_list[(n_pay, n_por)]
		a_por = por_list[(n_pay, n_por)]
		print("in both")
		print(a_pay.smaller_photo(297, 210))
		print(a_por.smaller_photo(210, 297))
		if a_pay.smaller_photo(297, 210) > a_por.smaller_photo(210, 297):
			a_pay.orientation = "paysage"
			return a_pay
		else:
			a_por.orientation = "portrait"
			return a_por
	if (n_pay, n_por) in pay_list:
		ret = pay_list[(n_pay, n_por)]
		ret.orientation = "paysage"
		return ret
	if (n_pay, n_por) in por_list:
		ret = por_list[(n_pay, n_por)]
		ret.orientation = "portrait"
		return ret

	return None

def preview_borders(arrangement, filename, w, h):
	img = Image(width=w, height=h, background=Color("white"))
	arrangement.draw_borders(img, w, h, 0, 0)
	img.save(filename=filename)

def main():

	# Find arrangements for 'paysage' pages
	pay_list = {}
	pay_list.update(find_hcanvas_arrangements(2, 2))
	pay_list.update(find_hcanvas_arrangements(3, 3))
	pay_list.update(find_hcanvas_arrangements(4, 4))

	pay_list = combine_arrangements(pay_list)

	# Find arrangements for 'portrait' pages by symmetry
	por_list = {}
	for (hor, ver) in pay_list:
		por_list[(ver, hor)] = pay_list[(hor, ver)].flip()

	N = 16
	print("    0 1 2 3 4 5 6 7 8 9 10  12  14  16")
	for x in range(0, N+1):
		print("%2d  " % x, end="")
		for y in range(0, N+1):
			if (x, y) in pay_list:
				print("x ", end="")
				w = 297
				h = 210
				img = Image(width=w, height=h, background=Color("white"))
				pay_list[(x, y)].draw_borders(img, w, h, 0, 0)
				img.save(filename="borders-paysage-%d-%d.pgm" % (x, y))
			elif (x, y) in por_list:
				print("+ ", end="")
				w = 210
				h = 297
				img = Image(width=w, height=h, background=Color("white"))
				por_list[(x, y)].draw_borders(img, w, h, 0, 0)
				img.save(filename="borders-portrait-%d-%d.png" % (x, y))
			else:
				print("  ", end="")
		print("")

if __name__ == "__main__":
	main()
