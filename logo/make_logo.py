import math
from typing import List, NamedTuple, Optional

import drawsvg


class Point(NamedTuple):
	x: float
	y: float

	def __add__(self, other: 'Point') -> 'Point':
		return Point(self.x + other.x, self.y + other.y)


def hexagon_points(r: float) -> List[Point]:
	"""
	   p0
	p5    p1
	p4    p2
	   p3
	"""
	hexagon = []
	for i in range(6):
		x = r * math.sin(-math.pi / 3 * i + math.pi)
		y = r * math.cos(-math.pi / 3 * i + math.pi)
		hexagon.append(Point(x, y))
	return hexagon


def make_polygon(points: List[Point], **kwargs) -> drawsvg.Path:
	def polish(v: float):
		v = round(v, 8)
		if v.is_integer():
			v = int(v)
		return v

	flatten = [x for point in points for x in point]
	return drawsvg.Lines(*map(polish, flatten), close=True, **kwargs)


def make(
		file_path: str,
		hexagon_background: bool = False,
		full_background: bool = False,
		strip_padding: bool = False,
		color_override: Optional[str] = None,
):
	background_color = '#F3F4F8'
	ring_yellow = color_override or '#FAC00F'
	ring_blue = color_override or '#3876A9'
	cube_green1 = color_override or '#399B2A'
	cube_green2 = color_override or '#397B0D'
	cube_brown = color_override or '#865B3E'

	width = 100
	if hexagon_background and strip_padding:
		raise ValueError('bad config')
	if strip_padding:
		width -= 20
	d = drawsvg.Drawing(width, width, origin='center')
	h0 = hexagon_points(r=1)   # tiny gap
	h1 = hexagon_points(r=20)  # cube
	h2 = hexagon_points(r=30)  # ring inner
	h3 = hexagon_points(r=40)  # ring outer
	h4 = hexagon_points(r=50)  # background_color
	o = Point(0, 0)

	# ======= background ======
	if full_background:
		d.append(drawsvg.Lines(
			*[
				-width, -width,
				width, -width,
				width, width,
				-width, width
			],
			close=True, fill=background_color
		))
	elif hexagon_background:
		d.append(make_polygon(
			h4,
			fill=background_color,
		))

	# ======= ring =======
	# top left
	d.append(make_polygon(
		[
			h3[0], h3[1], h3[2],
			h2[2], h2[1], h2[0],
		],
		fill=ring_yellow,
	))
	# bottom right
	d.append(make_polygon(
		[
			h3[3], h3[4], h3[5],
			h2[5], h2[4], h2[3],
		],
		fill=ring_blue,
	))

	# ======= cube =======
	# top
	d.append(make_polygon(
		[o + h0[0], h1[5] + h0[1], h1[0], h1[1] + h0[5]],
		fill=cube_green1,
	))
	# bottom left
	d.append(make_polygon(
		[o + h0[4], h1[3] + h0[5], h1[4], h1[5] + h0[3]],
		fill=cube_green2,
	))
	# bottom right
	d.append(make_polygon(
		[o + h0[2], h1[1] + h0[3], h1[2], h1[3] + h0[1]],
		fill=cube_brown,
	))

	d.save_svg(file_path)


def main():
	make('logo.svg')
	make('logo_compact.svg', strip_padding=True)
	make('logo_full_background.svg', full_background=True)
	make('logo_full_background_compact.svg', full_background=True, strip_padding=True)
	make('logo_hexagon_background.svg', hexagon_background=True)
	make('logo_white.svg', color_override='white')
	make('logo_white_compact.svg', strip_padding=True, color_override='white')


if __name__ == '__main__':
	main()
