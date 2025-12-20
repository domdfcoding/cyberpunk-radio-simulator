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
import asyncio
import os
import random
import textwrap
import time
from collections.abc import Callable, Coroutine, Iterator

# 3rd party
from cp2077_extractor.audio_data.adverts import adverts
from cp2077_extractor.audio_data.radio_stations import radio_jingle_ids, radio_stations
from cp2077_extractor.radio_dj import EventData, load_events_dict
from cp2077_extractor.track import Track
from cp2077_extractor.utils import InfiniteList, to_snake_case
from domdf_python_tools.typing import PathLike
from just_playback import Playback  # type: ignore[import-untyped]
from notify_rs import URGENCY_NORMAL

# this package
from cyberpunk_radio_simulator.data import StationData
from cyberpunk_radio_simulator.events import AdBreak, Event, Jingle, Link, Tune
from cyberpunk_radio_simulator.extractor import Directories
from cyberpunk_radio_simulator.notifications import NotificationSender

__all__ = ["AsyncRadio", "Radio", "RadioStation"]


class RadioStation(Directories):
	"""
	Emits events to simulate playing a radio station.

	:param station:
	:param output_directory: Directory containing files extracted from the game.
	"""

	station: StationData
	track_list: InfiniteList[Track]
	ad_list: InfiniteList[str]
	link_list: InfiniteList[list[int]]
	jingle_list: InfiniteList[int]
	audio_events: dict[int, list[EventData]]
	subtitles: dict[str, str]

	_last_non_tune_action: type[Event] | None

	def __init__(self, station: StationData, output_directory: PathLike = "data"):
		super().__init__(output_directory)
		self.station = station
		self._last_non_tune_action = None

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

	@property
	def has_dj(self) -> bool:
		"""
		Does the station have a DJ?
		"""  # noqa: D400

		return bool(self.station.dj)

	def get_tunes(self) -> Iterator[Tune]:
		"""
		Play 3-5 songs back to back.
		"""

		remaining_song_count = random.randint(3, 5)
		while remaining_song_count:
			song: Track = self.track_list.pop()
			remaining_song_count -= 1
			filename = self.stations_audio_directory / self.station.name / f"{song.filename_stub}.mp3"
			yield Tune(
					audio_files=[filename],
					subtitles=[f"{song.artist} – {song.title}"],
					artist=song.artist,
					title=song.title,
					)

	def get_link(self) -> Iterator[Link]:
		"""
		Play a link (the DJ talking).
		"""

		if not self.station.dj:
			raise NotImplementedError

		link = self.link_list.pop()
		yield from self._links_for_nodes(link)

	def _links_for_nodes(self, node_ids: list[int]) -> Iterator[Link]:
		assert self.station.dj is not None

		dj_audio_dir = self.dj_audio_directory / self.station.dj.station_name
		for node in node_ids:
			audio_files = dj_audio_dir / f"{node}_{len(self.audio_events[node])}.mp3"
			subtitles = '\n'.join(self.subtitles[event.subtitle_ruid] for event in self.audio_events[node])
			yield Link(
					audio_files=[audio_files],
					subtitles=[subtitles],
					start_delay=0.5,
					inner_delay=0.5,
					node_id=node,
					)

	def get_ad_break(self) -> Iterator[AdBreak]:
		"""
		Play an ad break, consisting of 2 or 3 adverts.
		"""

		ad_count = random.randint(2, 3)

		audio_files = []
		ad_names = []

		for _ in range(ad_count):
			advert = self.ad_list.pop()
			audio_files.append(self.advert_audio_directory / f"{advert}.mp3")
			ad_names.append(f" - {advert}")

		yield AdBreak(
				audio_files=audio_files,
				subtitles=ad_names,
				start_delay=1,
				inner_delay=0.5,
				end_delay=0.5,
				ad_count=ad_count,
				)

	def get_jingle(self) -> Iterator[Event]:
		"""
		Play one of the radio station's jingles.
		"""

		node = self.jingle_list.pop()
		if self.audio_events:
			if not self.station.dj:
				raise NotImplementedError

			yield from self._links_for_nodes([node])
		else:
			filename = self.stations_audio_directory / self.station.name / f"jingle_{node}.mp3"
			yield Jingle(audio_files=[filename], start_delay=0.5)

	def get_events(self, force_jingle: bool = False) -> Iterator[Event]:
		"""
		Returns an iterator of events (tunes, DJ links, ad breaks etc.) for this radio station.

		:param force_jingle: Start with a jingle. Otherwise the first event may be either a jingle or a tune
			(starting part way through), to simulating tuning in to the station mid song.
		"""

		# When starting, play either the station jingle or a song from a random start point, unless force_jingle is True
		self._last_non_tune_action = Jingle

		# Unless forced, either start with a jingle or part way through the song (1:2)
		start_with_jingle = force_jingle or not random.getrandbits(2)
		if start_with_jingle:
			yield from self.get_jingle()
			yield from self.get_tunes()
		else:
			# Pick random start point (as percentage of track)
			start_points = [
					0, random.randint(30 - 5, 30 + 5), random.randint(60 - 5, 60 + 6), random.randint(90 - 5, 90)
					]
			start_percentage = random.choice(start_points)
			if start_percentage:
				# Otherwise we can play as normal
				music_events = list(self.get_tunes())
				music_events[0].start_point = start_percentage
				yield from music_events
			else:
				yield from self.get_tunes()

		# Now loop, playing a link/jingle/ad break, and then music
		while True:
			break_options: dict[type[Event], float] = {Jingle: 1.0}
			if self.has_dj:
				break_options[Link] = 2.0
			if self.station.has_ads:
				break_options[AdBreak] = 1.0

			# Weight it against the one that last happened
			break_options[self._last_non_tune_action] = 0.25
			option = random.choices(list(break_options), weights=list(break_options.values()), k=1)[0]
			self._last_non_tune_action = option

			if option is Link:
				yield from self.get_link()
			elif option is AdBreak:
				yield from self.get_ad_break()
				if not random.getrandbits(2):  # So happens 1/3 of the time
					yield from self.get_jingle()
			elif option is Jingle:
				yield from self.get_jingle()
			else:
				raise NotImplementedError(option)

			yield from self.get_tunes()


