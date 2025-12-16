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
from dataclasses import dataclass
from typing import cast

# 3rd party
from domdf_python_tools.paths import PathPlus
from just_playback import Playback  # type: ignore[import-untyped]
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import HorizontalGroup, HorizontalScroll, VerticalGroup
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, OptionList
from textual.widgets.option_list import Option

# this package
from cyberpunk_radio_simulator.data import StationData, stations
from cyberpunk_radio_simulator.events import AdBreak, Tune
from cyberpunk_radio_simulator.logos import apply_colour, get_logo_tight
from cyberpunk_radio_simulator.simulator import AsyncRadio, RadioStation
from cyberpunk_radio_simulator.widgets import Clock, StationLogo, SubtitleLog, TrackInfoLabel, TrackProgress

__all__ = ["MainScreen", "MuteState", "RadioportApp", "TextualRadio"]

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


class MainScreen(Screen):
	"""
	The main screen of the app.
	"""

	def compose(self) -> ComposeResult:  # noqa: D102
		yield Header()
		yield Footer()

		with HorizontalGroup():
			with VerticalGroup():
				yield TrackInfoLabel("Station Name", id="station-name")
				yield TrackInfoLabel("Artist - Track Title", id="track-info")
			with VerticalGroup():
				yield TrackProgress(id="track-progress", total=120, show_percentage=False, show_eta=False)
			yield Clock("12:34:56")

		with HorizontalScroll():
			with VerticalGroup():
				yield OptionList(
						*(Option(station, id=station) for station in station_names),
						id="station-selector",
						)
				yield SubtitleLog(id="log", wrap=True)
			yield StationLogo(id="station-logo")


@dataclass
class MuteState:
	"""
	Tracks whether the radio is muted.
	"""

	muted: bool = False
	last_volume: float = 1.0


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

	CSS = """
	Screen { align: center middle; }
	Digits { width: auto; }
	"""

	BINDINGS = [
			Binding("ctrl+c", "quit", "Quit", show=False, priority=True),
			Binding(key='q', action="quit", description="Quit the app"),
			Binding(key='p', action="play", description="⏯ Play/Pause"),
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

		progbar = self._main_screen.query_one("#track-progress", TrackProgress)

		if self.player.paused:
			self._main_screen.query_one("#log", SubtitleLog).write_line("Play")
			progbar.paused = False
			self.player.resume()
		else:
			self._main_screen.query_one("#log", SubtitleLog).write_line("Pause")
			progbar.paused = True
			self.player.pause()

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

		self.play_music(force_jingle=force_jingle)

	def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:  # noqa: D102
		if event.option_list.id == "station-selector":
			self.station_data = stations[cast(str, event.option.id)]

			station = RadioStation(self.station_data, output_directory=self.data_dir)
			self.radio = TextualRadio(station=station, player=self.player)

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
			if isinstance(event, Tune):
				track_info_label.update(f"{event.artist or 'Unknown Artist'} – {event.title or 'Unknown Title'}")
			elif isinstance(event, AdBreak):
				track_info_label.update("Just Ads")
			else:
				track_info_label.update("No Track")
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
		progbar.set_track_pos(self.player.curr_pos, self.player.duration)

	def on_ready(self) -> None:  # noqa: D102

		self.setup_track_position()

		self.player = Playback()
		self.mute_state = MuteState(self.player.volume == 0, self.player.volume)
		self.setup_radio()
		log_widget = self._main_screen.query_one("#log", SubtitleLog)
		# log_widget.write_line(f"Station has DJ? {self.station.has_dj}")
		# log_widget.write_line("Ready")
		self.play_music()

	def setup_radio(self) -> None:
		"""
		Setup the :class:`~.Radio` class.
		"""

		# self.station_data = stations["89.7 Growl FM"]
		self.station_data = stations["107.5 Dark Star"]

		station = RadioStation(self.station_data, output_directory=self.data_dir)
		self.radio = TextualRadio(station=station, player=self.player)

		self.load_station(station, force_jingle=True)


if __name__ == "__main__":
	app = RadioportApp()
	app.run()
