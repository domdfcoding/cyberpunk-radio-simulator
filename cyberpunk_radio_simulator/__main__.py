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
from consolekit.input import choice
from consolekit.options import flag_option, version_option
from consolekit.versions import get_version_callback
from natsort import natsorted

# this package
from cyberpunk_radio_simulator import __version__
from cyberpunk_radio_simulator.data import stations

__all__ = ["extract", "gui", "main", "play", "web"]


@version_option(
		get_version_callback(
				__version__,
				"cyberpunk-song-extractor",
				dependencies=("click", "cp2077-extractor"),
				)
		)
@click_group(cls=SuggestionGroup, invoke_without_command=False, context_settings=CONTEXT_SETTINGS)
def main() -> None:
	"""
	Play Cyberpunk 2077 radios in your terminal, with jingles, DJs and adverts.
	"""


@click.option("-o", "--output-dir", default="data", help="Path to write files to.")
@click.option("-i", "--install-dir", default=None, help="Path to the Cyberpunk 2077 installation.")
@flag_option("-v", "--verbose", help="Show individual tracks being processed.")
@main.command()
def extract(install_dir: str | None = None, output_dir: str = "data", verbose: bool = False) -> None:
	"""
	Extract relevant files and data from the game.
	"""

	# 3rd party
	import dom_toml

	# this package
	from cyberpunk_radio_simulator.extractor import Extractor
	config = dom_toml.load("config.toml")

	if not install_dir:
		install_dir = config["config"]["install_dir"]

	if "output_dir" in config["config"]:
		output_dir = config["config"]["output_dir"]

	assert isinstance(install_dir, str)
	assert isinstance(output_dir, str)

	assert isinstance(install_dir, str)

	extractor = Extractor(install_dir, output_dir)

	# From quickest to slowest
	extractor.extract_station_logos()
	extractor.extract_advert_audio()
	extractor.extract_dj_audio()
	extractor.extract_radio_tracks(verbose=verbose)


station_choices = natsorted(stations.keys())


@click.option(
		"-s",
		"--station",
		"station_name",
		help="The station to play.",
		type=click.Choice(station_choices, case_sensitive=False)
		)
@click.option("-o", "--output-dir", default="data", help="Path to the extracted game files.")
@main.command()
def play(station_name: str | None = None, output_dir: str = "data") -> None:
	"""
	Play radio station in the terminal.
	"""

	# 3rd party
	import dom_toml
	from just_playback import Playback  # type: ignore[import-untyped]

	# this package
	from cyberpunk_radio_simulator.simulator import Radio, RadioStation

	config = dom_toml.load("config.toml")

	if "output_dir" in config["config"]:
		output_dir = config["config"]["output_dir"]

	assert isinstance(output_dir, str)

	# TODO: it played a song twice

	if not station_name:
		station_name = station_choices[choice(station_choices, text="Select a station", start_index=1)]

	station_data = stations[station_name]
	# station_data = stations["98.7 Body Heat Radio"]
	# station_data = stations["89.7 Growl FM"]
	# station_data = stations["107.5 Dark Star"]

	print("Tuning to", station_name)

	radio = Radio(
			station=RadioStation(station_data, output_directory=output_dir),
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


@click.option("-o", "--output-dir", default="data", help="Path to the extracted game files.")
@main.command()
def gui(output_dir: str = "data") -> None:
	"""
	Launch the Radioport GUI.
	"""

	# 3rd party
	from domdf_python_tools.paths import PathPlus

	# this package
	from cyberpunk_radio_simulator.gui import RadioportApp

	app = RadioportApp()
	app.data_dir = PathPlus(output_dir)
	app.run()


@click.option("-o", "--output-dir", default="data", help="Path to the extracted game files.")
@main.command()
def web(output_dir: str = "data") -> None:
	"""
	Launch the Radioport web UI.
	"""

	# stdlib
	import sys

	# 3rd party
	from textual_serve.server import Server

	server = Server(' '.join([sys.executable, __file__, "gui", "-o", output_dir]))
	server.serve(debug=True)


if __name__ == "__main__":
	main()