class Radio:
	"""
	Plays audio files for a radio station.

	:param station:
	"""

	station: RadioStation

	#: Reference to object playing the audio.
	player: Playback

	#: If :py:obj:`True`, skip all remaining actions for this event (stop playback, don't sleep, etc.)
	skip: bool = False

	#: Urgency to send the notification with.
	notification_urgency: int = URGENCY_NORMAL

	def __init__(self, station: RadioStation, player: Playback):
		self.station = station
		self.player = player

	def log(self, msg: str) -> None:
		"""
		Log a message; by default prints to the terminal.
		"""

		print('\n'.join(textwrap.wrap(msg, subsequent_indent="  ")))

	def wait(self) -> None:
		"""
		Wait for audio playback to finish.
		"""

		while self.player.active:
			pass

	def _send_tune_notification(self, tune: Tune) -> None:
		"""
		Send a desktop notification for the tune being played.
		"""

		icon_file = self.station.station_logos_directory.abspath() / f"{self.station.station.name}.png"

		# TODO: cancel unsend ones when switching station
		NotificationSender.send(
				summary=self.station.station.name,
				body=f"{tune.artist} – {tune.title}",
				icon_file=icon_file,
				urgency=self.notification_urgency,
				)

	def play_tune(self, tune: Tune) -> None:
		"""
		Play a :class:`~.Tune` – a single song.

		:param tune:
		"""

		self._send_tune_notification(tune)

		for idx, (filename, subtitles) in enumerate(tune.iter_files()):
			last_volume = self.player.volume

			if tune.start_point:
				self.player.set_volume(0)

			self.player.load_file(os.fspath(filename))
			self.player.play()

			if subtitles is not None:
				self.log(subtitles)

			if tune.start_point:
				self.player.seek((self.player.duration / 100) * tune.start_point)
				self.player.set_volume(last_volume)

			self.wait()

			if not self.skip and idx < len(tune.audio_files) - 1:
				time.sleep(tune.inner_delay)

	def play_ad_break(self, ad_break: AdBreak) -> None:
		"""
		Play an ad break, consisting of 2 or 3 adverts.

		:param ad_break:
		"""

		self.log(f"Ad Break ({ad_break.ad_count})")
		self._play_event(ad_break)

	def play_jingle(self, jingle: Jingle) -> None:
		"""
		Play one of the radio station's jingles.

		:param jingle:
		"""

		self.log("Play Jingle")
		self._play_event(jingle)

	def play_event(self, event: Event) -> None:
		"""
		Play an event (a jingle, ad break, tune, etc.).

		:param event:
		"""

		self.skip = False
		event_name = to_snake_case(type(event).__name__)
		event_fn = getattr(self, f"play_{event_name}", self._play_event)

		time.sleep(event.start_delay)
		event_fn(event)

		if not self.skip:
			time.sleep(event.end_delay)

	def _play_event(self, event: Event) -> None:
		"""
		Generic handler for playing events, where no specific function for the event type exists.

		:param event:
		"""

		for idx, (filename, subtitles) in enumerate(event.iter_files()):
			self.player.load_file(os.fspath(filename))
			self.player.play()

			if subtitles is not None:
				self.log(subtitles)

			self.wait()

			if not self.skip and idx < len(event.audio_files) - 1:
				time.sleep(event.inner_delay)

	def play(self) -> None:
		"""
		Play the station.
		"""

		for event in self.station.get_events(force_jingle=True):
			self.play_event(event)


