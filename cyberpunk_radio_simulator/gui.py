#!/usr/bin/env python3
#
#  gui.py
"""
Textual terminal GUI for playback.
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
from dataclasses import dataclass
from typing import NamedTuple, cast

# 3rd party
from domdf_python_tools.paths import PathPlus
from just_playback import Playback  # type: ignore[import-untyped]
from textual import events, work
from textual.app import App, ComposeResult
from textual.binding import ActiveBinding, Binding
from textual.containers import Center, HorizontalGroup, HorizontalScroll, Right
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, OptionList, TabPane
from textual.widgets.option_list import Option

# this package
from cyberpunk_radio_simulator.config import Config
from cyberpunk_radio_simulator.data import StationData, stations
from cyberpunk_radio_simulator.events import AdBreak, Event, Tune
from cyberpunk_radio_simulator.logos import apply_colour, get_logo_tight
from cyberpunk_radio_simulator.media_control import MediaControl
from cyberpunk_radio_simulator.media_control.player import TrackMetadata
from cyberpunk_radio_simulator.simulator import AsyncRadio, RadioStation
from cyberpunk_radio_simulator.widgets import (
		TC,
		Clock,
		StationLogo,
		SubtitleLog,
		ThirdColumn,
		TrackInfoLabel,
		TrackProgress
		)

__all__ = ["MainScreen", "MuteState", "RadioportApp", "TextualRadio", "TrackInfo"]

station_names = list(stations)


class TextualRadio(AsyncRadio):
	"""
	Plays audio files for a radio station, asynchronously.

	Logs to a Textual ``Log`` widget (set by the ``log_widget`` attribute).

	:param station:
	:param output_directory: Directory containing files extracted from the game.
	"""

	log_widget: SubtitleLog

	def log(self, msg: str) -> None:  # noqa: D102
		self.log_widget.write_line(msg)


class _OL(OptionList):

	async def on_click(self, event: events.Click) -> None:
		if event.chain < 2:
			event.prevent_default()


class MainScreen(Screen):
	"""
	The main screen of the app.
	"""

	def compose(self) -> ComposeResult:  # noqa: D102
		yield Header()
		yield Footer()

		with HorizontalGroup():
			with ThirdColumn():
				yield TrackInfoLabel("Station Name", id="station-name")
				yield TrackInfoLabel("Artist - Track Title", id="track-info")
			with ThirdColumn():
				with Center():
					yield TrackProgress(id="track-progress", total=120, show_percentage=False, show_eta=False)
			with ThirdColumn():
				with Right():
					yield Clock("12:34:56")

		with HorizontalScroll():
			with TC():
				with TabPane("Stations", id="tab-stations"):
					yield _OL(
							*(Option(station, id=station) for station in station_names),
							id="station-selector",
							)
				with TabPane("Subtitles", id="tab-subtitles"):
					yield SubtitleLog(id="log", wrap=True)
			yield StationLogo(id="station-logo")

	@property
	def active_bindings(self) -> dict[str, ActiveBinding]:  # noqa: D102
		bindings_map = super().active_bindings

		parent: RadioportApp = cast(RadioportApp, self.parent)

		if parent.player.paused:
			label = "▶ Play "
		else:
			label = "⏸ Pause"

		bindings_map['p'] = bindings_map['p']._replace(binding=Binding(key='p', action="play", description=label))

		return bindings_map


@dataclass
class MuteState:
	"""
	Tracks whether the radio is muted.
	"""

	muted: bool = False
	last_volume: float = 1.0


class TrackInfo(NamedTuple):
	"""
	The current track's artist and title.
	"""

	artist: str = ''
	title: str = "No Track"

	@classmethod
	def from_event(cls, event: Event) -> "TrackInfo":
		"""
		Construct a :class:`~.TrackInfo` from an :class:`~.Event`.

		:param event:
		"""

		if isinstance(event, Tune):
			return cls(
					artist=event.artist or "Unknown Artist",
					title=event.title or "Unknown Title",
					)
		elif isinstance(event, AdBreak):
			return cls(title="Just Ads")
		else:
			return cls(title="No Track")

	def __str__(self) -> str:
		if self.artist:
			return f"{self.artist} – {self.title}"
		else:
			return self.title


class RadioportApp(App):
	"""
	Textual terminal app for playing the Cyberpunk radio.
	"""

	data_dir: PathPlus
	station_data: StationData
	station: RadioStation
	radio: TextualRadio
	player: Playback
	mute_state: MuteState
	track_info: TrackInfo
	_main_screen: MainScreen

	CSS = """
	Screen { align: center middle; }
	Digits { width: auto; }
	"""

	BINDINGS = [
			Binding("ctrl+c", "quit", "Quit", show=False, priority=True),
			Binding(key='q', action="quit", description="Quit the app"),
			Binding(key='p', action="play", description="▶ Play "),
			Binding(key='m', action="mute", description="Mute"),
			Binding(key='P', action="pause_next", description="Pause after current track"),
			Binding(key='<', action="previous", description="Previous Station"),
			Binding(key="comma", action="previous", description="Previous Station", show=False),
			Binding(key='>', action="next", description="Next Station"),
			Binding(key='.', action="next", description="Next Station", show=False),
			]


	def on_mount(self) -> None:  # noqa: D102
		self.title = "Radioport"

		self._main_screen = MainScreen()
		self.push_screen(self._main_screen)

		self.player = Playback()

	def action_mute(self) -> None:
		"""
		Handler for the "Mute" button.
		"""

		progbar = self._main_screen.query_one("#track-progress", TrackProgress)

		if self.mute_state.muted:
			self.mute_state.muted = False
			progbar.muted = False
			self.player.set_volume(self.mute_state.last_volume)
			self._main_screen.query_one("#log", SubtitleLog).write_line("Unmute")
		else:
			self.mute_state.muted = True
			progbar.muted = True
			self.mute_state.last_volume = self.player.volume
			self.player.set_volume(0)
			self._main_screen.query_one("#log", SubtitleLog).write_line("Mute")

	def action_play(self) -> None:
		"""
		Handler for the "Play/Pause" button.
		"""

		if self.player.paused:
			self.resume_song()
		else:
			self.pause_song()

		self.media_control.on_playpause()

	@property
	def playing(self) -> bool:
		"""
		Is the radio currently playing?
		"""  # noqa: D400

		if not self.player.active:
			return False
		return not self.player.paused

	@property
	def position(self) -> float:
		"""
		The current track position, in seconds.
		"""

		return self.player.curr_pos

	@property
	def song_length(self) -> float:
		"""
		The length of the current track, in seconds.
		"""

		return self.player.duration

	def resume_song(self) -> None:
		"""
		Play, regardless of whether we're already playing.
		"""

		self._main_screen.query_one("#log", SubtitleLog).write_line("Play")
		self._main_screen.query_one("#track-progress", TrackProgress).paused = False
		self.player.resume()
		self.refresh_bindings()

	def pause_song(self) -> None:
		"""
		Pause, regardless of whether we're already paused.
		"""

		self._main_screen.query_one("#log", SubtitleLog).write_line("Pause")
		self._main_screen.query_one("#track-progress", TrackProgress).paused = True
		self.player.pause()
		self.refresh_bindings()

	stop = pause_song

	def action_pause_next(self) -> None:
		"""
		Handler for the "Pause after track" button.
		"""

		self._main_screen.query_one("#log", SubtitleLog).write_line("Pause after this track")

	def load_station(self, station: RadioStation, force_jingle: bool = False) -> None:
		"""
		Load and play the given radio station.

		:param station:
		:param force_jingle: Start with a jingle. Otherwise the first event may be either a jingle or a tune
			(starting part way through), to simulating tuning in to the station mid song.
		"""

		self.station = station
		self.radio.station = self.station

		station_name_label = self._main_screen.query_one("#station-name", Label)
		station_name_label.content = self.station_data.name
		if self.station_data.dj:
			station_name_label.content += " 👤"
		if self.station_data.has_ads:
			station_name_label.content += " 📣"

		station_selector = self._main_screen.query_one("#station-selector", OptionList)
		station_selector.highlighted = station_names.index(self.station_data.name)

		logo_label_widget = self._main_screen.query_one("#station-logo", StationLogo)
		logo_label_widget.img = apply_colour(get_logo_tight(self.station_data.name, self.station.output_directory))

		# Reset paused indicator
		self._main_screen.query_one("#track-progress", TrackProgress).paused = False

		self.play_music(force_jingle=force_jingle)

	def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:  # noqa: D102
		if event.option_list.id == "station-selector":
			self.station_data = stations[cast(str, event.option.id)]

			station = RadioStation(self.station_data, output_directory=self.data_dir)
			# self.radio = TextualRadio(station=station, player=self.player)

			self.load_station(station, force_jingle=True)

	def action_next(self) -> None:
		"""
		Handler for the "Next Station" button.
		"""

		current_index = station_names.index(self.station_data.name)
		new_index = current_index + 1
		new_index %= len(station_names)

		self.station_data = stations[station_names[new_index]]
		# self._main_screen.query_one("#log", SubtitleLog).write_line("Next Station")

		self.load_station(RadioStation(self.station_data, output_directory=self.data_dir))

	def action_previous(self) -> None:
		"""
		Handler for the "Previous Station" button.
		"""

		current_index = station_names.index(self.station_data.name)
		new_index = current_index - 1
		new_index %= len(station_names)

		self.station_data = stations[station_names[new_index]]
		# self._main_screen.query_one("#log", SubtitleLog).write_line("Previous Station")

		self.load_station(RadioStation(self.station_data, output_directory=self.data_dir))

	next = action_next
	previous = action_previous

	@work(exclusive=True)
	async def play_music(self, force_jingle: bool = True) -> None:
		"""
		Worker to play the radio station.

		:param force_jingle: Start with a jingle. Otherwise the first event may be either a jingle or a tune
			(starting part way through), to simulating tuning in to the station mid song.
		"""

		self.radio.log_widget = self._main_screen.query_one("#log", SubtitleLog)
		track_info_label = self._main_screen.query_one("#track-info", Label)

		for event in self.station.get_events(force_jingle=force_jingle):
			# TODO: save state when changing station
			self.track_info = TrackInfo.from_event(event)
			track_info_label.update(str(self.track_info))
			self.set_timer(0.5, self.media_control.on_playback)
			self.set_timer(0.5, self.refresh_bindings)
			await self.radio.play_event_async(event)

	def setup_track_position(self) -> None:
		"""
		Setup the track position progressbar.
		"""

		self.set_interval(0.1, self.update_track_position)

	def update_track_position(self) -> None:
		"""
		Update the track position progressbar for the current audio playback position.
		"""

		progbar = self._main_screen.query_one("#track-progress", TrackProgress)
		progbar.set_track_pos(self.position, self.song_length)

	def setup_media_control(self) -> None:
		"""
		Setup desktop media controls.
		"""

		self.media_control = MediaControl(self)

	def on_ready(self) -> None:  # noqa: D102
		self.track_info = TrackInfo()

		self.setup_track_position()

		self.mute_state = MuteState(self.player.volume == 0, self.player.volume)
		self.setup_radio()
		self.setup_media_control()
		# log_widget = self._main_screen.query_one("#log", SubtitleLog)
		# log_widget.write_line(f"Station has DJ? {self.station.has_dj}")
		# log_widget.write_line("Ready")
		self.play_music()

	def setup_radio(self) -> None:
		"""
		Setup the :class:`~.Radio` class.
		"""

		self.station_data = stations[random.choice(station_names)]

		# self.station_data = stations["89.7 Growl FM"]
		# self.station_data = stations["107.5 Dark Star"]

		station = RadioStation(self.station_data, output_directory=self.data_dir)
		self.radio = TextualRadio(station=station, player=self.player)
		self.radio.notification_urgency = Config("config.toml").get_notification_urgency()

		self.load_station(station, force_jingle=True)

	def get_track_metadata(self) -> TrackMetadata:
		"""
		Returns the track title, artist, album name, and album art path (as file URL).
		"""

		album_art = self.station.station_logos_directory.joinpath(f"{self.station_data.name}.png").abspath()
		return {
				"title": self.track_info.title,
				"artist": self.track_info.artist,
				"album": self.station_data.name,
				"album_art": album_art.as_uri(),
				"track_id": 1234,  # TODO
				}


if __name__ == "__main__":
	app = RadioportApp()
	app.run()
