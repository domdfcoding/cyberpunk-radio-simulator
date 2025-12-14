#!/usr/bin/env python3
#
#  events.py
"""
Events for radio simulation logic.
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
from collections.abc import Iterator
from dataclasses import dataclass, field
from itertools import zip_longest

# 3rd party
from domdf_python_tools.paths import PathPlus

__all__ = ["AdBreak", "Event", "Jingle", "Link", "Tune"]


@dataclass
class Event:
	"""
	An event for the radio station logic.
	"""

	audio_files: list[PathPlus]
	subtitles: list[str] = field(default_factory=list)
	start_delay: float = 0.0
	end_delay: float = 0.0
	inner_delay: float = 0.0

	def iter_files(self) -> Iterator[tuple[PathPlus, str | None]]:
		"""
		Returns an iterator over audio files and their subtitles (if any).
		"""

		if self.subtitles:
			assert len(self.subtitles) == len(self.audio_files)

		yield from zip_longest(self.audio_files, self.subtitles)


@dataclass
class Tune(Event):
	"""
	Represents a song.
	"""

	artist: str = ''
	title: str = ''

	#: Percentage through track to start playback from.
	start_point: int = 0


@dataclass
class Jingle(Event):
	"""
	Represents a station's jingle.
	"""


@dataclass
class Link(Event):
	"""
	Represents a DJ's link.
	"""

	node_id: int = -1


@dataclass
class AdBreak(Event):
	"""
	Represents an ad break.
	"""

	ad_count: int = 0
