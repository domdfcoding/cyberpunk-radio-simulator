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

	def play_music(self) -> None:
		"""
		Play 3-5 songs back to back.
		"""

		remaining_song_count = random.randint(3, 5)
		print("Playing", remaining_song_count, "songs")
		while remaining_song_count:
			song: Track = self.track_list.pop()
			remaining_song_count -= 1
			filename = self.stations_audio_directory / self.station.name / f"{song.filename_stub}.mp3"
			print(f"{song.artist} – {song.title}")
			# TODO: allow PathLike to be passed directly
			Notification().summary(self.station.name).body(f"{song.artist} – {song.title}").icon(
					self.station_logos_directory.abspath().joinpath(f"{self.station.name}.png").as_posix()
					).urgency(URGENCY_CRITICAL).show()
			playsound(filename)

	def play_link(self) -> None:
		"""
		Play a link (the DJ talking).
		"""

		link = self.link_list.pop()
		print("Play link", link)
		for node in link:
			time.sleep(0.5)
			self._play_scene_node(node)

	def play_ads(self) -> None:
		"""
		Play an ad break, consisting of 2 or 3 adverts.
		"""

		ad_count = random.randint(2, 3)
		print(f"Ad Break ({ad_count})")
		for _ in range(ad_count):
			time.sleep(0.5)
			advert = self.ad_list.pop()
			print(" -", advert)
			filename = self.advert_audio_directory / f"{advert}.mp3"
			playsound(filename)

	def play_jingle(self) -> None:
		"""
		Play one of the radio station's jingles.
		"""

		print("Jingle")
		time.sleep(0.5)
		node = self.jingle_list.pop()
		if self.audio_events:
			self._play_scene_node(node)
		else:
			filename = self.stations_audio_directory / self.station.name / f"jingle_{node}.mp3"
			playsound(filename)

	def _play_scene_node(self, node: int) -> None:
		if not self.station.dj:
			raise NotImplementedError

		filename = self.dj_audio_directory / self.station.dj.station_name / f"{node}_{len(self.audio_events[node])}.mp3"
		for event in self.audio_events[node]:
			print('\n'.join(textwrap.wrap(self.subtitles[event.subtitle_ruid], subsequent_indent="  ")))
		playsound(filename)
