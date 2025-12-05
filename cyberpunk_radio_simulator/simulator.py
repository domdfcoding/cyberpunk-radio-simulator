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
from collections.abc import Sequence
from typing import NamedTuple

# 3rd party
from cp2077_extractor.audio_data.adverts import adverts
from cp2077_extractor.audio_data.radio_stations import radio_jingle_ids, radio_stations
from cp2077_extractor.radio_dj import DJData, EventData, load_events_dict
from cp2077_extractor.track import Track
from cp2077_extractor.utils import _T, InfiniteList
from playsound3 import playsound

# this package
from cyberpunk_radio_simulator.data import djs
from cyberpunk_radio_simulator.extractor import Directories

__all__ = ["Radio", "StationData"]


class Radio:
	station_name: str
	working_track_list: InfiniteList[Track]
	working_ad_list: InfiniteList[int]
	working_link_list: InfiniteList[list[int]]
	working_jingle_list: InfiniteList[int]
	audio_events: dict[int, EventData]
	subtitles: dict[str, str]

	def __init__(
			self,
			station_name: str,
			track_list: Sequence[Track],
			ad_list: Sequence[int],
			jingle_list: Sequence[int],
			link_list: Sequence[list[int]] = (),
			audio_events: dict[int, EventData] | None = None,
			subtitles: dict[str, str] | None = None
			):
		self.station_name = station_name
		self.working_track_list = InfiniteList(list(track_list))
		self.working_ad_list = InfiniteList(list(ad_list))
		self.working_link_list = InfiniteList(list(link_list))
		self.working_jingle_list = InfiniteList(list(jingle_list))
		self.audio_events = audio_events
		self.subtitles = subtitles
		self.directories = Directories()  # TODO

	def play_music(self):
		# Play 3-5 songs
		remaining_song_count = random.randint(3, 5)
		print("Playing", remaining_song_count, "songs")
		while remaining_song_count:
			song: Track = self.working_track_list.pop()
			remaining_song_count -= 1
			filename = self.directories.stations_audio_directory / self.station_name / f"{song.filename_stub}.mp3"
			print(f"{song.artist} – {song.title}")
			playsound(filename)

	def play_link(self):
		link = self.working_link_list.pop()
		print("Play link", link)
		for node in link:
			time.sleep(0.5)
			self._play_scene_node(node)

	def play_ads(self):
		ad_count = random.randint(2, 3)
		print(f"Ad Break ({ad_count})")
		for _ in range(ad_count):
			time.sleep(0.5)
			advert = self.working_ad_list.pop()
			print(" -", advert)
			filename = self.directories.advert_audio_directory / f"{advert}.mp3"
			playsound(filename)

	def play_jingle(self):
		print("Jingle")
		time.sleep(0.5)
		node = self.working_jingle_list.pop()
		if self.audio_events:
			self._play_scene_node(node)
		else:
			filename = self.directories.stations_audio_directory / self.station_name / f"jingle_{node}.mp3"
			playsound(filename)

	def _play_scene_node(self, node: int):
		# TODO: self.station_name -> dj.station_name
		filename = self.directories.dj_audio_directory / self.station_name / f"{node}_{len(self.audio_events[node])}.mp3"
		for event in self.audio_events[node]:
			print('\n'.join(textwrap.wrap(self.subtitles[event.subtitle_ruid], subsequent_indent="  ")))
		playsound(filename)


class StationData(NamedTuple):
	#: The name of the radio station
	name: str

	#: The station's DJ, if any.
	dj: DJData | None = None


stations = {
		sd.name: sd
		for sd in [
				StationData("88.9 Pacific Dreams"),
				StationData("89.3 Radio Vexelstrom"),
				StationData("89.7 Growl FM", dj=djs["Ash"]),
				StationData("91.9 Royal Blue Radio"),
				StationData("92.9 Night FM"),
				StationData("95.2 Samizdat Radio"),
				StationData("96.1 Ritual FM"),
				StationData("98.7 Body Heat Radio"),
				StationData("99.9 Impulse"),
				StationData("101.9 The Dirge"),
				StationData("103.5 Radio PEBKAC"),
				StationData("106.9 30 Principales"),
				StationData(
						"107.3 Morro Rock Radio", dj=djs["Max Mike"]
						),  # TODO: filter out (and later program separately) the song intros/outros. TODO: played 274 as link on its own out of context
				StationData("107.5 Dark Star"),
				]
		}
