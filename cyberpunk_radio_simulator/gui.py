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
from cp2077_extractor.utils import InfiniteList
from domdf_python_tools.paths import PathPlus
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import HorizontalScroll, VerticalScroll
from textual.screen import Screen
from textual.widgets import Digits, Footer, Header, Label, Log, Placeholder

# this package
from cyberpunk_radio_simulator.data import stations
from cyberpunk_radio_simulator.simulator import AsyncRadio, Radio

__all__ = ["Clock", "Column", "MainScreen", "RadioportApp", "TextualRadio"]


class TextualRadio(AsyncRadio):
	log_widget: Log

	def log(self, msg):
		self.log_widget.write_line(msg)


class Column(VerticalScroll):
	DEFAULT_CSS = """
	Column {
		height: 1fr;
		width: 32;
		margin: 0 2;
	}
	"""


class Clock(Digits):

	def update_clock(self) -> None:
		clock = datetime.now().time()
		self.update(f"{clock:%T}")


class MainScreen(Screen):

	def compose(self) -> ComposeResult:
		yield Header()
		yield Footer()
		with HorizontalScroll():
			with Column():
				yield Label("Hello, world!", id="station-name")
				yield Clock("12:34:56")
			yield Log(id="log")


class RadioportApp(App):
	data_dir: PathPlus

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

	def on_mount(self) -> None:
		self.title = "Radioport"

		self._main_screen = MainScreen()
		self.push_screen(self._main_screen)

	def action_play(self):
		self._main_screen.query_one("#log", Log).write_line("Play")

	def action_next(self):
		self._main_screen.query_one("#log", Log).write_line("Next Station")

	def action_previous(self):
		self._main_screen.query_one("#log", Log).write_line("Previous Station")

	@work(exclusive=True)
	async def play_music(self) -> None:
		self.radio.log_widget = self._main_screen.query_one("#log", Log)

		LINK = 1
		AD_BREAK = 2
		JINGLE = 3
		if self.station.dj:
			break_options: InfiniteList[int] = InfiniteList([LINK, 0, AD_BREAK, JINGLE])
		else:
			break_options = InfiniteList([AD_BREAK, JINGLE])

		self.radio.log_widget.write_line("Jingle")
		await self.radio.play_jingle(blocking=False)
		while True:
			await self.radio.play_music(blocking=False)
			option = break_options.pop()
			if option == LINK:
				await self.radio.play_link(blocking=False)
			elif option == AD_BREAK:
				await self.radio.play_ad_break(blocking=False)
			elif option == JINGLE:
				self.radio.log_widget.write_line("Jingle")
				await self.radio.play_jingle(blocking=False)
			else:
				self.radio.log_widget.write_line("Link alt")
				await self.radio.play_link(blocking=False)

	def setup_clock(self):
		self.update_clock()
		self.set_interval(1, self.update_clock)  # TODO: call method on Clock itself.

	def on_ready(self):

		self.setup_clock()

		self.setup_radio()
		log_widget = self._main_screen.query_one("#log", Log)
		log_widget.write_line("Ready")
		self.play_music()

	def setup_radio(self):
		# self.station = stations["89.7 Growl FM"]
		self.station = stations["107.5 Dark Star"]
		self.radio = TextualRadio(station=self.station, output_directory=self.data_dir)
		print("Station has DJ?", self.station.dj is not None)

		self._main_screen.query_one("#station-name", Label).content = self.station.name


if __name__ == "__main__":
	app = RadioportApp()
	app.run()
