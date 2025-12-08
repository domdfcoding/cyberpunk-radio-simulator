#!/usr/bin/env python3
#
#  simulator.py
"""
Radio playback logic.
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
import os
import random
import textwrap
import time

# 3rd party
from cp2077_extractor.audio_data.adverts import adverts
from cp2077_extractor.audio_data.radio_stations import radio_jingle_ids, radio_stations
from cp2077_extractor.radio_dj import EventData, load_events_dict
from cp2077_extractor.track import Track
from cp2077_extractor.utils import InfiniteList
from domdf_python_tools.typing import PathLike
from notify_rs import URGENCY_CRITICAL, Notification
from playsound3 import playsound
from playsound3.playsound3 import Sound

# this package
from cyberpunk_radio_simulator.data import StationData
from cyberpunk_radio_simulator.extractor import Directories

__all__ = ["Radio"]


class Radio(Directories):
	"""
	Plays audio files for a radio station.

	:param output_directory: Directory containing files extracted from the game.
	"""

	station: StationData
	track_list: InfiniteList[Track]
	ad_list: InfiniteList[str]
	link_list: InfiniteList[list[int]]
	jingle_list: InfiniteList[int]
	audio_events: dict[int, list[EventData]]
	subtitles: dict[str, str]

	#: Reference to object playing the audio.
	player: Sound | None

	def __init__(self, station: StationData, output_directory: PathLike = "data"):
		super().__init__(output_directory)
		self.station = station

		self.track_list = InfiniteList(list(radio_stations[self.station.name]))
		self.ad_list = InfiniteList(list(adverts.keys()))

		if station.dj:
			dj_data = self.dj_data_directory.joinpath(station.dj.audio_filename_prefix + "_data.json").load_json()
			self.subtitles = dj_data["subtitles"]
			self.audio_events = load_events_dict(dj_data["audio_events"])
			# link_list = list(p for p in dj_data["link_paths"] if len(p) > 1),
			link_list = list(p for p in dj_data["link_paths"])
			jingle_list = dj_data["end_nodes"]
		else:
			self.subtitles = {}
			self.audio_events = {}
			link_list = []
			jingle_list = radio_jingle_ids[station.name]

		self.link_list = InfiniteList(list(link_list))
		self.jingle_list = InfiniteList(list(jingle_list))

	def wait(self) -> None:
		"""
		Wait for audio playback to finish.
		"""

		if self.player is None:
			return
		else:
			self.player.wait()

	def play_music(self, blocking: bool = True) -> None:
		"""
		Play 3-5 songs back to back.

		:param blocking: If :py:obj:`True` music playback blocks execution until finished.
		"""

		remaining_song_count = random.randint(3, 5)
		print("Playing", remaining_song_count, "songs")
		while remaining_song_count:
			song: Track = self.track_list.pop()
			remaining_song_count -= 1
			print(f"{song.artist} – {song.title}")
			self.play_track(song, blocking)

	def play_track(self, track: Track, blocking: bool = True) -> None:
		"""
		Play a single song.

		:param track:
		:param blocking: If :py:obj:`True` music playback blocks execution until finished.
		"""

		filename = self.stations_audio_directory / self.station.name / f"{track.filename_stub}.mp3"
		# TODO: allow PathLike to be passed directly to notification
		Notification().summary(self.station.name).body(f"{track.artist} – {track.title}").icon(
				self.station_logos_directory.abspath().joinpath(f"{self.station.name}.png").as_posix()
				).urgency(URGENCY_CRITICAL).show()
		self.play_file(filename, blocking)

	def play_link(self, blocking: bool = True) -> None:
		"""
		Play a link (the DJ talking).

		:param blocking: If :py:obj:`True` music playback blocks execution until finished.
		"""

		link = self.link_list.pop()
		print("Play link", link)
		for node in link:
			time.sleep(0.5)
			self._play_scene_node(node, blocking)
			if not blocking:
				self.wait()

	def play_ad_break(self, blocking: bool = True) -> None:
		"""
		Play an ad break, consisting of 2 or 3 adverts.

		:param blocking: If :py:obj:`True` music playback blocks execution until finished.
		"""

		ad_count = random.randint(2, 3)
		print(f"Ad Break ({ad_count})")
		for _ in range(ad_count):
			time.sleep(0.5)
			advert = self.ad_list.pop()
			print(" -", advert)
			self.play_ad(advert, blocking)
			if not blocking:
				self.wait()

	def play_ad(self, ad_name: str, blocking: bool = True) -> None:
		"""
		Play an advert.

		:param ad_name: The name of the advert to play.
		:param blocking: If :py:obj:`True` music playback blocks execution until finished.
		"""

		filename = self.advert_audio_directory / f"{ad_name}.mp3"
		self.play_file(filename, blocking)

	def play_jingle(self, blocking: bool = True) -> None:
		"""
		Play one of the radio station's jingles.

		:param blocking: If :py:obj:`True` music playback blocks execution until finished.
		"""

		time.sleep(0.5)
		self._play_jingle_immediate(blocking)

	def _play_jingle_immediate(self, blocking: bool = True) -> None:
		node = self.jingle_list.pop()
		if self.audio_events:
			self._play_scene_node(node, blocking)
		else:
			filename = self.stations_audio_directory / self.station.name / f"jingle_{node}.mp3"
			self.play_file(filename, blocking)

	def _play_scene_node(self, node: int, blocking: bool = True) -> None:
		if not self.station.dj:
			raise NotImplementedError

		filename = self.dj_audio_directory / self.station.dj.station_name / f"{node}_{len(self.audio_events[node])}.mp3"
		for event in self.audio_events[node]:
			print('\n'.join(textwrap.wrap(self.subtitles[event.subtitle_ruid], subsequent_indent="  ")))
		self.play_file(filename, blocking)

	def play_file(self, filename: PathLike, blocking: bool = True) -> None:
		"""
		Play the given audio file.

		:param filename:
		:param blocking: If :py:obj:`True` music playback blocks execution until finished.
		"""

		self.player = playsound(os.fspath(filename), block=blocking)
