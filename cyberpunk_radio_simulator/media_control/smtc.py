#!/usr/bin/env python3
#
#  smtc.py
"""
Windows media controls interface.
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
import logging

# 3rd party
from winrt.windows.media import (  # type: ignore[import-not-found,unused-ignore] # nodep
		MediaPlaybackStatus,
		SystemMediaTransportControls,
		SystemMediaTransportControlsButton,
		SystemMediaTransportControlsButtonPressedEventArgs
		)
from winrt.windows.media.playback import MediaPlayer  # type: ignore[import-not-found,unused-ignore] # nodep

# this package
from cyberpunk_radio_simulator.media_control.player import Player

__all__ = ["MediaControlWin32", "SIGRAISE"]

logger: logging.Logger = logging.getLogger(__name__)

SIGRAISE = 99


class MediaControlWin32:
	"""
	Windows media controls interface.

	:param player:
	"""

	player: Player
	media_player: MediaPlayer | None
	smtc: SystemMediaTransportControls | None

	def __init__(self, player: Player) -> None:
		self.player = player
		self.media_player = MediaPlayer()
		self.media_player.auto_play = True
		self.media_player.volume = 0.0
		# SMTC setup
		self.smtc = self.media_player.system_media_transport_controls
		self.smtc.shuffle_enabled = False
		self.smtc.is_play_enabled = True
		self.smtc.is_pause_enabled = True
		self.smtc.is_next_enabled = True
		self.smtc.is_previous_enabled = True
		self.smtc.is_enabled = True

		def button_pressed(_: None, args: SystemMediaTransportControlsButtonPressedEventArgs) -> None:
			logger.info("SMTC button pressed: %s", args.button)

			if args.button == SystemMediaTransportControlsButton.PLAY:
				self.play()
			elif args.button == SystemMediaTransportControlsButton.PAUSE:
				self.pause()
			elif args.button == SystemMediaTransportControlsButton.NEXT:
				self.player.next()
				self.play()
			elif args.button == SystemMediaTransportControlsButton.PREVIOUS:
				self.player.previous()
				self.play()

		self.smtc.add_button_pressed(button_pressed)

	def on_playback(self) -> None:
		"""
		Called when playback state changes.
		"""

	def on_playpause(self) -> None:
		"""
		Called when play/pause state changes.
		"""

		if not self.smtc or not self.player:
			return
		if self.player.playing and self.player.playing:
			self.smtc.playback_status = MediaPlaybackStatus.PLAYING
		else:
			self.smtc.playback_status = MediaPlaybackStatus.PAUSED

	def on_volume(self) -> None:
		pass

	def play(self) -> None:
		if self.player:
			self.player.resume_song()
		self.on_playpause()

	def pause(self) -> None:
		if self.player:
			self.player.pause_song()
		self.on_playpause()
