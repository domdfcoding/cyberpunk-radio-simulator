#!/usr/bin/env python3
#
#  widgets.py
"""
Textual widgets for terminal GUI.
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
import datetime

# 3rd party
from PIL import Image
from textual.app import ComposeResult
from textual.containers import VerticalGroup, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Digits, Label, ProgressBar, RichLog

# this package
from cyberpunk_radio_simulator.logos import logo_to_rich

__all__ = [
		"Clock",
		"Column",
		"StationLogo",
		"SubtitleLog",
		"TrackInfoLabel",
		"TrackProgress",
		"TrackProgressLabel",
		]


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

	def on_mount(self) -> None:  # noqa: D102
		self.set_interval(0.1, self.update_clock)

	def update_clock(self) -> None:
		"""
		Show the current time on the clock.
		"""

		clock = datetime.datetime.now().time()
		self.update(f"{clock:%T}")


class SubtitleLog(RichLog):
	"""
	Log widget for the DJ subtitles etc.
	"""

	DEFAULT_CSS = """
	SubtitleLog {
		height: 1fr;
		width: 1fr;
		border: tall $border-blurred;
        padding: 0 1;
		margin-top: 1;
	}
	"""

	def write_line(self, message: str) -> None:  # noqa: D102
		self.write(message)


audio_bars = "▁▂▃▄▅▆▇█▇▆▅▄▃"


class TrackProgressLabel(Label):
	"""
	Widget for displaying the current track position time, and the total track length.
	"""

	track_position: reactive[float] = reactive(0.0)
	duration: reactive[float] = reactive(0.0)
	paused: reactive[bool] = reactive(False)
	muted: reactive[bool] = reactive(False)
	audio_bar_idx = 0

	@staticmethod
	def format_time(seconds: float) -> str:
		"""
		Format a time in seconds to ``hours:minutes:seconds``.

		:param seconds:
		"""

		seconds = round(seconds)
		td = datetime.timedelta(seconds=seconds)
		# td = datetime.timedelta(days=td.days, seconds=td.seconds, microseconds=0)
		return str(td)

	def render(self) -> str:  # noqa: D102
		pos_td = self.format_time(seconds=self.track_position)
		dur_td = self.format_time(seconds=self.duration)
		elements = [f"{pos_td} / {dur_td}"]
		if self.paused:
			elements.append("  ⏸  ")
		else:
			self.audio_bar_idx += 1
			self.audio_bar_idx %= len(audio_bars)

			elements.append(
					''.join([
							audio_bars[self.audio_bar_idx - 12],
							audio_bars[self.audio_bar_idx - 9],
							audio_bars[self.audio_bar_idx - 6],
							audio_bars[self.audio_bar_idx - 3],
							audio_bars[self.audio_bar_idx],
							])
					)
		if self.muted:
			elements.append('🔇')
		else:
			elements.append("  ")

		return ' '.join(elements)


class TrackProgress(ProgressBar):
	"""
	Widget for displaying the position in the track, with a progress bar and times.
	"""

	DEFAULT_CSS = """
	TrackProgress {
		width: auto;
		height: 2;
		layout: horizontal;
	}
	"""
	# TODO: add spinner while playing and pause icon when paused (and mute icon when muted)

	track_position: reactive[float] = reactive(30)
	duration: reactive[float] = reactive(120)
	paused: reactive[bool] = reactive(False)
	muted: reactive[bool] = reactive(False)

	def set_track_pos(self, track_position: float, duration: float) -> None:
		"""
		Set the current track position and duration.

		:param track_position:
		:param duration:
		"""

		self.track_position = track_position
		self.duration = duration
		self.update(total=duration, progress=track_position)

	def compose(self) -> ComposeResult:  # noqa: D102
		with VerticalGroup():
			yield from super().compose()
			yield TrackProgressLabel().data_bind(
					track_position=TrackProgress.track_position,
					duration=TrackProgress.duration,
					paused=TrackProgress.paused,
					muted=TrackProgress.muted,
					)


class TrackInfoLabel(Label):
	"""
	Widget for displaying the current station or track.
	"""

	DEFAULT_CSS = """
	TrackInfoLabel {
		width: 40vw;
		max-width: 40vw;
	}
	"""


class StationLogo(Label):
	"""
	Widget for displaying the station logo.
	"""

	DEFAULT_CSS = """
	StationLogo {
		width: 50;
		max-width: 50;
		align-horizontal: center;
		align-vertical: middle;
		height: 1fr;
		text-align: center;
		background: #0e0204;
	}
	"""

	img: reactive[Image.Image | None] = reactive(None)

	def on_ready(self) -> None:  # noqa: D102
		self.data_bind(StationLogo.img)

	def render(self) -> str:  # noqa: D102
		if self.img:
			aspect = self.img.width / self.img.height
			if aspect < 1:
				# Taller than wide
				return logo_to_rich(self.img, 35)
			else:
				return logo_to_rich(self.img, 45)
		return ''
