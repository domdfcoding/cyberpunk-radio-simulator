#!/usr/bin/env python3
#
#  __main__.py
"""
Play Cyberpunk 2077 radios in your terminal, with jingles, DJs and adverts.
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

# 3rd party
import click
from consolekit import CONTEXT_SETTINGS, SuggestionGroup, click_group
from consolekit.options import flag_option
from consolekit.versions import version_callback_option

# this package
from cyberpunk_radio_simulator import __version__
from cyberpunk_radio_simulator.cli import get_subprocess_arguments, output_dir_option, station_option, theme_option

__all__ = ["extract", "gui", "main", "play", "web", "wrapper"]


@version_callback_option(
		__version__,
		"cyberpunk-song-extractor",
		dependencies=("click", "cp2077-extractor"),
		)
@click_group(cls=SuggestionGroup, invoke_without_command=False, context_settings=CONTEXT_SETTINGS)
def main() -> None:
	"""
	Play Cyberpunk 2077 radios in your terminal, with jingles, DJs and adverts.
	"""


@output_dir_option(help_text="Path to write files to.")
@click.option("-i", "--install-dir", default=None, help="Path to the Cyberpunk 2077 installation.")
@flag_option("-v", "--verbose", help="Show individual tracks being processed.")
@main.command()
def extract(install_dir: str | None = None, output_dir: str = "data", verbose: bool = False) -> None:
	"""
	Extract relevant files and data from the game.
	"""

	# this package
	from cyberpunk_radio_simulator.config import Config
	from cyberpunk_radio_simulator.extractor import Extractor

	config = Config("config.toml")
	extractor = Extractor(config.get_install_dir(install_dir), config.get_output_dir(output_dir))

	# From quickest to slowest
	extractor.extract_app_icon()
	extractor.extract_album_art()
	extractor.extract_station_logos()
	extractor.extract_advert_audio()
	extractor.extract_dj_audio()
	extractor.extract_radio_tracks(verbose=verbose)


@station_option()
@output_dir_option()
@main.command()
def play(station_name: str, output_dir: str = "data") -> None:
	"""
	Play radio station in the terminal.
	"""

	# 3rd party

	# 3rd party
	from just_playback import Playback  # type: ignore[import-untyped]

	# this package
	from cyberpunk_radio_simulator.config import Config
	from cyberpunk_radio_simulator.data import stations
	from cyberpunk_radio_simulator.simulator import Radio, RadioStation

	config = Config("config.toml")

	# TODO: it played a song twice

	station_data = stations[station_name]

	print("Tuning to", station_name)

	radio = Radio(
			station=RadioStation(station_data, output_directory=config.get_output_dir(output_dir)),
			player=Playback(),
			)

	# Start with jingle
	# Loop:
	# 	Play 3-5 songs, then either:
	# 		- A link
	# 		- 1-3 ads and a jingle
	# 		- a jingle
	# Repeat

	print(f"Station has DJ? {radio.station.has_dj}")

	radio.play()


@theme_option()
@output_dir_option()
@main.command()
def gui(theme: str | None = None, output_dir: str = "data") -> None:
	"""
	Launch the Radioport GUI.
	"""

	# 3rd party
	from domdf_python_tools.paths import PathPlus

	# this package
	from cyberpunk_radio_simulator.config import Config
	from cyberpunk_radio_simulator.gui import RadioportApp

	config = Config("config.toml")

	app = RadioportApp()
	app.data_dir = PathPlus(config.get_output_dir(output_dir))

	if theme:
		app.theme = theme

	app.run()


@theme_option()
@output_dir_option()
@main.command()
def web(theme: str | None = None, output_dir: str = "data") -> None:
	"""
	Launch the Radioport web UI.
	"""

	# stdlib
	import shlex
	import sys

	# 3rd party
	from textual_serve.server import Server

	arguments = [shlex.quote(sys.executable), *get_subprocess_arguments(theme, output_dir)]
	server = Server(' '.join(arguments), title="Radioport")
	server.serve(debug=True)


@theme_option()
@output_dir_option()
@main.command()
def wrapper(theme: str | None = None, output_dir: str = "data") -> None:
	"""
	Launch the Radioport wrapper window.
	"""

	# this package
	from cyberpunk_radio_simulator.wrapper import Wrapper

	wrapper = Wrapper()
	wrapper.run(theme, output_dir)


if __name__ == "__main__":
	main()
