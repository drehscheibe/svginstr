#!python

import sys
import gzip
import string
from math import ceil, sin, cos, tan, pi, sqrt
from random import random

__author__ = "Melchior FRANZ < mfranz # aon : at >"
__url__ = "http://github.com/drehscheibe/svginstr/"
__version__ = "0.3"
__license__ = "GPL v2"
__doc__ = """
"""



class Error(Exception):
	pass



class Global:
	indent = '\t'
	transforms = {}
	attributes = {  # use underscore instead of hyphen!
		'color': 'white',
		'fill': 'white',
		'font_family': 'Helvetica',
		'font_size': 11,
		'text_anchor': 'middle',
	}



def set_global_attributes(**args):
	for key, value in list(args.items()):
		if value is None:
			if key in Global.attributes:
				del(Global.attributes[key])
		else:
			Global.attributes[key] = value



class XML:
	def __init__(self, filename, indent = '\t', compress = False):
		self.indent = indent
		self.level = 0
		self.file = None
		try:
			if compress:
				self.file = gzip.GzipFile(filename, "w")
			else:
				self.file = open(filename, "w")

		except IOError as error:
			raise Error("Error: XML.__init__(): " + str(error))

	def __del__(self):
		try:
			if self.file:
				self.file.close()

		except IOError as error:
			raise Error("Error: XML.__del__(): " + str(error))

	def write(self, s = ''):
		try:
			s = s.strip()
			if not s:
				self.file.write('\n')
				return

			if s.startswith('<?') or s.startswith('<!'):
				self.file.write(s + '\n')
				return

			if s.startswith('</'):
				self.level -= 1

			self.file.write(self.level * self.indent + s + '\n')

			if s.startswith('<'):
				if s.find('</') > 0:
					return
				if not s.startswith('</') and not s.endswith('/>'):
					self.level += 1

		except IOError as error:
			raise Error("Error: XML.write(): " + str(error))



class Matrix:
	def __init__(self, a = 1, b = 0, c = 0, d = 1, e = 0, f = 0):
		self.a, self.b, self.c, self.d, self.e, self.f = a, b, c, d, e, f

	def __str__(self):
		return "[Matrix %f %f %f %f %f %f]" % (self.a, self.b, self.c, self.d, self.e, self.f)

	def __cmp__(self, m):
		return cmp((self.a, self.b, self.c, self.d, self.e, self.f), \
				(m.a, m.b, m.c, m.d, m.e, m.f))

	def __bool__(self):
		return (self.a, self.b, self.c, self.d, self.e, self.f) != (1, 0, 0, 1, 0, 0)

	def copy(self):
		return Matrix(self.a, self.b, self.c, self.d, self.e, self.f)

	def transform(self, u, v):
		return u * self.a + v * self.c + self.e, u * self.b + v * self.d + self.f

	def multiply(self, m):
		a = m.a * self.a + m.c * self.b
		b = m.b * self.a + m.d * self.b
		c = m.a * self.c + m.c * self.d
		d = m.b * self.c + m.d * self.d
		e = m.a * self.e + m.c * self.f + m.e
		f = m.b * self.e + m.d * self.f + m.f
		self.a, self.b, self.c, self.d, self.e, self.f = a, b, c, d, e, f
		return self

	def invert(self):
		det = (self.a * self.d - self.b * self.c)
		if det == 0.0:
			raise ValueError("Matrix not invertible")
		idet = 1.0 / det
		a = idet * self.d
		b = idet * -self.b
		c = idet * -self.c
		d = idet * self.a
		e = idet * (self.f * self.c - self.d * self.e)
		f = idet * (self.b * self.e - self.f * self.a)
		self.a, self.b, self.c, self.d, self.e, self.f = a, b, c, d, e, f
		return self

	def translate(self, dx, dy):
		return self.multiply(Matrix(1, 0, 0, 1, dx, dy))

	def scale(self, sx, sy = None):
		if sy == None:
			sy = sx
		return self.multiply(Matrix(sx, 0, 0, sy, 0, 0))

	def rotate(self, a):
		a = float(a) * pi / 180.0
		return self.multiply(Matrix(cos(a), sin(a), -sin(a), cos(a), 0, 0))

	def skewX(self, a):
		a = float(a) * pi / 180.0
		return self.multiply(Matrix(1, 0, tan(a), 1, 0, 0))

	def skewY(self, a):
		a = float(a) * pi / 180.0
		return self.multiply(Matrix(1, tan(a), 0, 1, 0, 0))



