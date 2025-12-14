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
from datetime import datetime

# 3rd party
from domdf_python_tools.paths import PathPlus
from just_playback import Playback  # type: ignore[import-untyped]
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import HorizontalScroll, VerticalScroll
from textual.screen import Screen
from textual.widgets import Digits, Footer, Header, Label, Log

# this package
from cyberpunk_radio_simulator.data import StationData, stations
from cyberpunk_radio_simulator.simulator import AsyncRadio, RadioStation

__all__ = ["Clock", "Column", "MainScreen", "RadioportApp", "TextualRadio"]


class TextualRadio(AsyncRadio):
	"""
	Plays audio files for a radio station, asynchronously.

	Logs to a Textual ``Log`` widget (set by the ``log_widget`` attribute).

	:param station:
	:param output_directory: Directory containing files extracted from the game.
	"""

	log_widget: Log

	def log(self, msg: str) -> None:  # noqa: D102
		self.log_widget.write_line(msg)


class Column(VerticalScroll):
	"""
	A vertically scrollable column with a fixed width.
	"""

	DEFAULT_CSS = """
	Column {
		height: 1fr;
		width: 32;
		margin: 0 2;
	}
	"""


class Clock(Digits):
	"""
	Widget to show the current time.
	"""

	def update_clock(self) -> None:
		"""
		Show the current time on the clock.
		"""

		clock = datetime.now().time()
		self.update(f"{clock:%T}")


class MainScreen(Screen):
	"""
	The main screen of the app.
	"""

	def compose(self) -> ComposeResult:  # noqa: D102
		yield Header()
		yield Footer()
		with HorizontalScroll():
			with Column():
				yield Label("Hello, world!", id="station-name")
				yield Clock("12:34:56")
			yield Log(id="log")


class RadioportApp(App):
	"""
	Textual terminal app for playing the Cyberpunk radio.
	"""

	data_dir: PathPlus
	station_data: StationData
	station: RadioStation
	radio: TextualRadio

	CSS = """
	Screen { align: center middle; }
	Digits { width: auto; }
	"""

	BINDINGS = [
			Binding("ctrl+c", "quit", "Quit", show=False, priority=True),
			Binding(key='q', action="quit", description="Quit the app"),
			Binding(key='p', action="play", description="Play/Pause"),
			Binding(key='P', action="pause_next", description="Pause after current track"),
			Binding(key='<', action="previous", description="Previous Station"),
			Binding(key="comma", action="previous", description="Previous Station", show=False),
			Binding(key='>', action="next", description="Next Station"),
			Binding(key='.', action="next", description="Next Station", show=False),
			]

	def update_clock(self) -> None:
		clock = datetime.now().time()
		self._main_screen.query_one(Digits).update(f"{clock:%T}")

	def on_mount(self) -> None:  # noqa: D102
		self.title = "Radioport"

		self._main_screen = MainScreen()
		self.push_screen(self._main_screen)

	def action_play(self) -> None:
		"""
		Handler for the "Play/Pause" button.
		"""

		self._main_screen.query_one("#log", Log).write_line("Play")

	def action_pause_next(self) -> None:
		"""
		Handler for the "Pause after track" button.
		"""

		self._main_screen.query_one("#log", Log).write_line("Pause after this track")

	def action_next(self) -> None:
		"""
		Handler for the "Next Station" button.
		"""

		self._main_screen.query_one("#log", Log).write_line("Next Station")

	def action_previous(self) -> None:
		"""
		Handler for the "Previous Station" button.
		"""

		self._main_screen.query_one("#log", Log).write_line("Previous Station")

	@work(exclusive=True)
	async def play_music(self) -> None:  # noqa: D102
		self.radio.log_widget = self._main_screen.query_one("#log", Log)

		for event in self.station.get_events(force_jingle=True):
			# TODO: handle station changing
			await self.radio.play_event_async(event)

	def setup_clock(self) -> None:
		"""
		Setup the clock widget.
		"""

		# TODO: call update_clock method on Clock itself.
		self.update_clock()
		self.set_interval(1, self.update_clock)

	def on_ready(self) -> None:  # noqa: D102

		self.setup_clock()

		self.setup_radio()
		log_widget = self._main_screen.query_one("#log", Log)
		log_widget.write_line("Station has DJ?", self.station.has_dj)
		log_widget.write_line("Ready")
		self.play_music()

	def setup_radio(self) -> None:
		"""
		Setup the :class:`~.Radio` class.
		"""

		# self.station_data = stations["89.7 Growl FM"]
		self.station_data = stations["107.5 Dark Star"]

		self.station = RadioStation(self.station_data, output_directory=self.data_dir)
		self.radio = TextualRadio(station=self.station, player=Playback())

		self._main_screen.query_one("#station-name", Label).content = self.station_data.name


if __name__ == "__main__":
	app = RadioportApp()
	app.run()
