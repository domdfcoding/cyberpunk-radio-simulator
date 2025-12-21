#!/usr/bin/env python3
#
#  logos.py
"""
Functions for displaying radio station logos.
"""
#
#  Copyright © 2025 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

# stdlib
from typing import cast

# 3rd party
from domdf_python_tools.paths import PathPlus
from PIL import Image

__all__ = ["get_logo_tight", "logo_to_rich"]


def logo_to_rich(img: Image.Image, dest_width: int) -> str:
	"""
	Convert a logo, as a PIL image, for displaying with rich/Textual in a terminal.

	:param img:
	:param dest_width:
	"""

	scale = img.size[0] / dest_width
	dest_height = int(img.size[1] / scale)

	if dest_height % 2:
		dest_height += 1

	img = img.resize((dest_width, dest_height))

	output = ''

	for y in range(0, dest_height, 2):
		for x in range(dest_width):
			r1, g1, b1, *_ = cast(tuple[int, ...], img.getpixel((x, y)))
			r2, g2, b2, *_ = cast(tuple[int, ...], img.getpixel((x, y + 1)))
			output += f"[rgb({r1},{g1},{b1}) on rgb({r2},{g2},{b2})]▀[/]"

		output += '\n'

	return output


def get_logo_tight(station_name: str, data_directory: PathPlus) -> Image.Image:
	"""
	Return the radio station logo image, cropped tight to the logo itself.

	:param station_name:
	:param data_directory:
	"""

	image_file = data_directory / "artwork/stations" / f"{station_name}.png"
	img = cast(Image.Image, Image.open(image_file))
	img = img.crop(img.getbbox())

	return img


def apply_colour(
		img: Image.Image,
		background_colour: str = "#0e0204",
		graphic_colour: str = "#77ffff",
		) -> Image.Image:
	background: Image.Image = Image.new("RGBA", img.size, background_colour)
	foreground: Image.Image = Image.new("RGBA", img.size, graphic_colour)
	return Image.composite(foreground, background, img)