class Path:
	def __init__(self, x = None, y = None):
		self.x = x or 0
		self.y = y or 0
		self.points = []
		self.lines = []
		self.absolute = True
		self.path = ""

		if x != None and y != None:
			self.moveto(x, y)

		self.absolute = False

	def __str__(self):
		return self.path

	def _assert_multi_args(self, args, num):
		if len(args) % num:
			raise Error("Path: incomplete argument list")

	def _update(self, x, y):
		if self.absolute:
			self.x = x
			self.y = y
		else:
			self.x += x
			self.y += y

	def abs(self):
		self.absolute = True
		return self

	def rel(self):
		self.absolute = False
		return self

	def moveto(self, x, y):
		self.path += " %s %s %s" % (['m', 'M'][self.absolute], x, y)
		self._update(x, y)
		self.points.append((self.x, self.y))
		return self

	def moveto_polar(self, angle, radius):
		x, y = radius * sind(angle), radius * cosd(angle)
		self.path += " %s %s %s" % (['m', 'M'][self.absolute], x, y)
		self._update(x, y)
		self.points.append((self.x, self.y))
		return self

	def lineto(self, *args):
		self._assert_multi_args(args, 2)
		while args:
			x, y = args[0], args[1]
			args = args[2:]
			self.path += " %s %s %s" % (['l', 'L'][self.absolute], x, y)
			self._update(x, y)
			self.points.append((self.x, self.y))
		return self

	def lineto_polar(self, *args):
		self._assert_multi_args(args, 2)
		while args:
			angle, radius, args = args[0], args[1], args[2:]
			x, y = radius * sind(angle), radius * cosd(angle)
			self.path += " %s %s %s" % (['l', 'L'][self.absolute], x, y)
			self._update(x, y)
			self.points.append((self.x, self.y))
		return self

	def close(self):
		self.path += " z"
		return self

	def cubic_bezier(self, x1, y1, x2, y2, x, y):
		self.path += " %s %s %s %s %s %s %s" % (['c', 'C'][self.absolute], x1, y1, x2, y2, x, y)
		self._update(x, y)
		self.points.append((self.x, self.y))
		#self.points.append((x1, y1))
		#self.points.append((x2, y2))
		#self.lines.append((x1, y1, x2, y2), (x2, y2, x, y))
		return self

	def smooth_cubic_bezier(self, x2, y2, x, y):
		self.path += " %s %s %s %s %s %s %s" % (['s', 'S'][self.absolute], x2, y2, x, y)
		self._update(x, y)
		self.points.append((self.x, self.y))
		#self.points.append((x, y))
		#self.points.append((x2, y2))
		return self

	def quad_bezier(selfs, x1, y1, x, y):
		self.path += " %s %s %s %s %s" % (['q', 'Q'][self.absolute], x1, y1, x, y)
		self._update(x, y)
		self.points.append((self.x, self.y))
		#self.points.append((x1, y1))
		#self.points.append((x, y))
		return self

	def smooth_quad_bezier(self, x, y):
		self.path += " %s %s %s" % (['t', 'T'][self.absolute], x, y)
		self._update(x, y)
		self.points.append((self.x, self.y))
		return self

	def arc(self, rx, ry, rot, large, sweep, x, y):
		self.path += " %s %s, %s %s %s, %s %s, %s" % (['a', 'A'][self.absolute], rx, ry, rot, large, sweep, x, y)
		self._update(x, y)
		self.points.append((self.x, self.y))
		return self

	def right(self, dx):
		self.path += " h %s" % dx
		self.x += dx
		self.points.append((self.x, self.y))
		return self

	def left(self, dx):
		return self.right(-dx)

	def down(self, dy):
		self.path += " v %s" % dy
		self.y += dy
		self.points.append((self.x, self.y))
		return self

	def up(self, dy):
		return self.down(-dy)

	def debug(self, instr):
		print(self.points)
		print(self.lines)
		for l in self.lines:
			instr.write('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke-width="%s" stroke="%s"/>' \
					% (l[0], l[1], l[2], l[3], instr.unit * 0.5, 'white'))
		for p in self.points:
			instr.write('<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % (p[0], p[1], 0.75 * instr.unit, 'green'))



class Gradient:
	counter = 0

	def __init__(self):
		self.stops = []
		Gradient.counter += 1
		self.name = "gradient%d" % Gradient.counter

	def stop(self, offset, red, green = None, blue = None, alpha = 1):
		if green == None:
			green = red
		if blue == None:
			blue = green
		self.stops.append((offset, red, green, blue, alpha))
		return self

	def code(self):
		return ['<stop offset="%s" style="stop-color:rgb(%s, %s, %s); stop-opacity:%s"/>' \
				% b for b in self.stops]



class LinearGradient(Gradient):
	def __init__(self, x1 = "0%", y1 = "0%", x2 = "100%", y2 = "100%"):
		Gradient.__init__(self)
		self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2

	def copy(self):
		c = LinearGradient(self.x1, self.y1, self.x2, self.y2)
		c.stops = self.stops[:]
		return c

	def code(self):
		return ['<linearGradient id="%s" x1="%s" y1="%s" x2="%s" y2="%s">' \
				% (self.name, self.x1, self.y1, self.x2, self.y2)] \
				+ Gradient.code(self) + ["</linearGradient>"]



class RadialGradient(Gradient):
	def __init__(self, cx = "50%", cy = "50%", r = "50%", fx = None, fy = None):
		Gradient.__init__(self)
		if fx == None:
			fx = cx
		if fy == None:
			fy = cy
		self.cx, self.cy, self.r, self.fx, self.fy = cx, cy, r, fx, fy

	def copy(self):
		c = RadialGradient(self.cx, self.cy, self.r, self.fx, self.fy)
		c.stops = self.stops[:]
		return c

	def code(self):
		return ['<radialGradient id="%s" cx="%s" cy="%s" r="%s" fx="%s" fy="%s">' \
				% (self.name, self.cx, self.cy, self.r, self.fx, self.fy)] \
				+ Gradient.code(self) + ["</radialGradient>"]



class Instrument:
	def __init__(self, filename, w, h = None, title = None, **args):
		self.basename = ".".split(filename)[0]
		self.indent = 0
		self.x = 0
		self.y = 0
		self.w = w
		self.h = h or w
		self._title = title
		self._desc = title
		self.defs = []
		self.trans = []
		self.contents = []
		self.unit = 0.01
		self.matrix = None

		if w > h: # width/height in internal coords  (min(w, h) -> 200)
			self.W, self.H = 200.0 * w / h, 200.0
		else:
			self.W, self.H = 200.0, 200.0 * h / w

		if w != h:
			print('internal coordinate system: x = [-%s, +%s],  y = [-%s, +%s]' \
					% (R(self.W * 0.5), R(self.W * 0.5), R(self.H * 0.5), R(self.H * 0.5)))

		# matrix that transforms from internal svginstr coords to UV coords
		self.matrix_stack = [Matrix().translate(-0.5, -0.5).scale(self.W, -self.H).invert()]

		self.file = None
		self.file = XML(filename, Global.indent, filename.endswith(".svgz") or \
				filename.endswith(".svg.gz"))
		self.file.write('<?xml version="1.0" standalone="no"?>')
		self.file.write('<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '\
				'"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">')
		self.file.write()
		self.file.write('<svg width="%spx" height="%spx" viewBox="%s %s %s %s" '\
				'xmlns="http://www.w3.org/2000/svg" '\
				'xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1">' \
				% (R(self.w), R(self.h), 0, 0, R(self.W), R(self.H)))

		attributes = Global.attributes.copy()
		attributes.update(args)
		self.write('<g transform="translate(%s, %s)"%s>' \
				% (R(self.W * 0.5), R(self.H * 0.5), self._args_string(attributes)))
		self.write('<rect x="%s" y="%s" width="%s" height="%s" stroke="none" fill="none"/>' \
				% (R(self.W * -0.5), R(self.H * -0.5), R(self.W), R(self.H)))
		self.reset()


	def __del__(self):
		if self.file:
			if self._title:
				self.file.write('<title>%s</title>' % self._title)
			if self._desc:
				self.file.write('<desc>%s</desc>' % self._desc)
			if self.defs:
				self.file.write('<defs>')
				for d in self.defs:
					for i in d.code():
						self.file.write(i)
				self.file.write('</defs>')

			for i in self.contents:
				self.file.write(i)

			self.file.write('</g>')
			self.file.write('</svg>\n')
			del self.file


	# general methods
	def write(self, s = ""):
		self.contents.append(s)

	def title(self, s):
		self._title = s

	def description(self, s):
		self._desc = s

	def fg_size(self, w, h):
		self.fgpanel = FGPanel(self.basename, w, h)
		return self

	def begin(self, name = None, **args):
		if name:
			args["id"] = name

		attr = self._args_string(args)
		if self.trans:
			t = self.trans[:]
			t.reverse()
			attr += ' transform="%s"' % "".join(t)

		self.write('<g%s>' % attr)

		self.matrix_stack.append(self.matrix.multiply(self.matrix_stack[-1]))

		x, y = self.matrix_stack[-1].copy().invert().transform(0, 1) # FIXME square
		self.unit = 0.01 * sqrt(x * x + y * y)

		self.reset()
		return True

	def end(self):
		self.write('</g>')
		self.matrix_stack.pop()
		self.reset()

	def angle(self, alpha):
		return alpha - 90

	def reset(self):
		self.at_origin()
		self.styles = []
		self.trans = []
		self.matrix = Matrix()

	def _attrib(self, args):
		return self._style() + self._trans() + self._args_string(args)

	def _args_string(self, dic):
		""" turn dictionary into joined string of ' key="value"' """
		s = ""
		for key in sorted(dic.keys()):
			s += ' %s="%s"' % (key.replace('_', '-'), dic[key])
		return s

	def _map_args(self, dic, **args):
		for k, v in list(args.items()):
			if v != None:
				dic[k] = v


	# positioning methods
	def at_origin(self):
		self.x = self.y = 0
		return self

	def at(self, x, y):
		return self.at_origin().offset(x, y)

	def at_polar(self, angle, radius):
		return self.at_origin().polar_offset(angle, radius)

	def offset(self, x, y):
		self.x += x
		self.y += y
		return self

	def polar_offset(self, angle, radius):
		""" first choose the azimuth (angle), then go the distance (radius)! """
		a = self.angle(angle)
		self.x, self.y = radius * cosd(a), radius * sind(a)
		return self


	# style methods
	def _style(self):
		""" return assembled style """
		if self.styles:
			return " style=\"%s\"" % "; ".join(self.styles)
		else:
			return ""

	def style(self, s):
		self.styles.append(s)
		return self

	def gradient(self, g, name = None):
		self.defs.append(g)
		return self.style("fill:url(#%s)" % (name or g.name))


	# transform methods
	def _trans(self):
		""" return assembled transformation """
		if self.trans:
			return " transform=\"%s\"" % " ".join(self.trans)
		else:
			return ""

	def save_matrix(self, name):
		Global.transforms[name] = (self.matrix, self.trans)
		self.matrix = Matrix()
		self.trans = []

	def use_matrix(self, name):
		if name not in Global.transforms:
			raise Error("use_matrix: undefined matrix '%s'" % name)

		self.matrix.multiply(Global.transforms[name][0])
		for t in Global.transforms[name][1]:
			self.trans.append(t)
		return self

	def translate(self, x, y = None):
		if y == None:
			y = 0
		self.trans.append("translate(%s, %s)" % (x, y))
		self.matrix.translate(x, y)
		return self

	def rotate(self, a, x = None, y = None):
		if x == None and y == None:
			self.trans.append("rotate(%s)" % a)
			self.matrix.rotate(a)
		else:
			self.trans.append("rotate(%s, %s, %s)" % (a, x, y))
			self.matrix.translate(-x, -y).rotate(a).translate(x, y)
		return self

	def scale(self, x, y = None):
		if y == None:
			y = x
		self.trans.append("scale(%s, %s)" % (x, y))
		self.matrix.scale(x, y)
		return self

	def xscale(self, x):
		self.trans.append("scale(%s, 1)" % x)
		self.matrix.scale(x, 1)
		return self

	def yscale(self, y):
		self.trans.append("scale(1, %s)" % y)
		self.matrix.scale(1, y)
		return self

	def xskew(self, a):
		self.trans.append("skewX(%s)" % a)
		self.matrix.skewX(a)
		return self

	def yskew(self, a):
		self.trans.append("skewY(%s)" % a)
		self.matrix.skewY(a)
		return self

	def matrix(self, a, b, c, d, e, f):
		self.trans.append("matrix(%s, %s, %s, %s, %s, %s)" % (a, b, c, d, e, f))
		self.matrix.multiply(Matrix(a, b, c, d, e, f))
		return self

	def region(self, x, y, w, h, clip = 1, name = None):
		uv_matrix = self.matrix.copy().multiply(self.matrix_stack[-1])
		self.fgpanel.add(name, uv_matrix, x, y, w, h)
		W = max(w, h)
		return self.scale(W / 200.0).translate(x + w * 0.5, y + h * 0.5)


	# drawing primitives
	def circle(self, radius, width, color = Global.attributes['color'], **args):
		self._map_args(args, stroke = color)
		self.write('<circle cx="%s" cy="%s" r="%s" fill="none" stroke-width="%s"%s/>' \
				% (self.x, self.y, R(radius), R(width), self._attrib(args)))
		self.reset()

	def disc(self, radius, color = None, **args):
		self._map_args(args, fill = color)
		self.write('<circle cx="%s" cy="%s" r="%s"%s/>' \
				% (self.x, self.y, R(radius), self._attrib(args)))
		self.reset()

	def square(self, width, color = None, **args):
		self._map_args(args, fill = color)
		self.write('<rect x="%s" y="%s" width="%s" height="%s"%s/>' \
				% (self.x - 0.5 * width, self.y - 0.5 * width, R(width), R(width), \
				self._attrib(args)))
		self.reset()

	def rectangle(self, width, height, color = None, **args):
		self._map_args(args, fill = color)
		self.write('<rect x="%s" y="%s" width="%s" height="%s"%s/>' \
				% (self.x - 0.5 * width, self.y - 0.5 * height, R(width), R(height), \
				self._attrib(args)))
		self.reset()

	def shape(self, path, **args):
		self.write('<path d="%s"%s/>' % (str(path), self._attrib(args)))
		self.reset()

	def text(self, text, size = None, color = None, **args):
		self._map_args(args, font_size = size, fill = color)
		self.write('<text x="%s" y="%s"%s>%s</text>' \
				% (self.x, self.y, self._attrib(args), text))
		self.reset()

	def arc(self, begin, end, radius, width = None, color = None, **args):
		self._map_args(args, stroke = color, stroke_width = width)
		begin = self.angle(begin)
		end = self.angle(end)
		b = min(begin, end)
		e = max(begin, end) - b
		r = radius or 10e-10

		self.rotate(R(b))
		if self.x != 0 or self.y != 0:
			self.translate(self.x, self.y)
		self.begin()
		self.write('<path d="M%s,0 A%s,%s %s %d,1 %s,%s" fill="none"%s/>' \
				% (r, r, r, e / 2, (e >= 180), R(r * cosd(e)), R(r * sind(e)),
				self._attrib(args)))
		self.end()
		self.reset()

	def line(self, x1, y1, x2, y2, width = None, color = Global.attributes['color'], **args):
		self._map_args(args, stroke_width = width, stroke = color)
		self.write('<line x1="%s" y1="%s" x2="%s" y2="%s"%s/>' \
				% (x1, y1, x2, y2, self._attrib(args)))
		self.reset()

	def tick(self, alpha, inner, outer, width = None, color = Global.attributes['color'], **args):
		self._map_args(args, stroke_width = width, stroke = color)
		a = self.angle(alpha)
		self.write('<line x1="%s" y1="%s" x2="%s" y2="%s"%s/>' \
				% (self.x + inner * cosd(a), self.y + inner * sind(a), \
				self.x + outer * cosd(a), self.y + outer * sind(a), \
				self._attrib(args)))
		self.reset()

	def arctext(self, startangle, radius, text, size = None, color = None, **args):
		self._map_args(args, font_size = size, fill = color, text_anchor = 'start')
		r = R(radius)
		self.write('<g transform="rotate(%s)">' % startangle)
		self.write('<defs>')
		self.write('<path id="arctext" d="M0,-%s A%s,%s 0 0,1 0,%s"/>' % (r, r, r, r))
		self.write('</defs>')
		self.write('<text%s>' % self._attrib(args))
		self.write('<textPath xlink:href="#arctext">%s</textPath>' % text)
		self.write('</text>')
		self.write('</g>')
		self.reset()

	def chequer(self, size = 10, color = "lightgrey"):
		for y in range(20):
			for x in range(20):
				if (x + y) & 1:
					continue
				self.write('<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' \
						% (R(size * x - 100), R(size * y - 100), R(size), R(size), color))
		self.reset()

	def screw(self, scale, rotation = None):
		if rotation == None:
			rotation = random() * 180

		hole = RadialGradient()
		hole.stop("0%", 0, alpha = 1)
		hole.stop("30%", 0, alpha = 1)
		hole.stop("61%", 0, alpha = 0)

		head = RadialGradient("50%", "50%", "70%", "0%", "0%")
		head.stop("0%", 60)
		head.stop("90%", 25)
		head.stop("100%", 10)

		if self.scale(scale).translate(self.x, self.y).begin():
			self.gradient(hole).disc(100)
			self.gradient(head).disc(50)
			if self.rotate(rotation).begin():
				self.rectangle(100, 19, color = "#1a1a1a")
				self.end()
			self.end()

	def xml(self, name):
		return _xml(self, name)



class _xml(XML):
	def __init__(self, parent, filename):
		if not isinstance(parent, Instrument):
			self.instrument = None
			raise ValueError("_xml is only available as method of instrument")
		self.instrument = parent

		XML.__init__(self, filename + ".xml", Global.indent)
		self.write('<?xml version="1.0"?>')
		self.write()
		self.write('<PropertyList>')
		self.write('<path>%s.ac</path>' % filename)

	def __del__(self):
		self.write("</PropertyList>")
		XML.__del__(self)

	def animation(self, objname, prop, points):
		self.write('<animation>')
		self.write('<type>rotate</type>')
		self.write('<object-name>%s</object-name>' % objname)
		self.write('<property>%s</property>' % prop)
		self.write('<interpolation>')
		for p in points:
			self.write('<entry><ind>%s</ind><dep>%s</dep></entry>' \
				% (R(p), R(self.instrument.angle(p))))
		self.write('</interpolation>')
		self.write('<axis>')
		self.write('<x>-1</x>')
		self.write('<y>0</y>')
		self.write('<z>0</z>')
		self.write('</axis>')
		self.write('</animation>')



class FGPanel:
	def __init__(self, name, w, h):
		self.data = []
		self.name = name
		self.W = w
		self.H = h
		self.f = XML(self.name + "-panel.xml", Global.indent)

	def add(self, name, matrix, x, y, w, h):
		self.data.append((name or "NoName", matrix, x, y, w, h))

	def __del__(self):
		self.f.write('<?xml version="1.0"?>')
		self.f.write()
		self.f.write('<PropertyList>')
		self.f.write('<name>%s</name>' % self.name)
		self.f.write('<w-base>%s</w-base>' % self.W)
		self.f.write('<h-base>%s</h-base>' % self.W)
		self.f.write()
		self.f.write('<layers>')
		for i in self.data:
			name, matrix, x, y, w, h = i
			p1 = matrix.transform(x, y + h)
			p2 = matrix.transform(x + w, y)
			s = matrix.transform(w - 100, 100 - h)
			self.f.write('<name>%s</name>' % name)
			self.f.write('<layer>')
			self.f.write('<w>%s</w>' % R(self.W * s[0]))
			self.f.write('<h>%s</h>' % R(self.H * s[1]))
			self.f.write('<texture>')
			self.f.write('<x1>%s</x1>' % R(p1[0]))
			self.f.write('<y1>%s</y1>' % R(p1[1]))
			self.f.write('<x2>%s</x2>' % R(p2[0]))
			self.f.write('<y2>%s</y2>' % R(p2[1]))
			self.f.write('</texture>')
			self.f.write('</layer>')
		self.f.write('</layers>')
		self.f.write('</PropertyList>')



def R(f, digits = 8):
	r = round(f, digits)
	if r == int(r):
		return str(int(r))
	else:
		return str(r)



def sind(a):
	return sin(a * pi / 180.0)



def cosd(a):
	return cos(a * pi / 180.0)



def position(begin, end, n):
	# return list of n evenly spaced steps from begin to end (n+1 positions)
	return [begin + i * (float(end) - begin) / n for i in range(n)] + [end]



def frange(start, end = None, step = None):
	if end:
		start += 0.0
	else:
		end = start + 0.0
		start = 0.0

	if not step:
		step = 1.0

	count = int(ceil((end - start) / step))
	L = [None,] * count
	for i in range(count):
		L[i] = start + i * step

	return L
