#!/usr/bin/env python3
#
#  player.py
"""
Protocol interface for media players.
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
from typing import Protocol, TypedDict

__all__ = ["Player", "TrackMetadata"]


class TrackMetadata(TypedDict):
	"""
	The return type of :meth:`~.get_track_metadata`.
	"""

	title: str
	artist: str
	album: str
	album_art: str
	track_id: int


class Player(Protocol):
	"""
	Protocol interface for media players.
	"""

	@property
	def playing(self) -> bool: ...

	@property
	def position(self) -> float: ...

	@property
	def song_length(self) -> float: ...

	def next(self) -> None: ...

	def previous(self) -> None: ...

	def pause_song(self) -> None: ...

	def resume_song(self) -> None: ...

	def stop(self) -> None: ...

	def get_track_metadata(self) -> TrackMetadata: ...
