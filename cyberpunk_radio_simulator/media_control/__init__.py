#!/usr/bin/env python3
#
#  __init__.py
"""
Desktop media control integration.
"""
#
#  Adapted from https://github.com/ZachVFXX/PyMusicTerm
#  Copyright (c) 2025 ZachVFX
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
import sys

# this package
from cyberpunk_radio_simulator.media_control.player import Player

__all__ = ["MediaControl"]

if sys.platform == "win32":
	# this package
	from .smtc import MediaControlWin32 as MediaControlWin

	class MediaControl(MediaControlWin):
		"""
		Desktop media controls interface.
		"""

		def __init__(self) -> None:
			super().__init__()

		def init(self, player: Player) -> None:
			"""
			Initialize with player.

			:param player:
			"""

			return super().init(player)

		def on_playback(self) -> None:
			return super().on_playback()

		def on_playpause(self) -> None:
			return super().on_playpause()

else:
	# this package
	from .mpris import DBusAdapter

	class MediaControl:
		"""
		Desktop media controls interface.
		"""

		def __init__(self) -> None:
			self.adapter: DBusAdapter = DBusAdapter()

		def init(self, player: Player) -> None:
			"""
			Initialize with player and start background loop.

			:param player:
			"""

			self.adapter.setup(player)
			self.adapter.start_background()

		def on_playback(self) -> None:
			"""
			Handle playback events.
			"""

			return self.adapter.on_playback()

		def on_playpause(self) -> None:
			"""
			Handle play/pause events.
			"""

			return self.adapter.on_playback()
