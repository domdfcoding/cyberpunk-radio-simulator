#!/usr/bin/env python3
#
#  mpris.py
"""
D-Bus MPRIS2 Server.
"""
#
#  From https://github.com/ZachVFXX/PyMusicTerm
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
import asyncio
import logging
import sys
import threading
from typing import TYPE_CHECKING, no_type_check

# 3rd party
from dbus_next import BusType, Variant
from dbus_next.aio import MessageBus
from dbus_next.service import PropertyAccess, ServiceInterface, dbus_property, method

# this package
from cyberpunk_radio_simulator.media_control.player import Player

logger: logging.Logger = logging.getLogger(__name__)

if TYPE_CHECKING:
	# String types used by dbus-next
	b = bool
	s = str
	d = float
	o = int
	x = int
	u = int

__all__ = [
		"DBusAdapter",
		"MPRISInterface",
		"MPRISPlayerInterface",
		"MPRISPlaylistsInterface",
		"Player",
		"TrackMetadata",
		]


class MPRISInterface(ServiceInterface):
	"""
	MPRIS2 Root Interface.

	:param adapter:
	"""

	adapter: "DBusAdapter"

	def __init__(self, adapter: "DBusAdapter") -> None:
		super().__init__("org.mpris.MediaPlayer2")
		self.adapter: DBusAdapter = adapter

	@method()
	def Raise(self) -> None:
		"""
		Does nothing. Exists so they widget is not greyed out as it is otherwise unclickable.
		"""

	@method()
	def Quit(self) -> None:
		"""
		Quit the media player.
		"""

		sys.exit()

	@dbus_property(access=PropertyAccess.READ)
	def CanQuit(self) -> 'b':
		return True

	@dbus_property(access=PropertyAccess.READ)
	def CanRaise(self) -> 'b':
		return True

	@dbus_property(access=PropertyAccess.READ)
	def HasTrackList(self) -> 'b':
		return False

	@dbus_property(access=PropertyAccess.READ)
	def Identity(self) -> 's':
		return "Radioport"

	# @no_type_check
	# @dbus_property(access=PropertyAccess.READ)
	# def SupportedUriSchemes(self) -> "as":
	# 	return ["file", "http", "https"]

	@no_type_check
	@dbus_property(access=PropertyAccess.READ)
	def SupportedMimeTypes(self) -> "as":
		return ["audio/mpeg", "audio/mp4", "audio/ogg", "audio/flac"]

	@dbus_property(access=PropertyAccess.READ)
	def DesktopEntry(self) -> 's':
		# TODO: file needs to exist for this to work; have it launch in new terminal window
		return "radioport.desktop"

	@dbus_property(access=PropertyAccess.READ)
	def Fullscreen(self) -> 'b':
		return False

	@dbus_property(access=PropertyAccess.READ)
	def CanSetFullscreen(self) -> 'b':
		return False


