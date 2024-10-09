import base64
import functools
import math
import re
from io import BytesIO
from pathlib import Path
from typing import List, NamedTuple, Optional

import drawsvg
from fontTools.subset import Subsetter
from fontTools.ttLib import TTFont


class Point(NamedTuple):
	x: float
	y: float

	def __add__(self, other: 'Point') -> 'Point':
		return Point(self.x + other.x, self.y + other.y)


@functools.lru_cache(maxsize=None)
def font_subset_uri():
	"""Get a base64-encoded subset of the Minecrafter font as a data URI."""
	font = TTFont('font/Minecrafter.Reg.ttf', recalcTimestamp=False)

	subsetter = Subsetter()
	subsetter.populate(text=''.join(set('MCDaemonReforged')))
	subsetter.subset(font)

	font.flavor = 'woff'
	file = BytesIO()
	font.save(file)

	b64_encoded = base64.b64encode(file.getvalue()).decode('utf-8')
	subset_cache = 'data:font/ttf;base64,' + b64_encoded

	return subset_cache


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


def save_svg(img: drawsvg.Drawing, file_path: Path):
	svg = img.as_svg()
	svg = re.sub(r' xmlns:xlink="http://www\.w3\.org/1999/xlink"([\n\r])', '\\1', svg, 1)  # pycharm says this is useless
	with open(file_path, 'w', encoding='utf8', newline='\n') as f:
		f.write(svg)


def make(
		file_path: Path,
		hexagon_background: bool = False,
		full_background: bool = False,
		strip_padding: bool = False,
		long: bool = False,
		color_override: Optional[str] = None,
):
	background_color = '#F3F4F8'
	ring_yellow = color_override or '#FAC00F'
	ring_blue = color_override or '#3876A9'
	cube_green1 = color_override or '#399B2A'
	cube_green2 = color_override or '#397B0D'
	cube_brown = color_override or '#865B3E'
	text_brown = color_override or '#C8723F'
	text_gray = color_override or '#646464'

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
	if full_background and not long:
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

	if long:
		if hexagon_background or strip_padding:
			raise ValueError('strip_padding and hexagon_background are incompatible with long')

		text_size = 40
		text_x = 165
		font_css = '\n'.join([
			'@font-face {',
			'   font-family: "MineCrafter";',
			f'   src: url({font_subset_uri()}) format("woff");',
			'}',
		])

		long = drawsvg.Drawing(
			350, 100,
			viewBox='-50 -50 350 100',
			style=f'background: {background_color}' if full_background else ''
		)
		long.append_css(font_css)
		for ele in d.elements:
			long.append(ele)
		text = drawsvg.Text(
			text='',
			font_size=text_size,
			x=text_x,
			y=-4.25,
			style='font-family: Minecrafter',
			text_anchor='middle',
		)
		text.append_line('MCDaemon', fill=text_brown)
		text.append_line('Reforged', fill=text_gray, x=text_x, dy=text_size)
		long.append(text)
		save_svg(long, file_path)

	else:
		save_svg(d, file_path)


def main():
	output_dir = Path('images')
	output_dir.mkdir(exist_ok=True)

	make(output_dir / 'logo.svg')
	make(output_dir / 'logo_compact.svg', strip_padding=True)
	make(output_dir / 'logo_full_background.svg', full_background=True)
	make(output_dir / 'logo_full_background_compact.svg', full_background=True, strip_padding=True)
	make(output_dir / 'logo_hexagon_background.svg', hexagon_background=True)
	make(output_dir / 'logo_white.svg', color_override='white')
	make(output_dir / 'logo_white_compact.svg', strip_padding=True, color_override='white')
	make(output_dir / 'logo_long.svg', long=True)
	make(output_dir / 'logo_long_white.svg', long=True, color_override='white')
	make(output_dir / 'logo_long_full_background.svg', long=True, full_background=True)


if __name__ == '__main__':
	main()
