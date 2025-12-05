#!/usr/bin/env python3
#
#  extractor.py
"""
Extract logic from game scenes, and audio files.
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
from io import BytesIO
from typing import IO

# 3rd party
from cp2077_extractor.audio_data import SceneAudioData
from cp2077_extractor.audio_data.adverts import adverts
from cp2077_extractor.cr2w.io import parse_cr2w_buffer
from cp2077_extractor.radio_dj import (
		EventData,
		find_graph_entry_points,
		get_link_paths,
		parse_radio_scene_graph,
		parse_subtitles
		)
from cp2077_extractor.redarchive_reader import REDArchive
from cp2077_extractor.utils import transcode_file
from cyberpunk_radio_extractor import extract_radio_songs
from cyberpunk_radio_extractor.album_art import get_album_art, get_station_logos
from domdf_python_tools.paths import PathPlus, TemporaryPathPlus
from domdf_python_tools.typing import PathLike
from moviepy.audio.AudioClip import CompositeAudioClip, concatenate_audioclips  # type: ignore[import-untyped]
from moviepy.audio.io.AudioFileClip import AudioFileClip  # type: ignore[import-untyped]
from networkx import Graph

# this package
from cyberpunk_radio_simulator.data import advert_scenes, dj_scenes, djs

__all__ = ["Extractor"]


class Directories:
	"""
	Base class with information on the data directory structure.

	:param output_directory: Directory to write files to.
	"""

	output_directory: PathPlus
	audio_output_directory: PathPlus
	advert_audio_directory: PathPlus
	dj_audio_directory: PathPlus
	stations_audio_directory: PathPlus
	dj_data_directory: PathPlus
	artwork_directory: PathPlus
	station_logos_directory: PathPlus

	def __init__(self, output_directory: PathLike = "data"):
		self.output_directory = PathPlus(output_directory)

		self.prepare_directories()

	def prepare_directories(self, create_missing: bool = False) -> None:
		"""
		Create output directories.
		"""

		self.audio_output_directory = self.output_directory / "audio"
		self.dj_data_directory = self.output_directory / "dj"
		self.artwork_directory = self.output_directory / "artwork"

		self.advert_audio_directory = self.audio_output_directory / "adverts"
		self.dj_audio_directory = self.audio_output_directory / "dj"
		self.stations_audio_directory = self.audio_output_directory / "stations"

		self.station_logos_directory = self.artwork_directory / "stations"

		if create_missing:
			self.output_directory.maybe_make()
			if not self.output_directory.joinpath(".gitignore").is_file():
				self.output_directory.joinpath(".gitignore").write_clean('*')

			self.advert_audio_directory.maybe_make(parents=True)
			self.dj_audio_directory.maybe_make(parents=True)
			self.stations_audio_directory.maybe_make(parents=True)
			self.dj_data_directory.maybe_make(parents=True)
			self.station_logos_directory.maybe_make(parents=True)


class Extractor(Directories):
	"""
	Extract game data.

	:param install_directory: Path to the Cyberpunk 2077 installation.
	:param output_directory: Directory to write files to.
	"""

	install_directory: PathPlus

	gamedata_archive_file: PathPlus
	soundbanks_archive_file: PathPlus
	lang_en_voice_archive_file: PathPlus
	audio_general_archive_file: PathPlus

	gamedata_archive: REDArchive
	soundbanks_archive: REDArchive
	lang_en_voice_archive: REDArchive
	audio_general_archive: REDArchive

	def __init__(self, install_directory: PathLike, output_directory: PathLike = "data"):
		super().__init__(output_directory)

		self.install_directory = PathPlus(install_directory)

		self.gamedata_archive_file = self.install_directory / "archive/pc/content" / "basegame_4_gamedata.archive"
		assert self.gamedata_archive_file.is_file()

		self.soundbanks_archive_file = self.install_directory / "archive/pc/content" / "audio_2_soundbanks.archive"
		assert self.soundbanks_archive_file.is_file()

		self.lang_en_voice_archive_file = self.install_directory / "archive/pc/content" / "lang_en_voice.archive"
		assert self.lang_en_voice_archive_file.is_file()

		self.audio_general_archive_file = self.install_directory / "archive/pc/content" / "audio_1_general.archive"
		assert self.audio_general_archive_file.is_file()

		self.gamedata_archive = REDArchive.load_archive(self.gamedata_archive_file)
		self.soundbanks_archive = REDArchive.load_archive(self.soundbanks_archive_file)
		self.lang_en_voice_archive = REDArchive.load_archive(self.lang_en_voice_archive_file)
		self.audio_general_archive = REDArchive.load_archive(self.audio_general_archive_file)

	def concatenate_advert_audio_clips(
			self,
			events: list[EventData],
			ad_data: SceneAudioData,
			output_file: PathPlus,
			) -> None:
		"""
		Extract individual audio files and combine together into a single file.

		:param events:
		:param ad_data:
		:param output_file:
		"""

		audio_filename_prefix = ad_data.audio_filename_prefix + '_'

		# TODO: add attribute to advert class
		if hasattr(ad_data, "general_audio") and ad_data.general_audio:
			archive_file = self.audio_general_archive_file
			archive = self.audio_general_archive
			directory = r"base\localization\common\vo"
		else:
			archive_file = self.lang_en_voice_archive_file
			archive = self.lang_en_voice_archive
			directory = r"base\localization\en-us\vo"

		with archive_file.open("rb") as fp, TemporaryPathPlus() as tmpdir:
			audio_filenames: list[PathPlus] = []
			for event in events:
				event_filename = fr"{directory}\{audio_filename_prefix}{event.audio_file_suffix.lower()}.wem"

				if ad_data.scene_file == "ab_ad_nicola":
					if event.audio_file_suffix.lower() == "f_1b8d42f0a04ea000":
						event_filename = event_filename.replace("female", "male")

				mp3_filename = tmpdir / f"{event.audio_file_suffix}.mp3"
				self.extract_audio(archive, fp, event_filename, mp3_filename)
				audio_filenames.append(mp3_filename)

			if len(audio_filenames) > 1:
				clips = [AudioFileClip(c) for c in audio_filenames]
				final_clip: CompositeAudioClip = concatenate_audioclips(clips)
				final_clip.write_audiofile(output_file)
			else:
				audio_filenames[0].move(output_file.abspath())

	def extract_audio(self, archive: REDArchive, fp: IO, filename: str, mp3_filename: PathPlus) -> None:
		"""
		Extract audio file from the archive, as MP3.

		:param archive:
		:param fp: Open file handle to the archive.
		:param filename: The file in the archive.
		:param mp3_filename: Output filename.
		"""

		wem_filename = mp3_filename.with_suffix(".wem")
		file = archive.file_list.find_filename(filename)
		contents = archive.extract_file(fp, file)
		wem_filename.write_bytes(contents)
		transcode_file(wem_filename, mp3_filename)

	def extract_advert_audio(self) -> tuple[Graph, dict[int, list[EventData]]]:
		"""
		Extract audio for adverts.
		"""

		with self.gamedata_archive_file.open("rb") as gamedata_fp:

			for ad_name, ad_data in adverts.items():
				print(ad_data, ad_name)

				file = self.gamedata_archive.file_list.find_filename(advert_scenes[ad_data.scene_file])
				crw2_file = parse_cr2w_buffer(BytesIO(self.gamedata_archive.extract_file(gamedata_fp, file)))

				graph, audio_events = parse_radio_scene_graph(crw2_file)

				for node_id, events in audio_events.items():
					# print([e.audio_file_suffix.lower() for e in events])

					output_file = self.advert_audio_directory / f"{ad_name}.mp3"
					if not output_file.is_file():
						self.concatenate_advert_audio_clips(events, ad_data, output_file)

		return graph, audio_events

	def extract_dj_audio(self) -> tuple[Graph, dict[int, list[EventData]]]:
		"""
		Extract audio for radio DJs.
		"""

		with self.gamedata_archive_file.open("rb") as gamedata_fp:

			for dj_data in djs.values():
				print(dj_data)

				file = self.gamedata_archive.file_list.find_filename(dj_scenes[dj_data.scene_file])
				crw2_file = parse_cr2w_buffer(BytesIO(self.gamedata_archive.extract_file(gamedata_fp, file)))

				subtitles = parse_subtitles(crw2_file)

				graph, audio_events = parse_radio_scene_graph(crw2_file)

				output_dir = self.dj_audio_directory / dj_data.station_name
				output_dir.maybe_make()

				for node_id, events in audio_events.items():
					output_file = output_dir / f"{node_id}_{len(events)}.mp3"
					if not output_file.is_file():
						self.concatenate_advert_audio_clips(events, dj_data, output_file)

				lone_nodes, start_nodes, end_nodes = find_graph_entry_points(graph)
				combinations = list(get_link_paths(graph))
				output_data = {
						"link_paths": combinations,
						"start_nodes": start_nodes,
						"lone_nodes": lone_nodes,
						"end_nodes": end_nodes,
						"audio_events": audio_events,
						"subtitles": subtitles,
						}
				self.dj_data_directory.joinpath(dj_data.audio_filename_prefix + "_data.json").dump_json(
						output_data, indent=2
						)

		return graph, audio_events

	def extract_radio_tracks(self) -> None:
		"""
		Extract the tracks that play on the radio stations.
		"""

		album_art_data = get_album_art(self.install_directory)

		extract_radio_songs(
				self.install_directory,
				self.stations_audio_directory,
				album_art_data=album_art_data,
				jingles=True,
				verbose=True,
				)

	def extract_station_logos(self) -> None:
		"""
		Extract the logos for the radio stations.
		"""

		station_logos = get_station_logos(self.install_directory)

		for station_name, logo_png_bytes in station_logos.items():
			self.station_logos_directory.joinpath(f"{station_name}.png").write_bytes(logo_png_bytes)