class MPRISPlayerInterface(ServiceInterface):
	"""
	MPRIS2 Player Interface.

	:param adapter:
	"""

	def __init__(self, adapter: "DBusAdapter") -> None:
		super().__init__("org.mpris.MediaPlayer2.Player")
		self.adapter = adapter
		self._rate = 1.0
		self._volume = 1.0
		self._loop_status = "None"
		self._shuffle = False

	@method()
	def Next(self) -> None:
		"""
		Skip to next track.
		"""

		if self.adapter.player:
			self.adapter.player.next()
			self.adapter.schedule_update()

	@method()
	def Previous(self) -> None:
		"""
		Skip to previous track.
		"""

		if self.adapter.player:
			self.adapter.player.previous()
			self.adapter.schedule_update()

	@method()
	def Pause(self) -> None:
		"""
		Pause playback.
		"""

		if self.adapter.player:
			self.adapter.player.pause_song()
			self.adapter.schedule_update()

	@method()
	def PlayPause(self) -> None:
		"""
		Toggle play/pause.
		"""

		if self.adapter.player:
			if self.adapter.player.playing:
				self.adapter.player.pause_song()
			else:
				self.adapter.player.resume_song()
			self.adapter.schedule_update()

	@method()
	def Stop(self) -> None:
		"""
		Stop playback.
		"""

		if self.adapter.player:
			self.adapter.player.stop()
			self.adapter.schedule_update()

	@method()
	def Play(self) -> None:
		"""
		Start or resume playback.
		"""

		if self.adapter.player:
			self.adapter.player.resume_song()
			self.adapter.schedule_update()

	# @method()
	# def Seek(self, offset: 'x') -> None:
	# 	"""
	# 	Seek forward or backward (microseconds).
	# 	"""

	# 	if self.adapter.player:
	# 		current = self.adapter.player.position
	# 		new_pos = current + (offset / 1000000)
	# 		self.adapter.player.seek_to(max(0, new_pos))

	# @method()
	# def SetPosition(self, track_id: 'o', position: 'x') -> None:
	# 	"""
	# 	Set absolute position (microseconds).
	# 	"""

	# 	if self.adapter.player:
	# 		self.adapter.player.seek_to(position / 1000000)

	# @method()
	# def OpenUri(self, uri: 's') -> None:
	# 	"""
	# 	Open a URI.
	# 	"""

	@dbus_property(access=PropertyAccess.READ)
	def PlaybackStatus(self) -> 's':
		"""
		Current playback status: ``'Playing'``, ``'Paused'``, or ``'Stopped'``.
		"""

		if not self.adapter.player:
			return "Stopped"

		return "Playing" if self.adapter.player.playing else "Paused"

	@no_type_check
	@dbus_property(access=PropertyAccess.READ)
	def Metadata(self) -> "a{sv}":
		"""
		Current track metadata.
		"""

		if not self.adapter.player:
			return {}

		try:

			track_meta = self.adapter.player.get_track_metadata()
			track_id = f"/org/mpris/MediaPlayer2/Track/{track_meta['track_id']}"
			length = int(self.adapter.player.song_length * 1000000)

			metadata = {
					"mpris:trackid": Variant('o', track_id),
					"mpris:length": Variant('x', length),
					"mpris:artUrl": Variant('s', track_meta["album_art"]),
					"xesam:title": Variant('s', track_meta["title"]),
					"xesam:album": Variant('s', track_meta["album"]),
					"xesam:artist": Variant("as", [track_meta["artist"]]),
					}

			return metadata
		except Exception as e:
			logger.error(f"Error getting metadata: {e}")
			return {}

	@dbus_property(access=PropertyAccess.READ)
	def Position(self) -> 'x':
		"""
		Current position in microseconds.
		"""

		if self.adapter.player:
			return int(self.adapter.player.position * 1000000)
		return 0

	@dbus_property(access=PropertyAccess.READ)
	def MinimumRate(self) -> 'd':
		return 1.0

	@dbus_property(access=PropertyAccess.READ)
	def MaximumRate(self) -> 'd':
		return 1.0

	@dbus_property(access=PropertyAccess.READ)
	def CanGoNext(self) -> 'b':
		return True

	@dbus_property(access=PropertyAccess.READ)
	def CanGoPrevious(self) -> 'b':
		return True

	@dbus_property(access=PropertyAccess.READ)
	def CanPlay(self) -> 'b':
		return True

	@dbus_property(access=PropertyAccess.READ)
	def CanPause(self) -> 'b':
		return True

	@dbus_property(access=PropertyAccess.READ)
	def CanSeek(self) -> 'b':
		return False

	@dbus_property(access=PropertyAccess.READ)
	def CanControl(self) -> 'b':
		return True

	@dbus_property()
	def Rate(self) -> 'd':
		return self._rate

	@Rate.setter
	def set_rate(self, val: 'd') -> None:
		self._rate = val

	@dbus_property()
	def Volume(self) -> 'd':
		return self._volume

	@Volume.setter
	def set_volume(self, val: 'd') -> None:
		self._volume = val

	@dbus_property()
	def LoopStatus(self) -> 's':
		return self._loop_status

	@LoopStatus.setter
	def set_loop_status(self, val: 's') -> None:
		self._loop_status = val

	@dbus_property()
	def Shuffle(self) -> 'b':
		return self._shuffle

	@Shuffle.setter
	def set_shuffle(self, val: 'b') -> None:
		self._shuffle = val