class AsyncRadio(Radio):
	"""
	Plays audio files for a radio station, asynchronously.

	:param station:
	"""

	async def wait(self) -> None:  # type: ignore[override]
		"""
		Wait for audio playback to finish.
		"""

		while self.player.active:
			await asyncio.sleep(0.1)

	async def play_tune_async(self, tune: Tune) -> None:
		"""
		Play a :class:`~.Tune` – a single song.

		:param tune:
		"""

		self._send_tune_notification(tune)

		for idx, (filename, subtitles) in enumerate(tune.iter_files()):
			last_volume = self.player.volume

			if tune.start_point:
				self.player.set_volume(0)

			self.player.load_file(os.fspath(filename))
			self.player.play()

			# if subtitles is not None:
			# 	self.log(subtitles)

			if tune.start_point:
				self.player.seek((self.player.duration / 100) * tune.start_point)
				self.player.set_volume(last_volume)

			await self.wait()

			if not self.skip and idx < len(tune.audio_files) - 1:
				await asyncio.sleep(tune.inner_delay)

	async def play_ad_break_async(self, ad_break: AdBreak) -> None:
		"""
		Play an ad break, consisting of 2 or 3 adverts.

		:param ad_break:
		"""

		self.log(f"Ad Break ({ad_break.ad_count})")
		await self._play_event_async(ad_break)

	async def play_jingle_async(self, jingle: Jingle) -> None:
		"""
		Play one of the radio station's jingles.

		:param jingle:
		"""

		self.log("Play Jingle")
		await self._play_event_async(jingle)

	async def play_event_async(self, event: Event) -> None:
		"""
		Play an event (a jingle, ad break, tune, etc.).

		:param event:
		"""

		self.skip = False
		event_name = to_snake_case(type(event).__name__)
		event_fn: Callable[[Event], Coroutine] = getattr(self, f"play_{event_name}_async", self._play_event_async)

		await asyncio.sleep(event.start_delay)
		await event_fn(event)

		if not self.skip:
			await asyncio.sleep(event.end_delay)

	async def _play_event_async(self, event: Event) -> None:
		"""
		Generic handler for playing events, where no specific function for the event type exists.

		:param event:
		"""

		for idx, (filename, subtitles) in enumerate(event.iter_files()):
			self.player.load_file(os.fspath(filename))
			self.player.play()

			if subtitles is not None:
				self.log(subtitles)

			await self.wait()

			if not self.skip and idx < len(event.audio_files) - 1:
				await asyncio.sleep(event.inner_delay)

	async def play_async(self) -> None:
		"""
		Play the station.
		"""

		for event in self.station.get_events(force_jingle=True):
			await self.play_event_async(event)