class MPRISPlaylistsInterface(ServiceInterface):
	"""
	MPRIS2 Playlists Interface.

	Optional but an error is raised if it doesn't exist 🤷.

	:param adapter:
	"""

	def __init__(self, adapter: "DBusAdapter") -> None:
		super().__init__("org.mpris.MediaPlayer2.Playlists")

	@dbus_property(access=PropertyAccess.READ)
	def PlaylistCount(self) -> 'u':
		return 0


class DBusAdapter:
	"""
	Adapter for dbus-next MPRIS implementation.
	"""

	def __init__(self) -> None:
		self.player: Player | None = None
		self.bus: MessageBus | None = None
		self.root_interface: MPRISInterface | None = None
		self.player_interface: MPRISPlayerInterface | None = None
		self._loop: asyncio.AbstractEventLoop | None = None
		self._thread: threading.Thread | None = None
		self._started = False

	def setup(self, player: Player) -> None:
		"""
		Setup the adapter with a player instance.

		:param player:
		"""

		self.player = player

	def _run_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
		"""
		Run the asyncio event loop in a separate thread.

		:param loop:
		"""

		asyncio.set_event_loop(loop)
		try:
			loop.run_forever()
		except Exception as e:
			logger.error(f"Event loop error: {e}")
		finally:
			loop.close()

	async def _start_server(self) -> None:
		"""
		Start the DBus server.
		"""

		try:
			self.bus = await MessageBus(bus_type=BusType.SESSION).connect()

			self.root_interface = MPRISInterface(self)
			self.player_interface = MPRISPlayerInterface(self)

			self.bus.export("/org/mpris/MediaPlayer2", self.root_interface)
			self.bus.export("/org/mpris/MediaPlayer2", self.player_interface)
			self.bus.export("/org/mpris/MediaPlayer2", MPRISPlaylistsInterface(self))

			await self.bus.request_name("org.mpris.MediaPlayer2.radioport")

			self._started = True

		except Exception as e:
			logger.error(f"Failed to start DBus server: {e}")
			self._started = False

	def start_background(self) -> None:
		"""
		Start the DBus server in a background thread.
		"""

		if self._thread is not None and self._thread.is_alive():
			return

		self._loop = asyncio.new_event_loop()

		self._thread = threading.Thread(
				target=self._run_event_loop,
				args=(self._loop, ),
				daemon=True,
				name="MPRIS-DBus-Thread",
				)
		self._thread.start()

		# Schedule the server start in the new loop
		asyncio.run_coroutine_threadsafe(self._start_server(), self._loop)

		# Give it a moment to start
		# stdlib
		import time

		time.sleep(0.5)

		if not self._started:
			logger.warning("DBus server may not have started correctly")

	def schedule_update(self) -> None:
		"""
		Schedule a property update in the event loop.
		"""

		if self._loop and self.player_interface:
			asyncio.run_coroutine_threadsafe(
					self._emit_properties_changed(),
					self._loop,
					)

	async def _emit_properties_changed(self) -> None:
		"""
		Emit properties changed signal.
		"""

		try:
			if self.player_interface:
				# Don't wrap in Variant - emit_properties_changed does that automatically
				changed_properties = {
						"PlaybackStatus": self.player_interface.PlaybackStatus,
						"Metadata": self.player_interface.Metadata,
						}
				self.player_interface.emit_properties_changed(changed_properties)
				logger.debug("Properties changed signal emitted")
		except Exception as e:
			logger.error(f"Error emitting properties changed: {e}", exc_info=True)

	def on_playback(self) -> None:
		"""
		Called when playback state changes.
		"""

		self.schedule_update()

	def on_playpause(self) -> None:
		"""
		Called when play/pause state changes.
		"""

		self.schedule_update()

	# def on_volume(self) -> None:
	# 	"""
	# 	Called when volume changes.
	# 	"""
