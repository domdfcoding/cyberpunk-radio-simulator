#!/usr/bin/env python3
#
#  scenes.py
"""
Extract data from game scenes.
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
from pathlib import PureWindowsPath

# 3rd party
from cp2077_extractor.audio_data.adverts import AdvertData, adverts
from cp2077_extractor.cr2w.io import parse_cr2w_buffer
from cp2077_extractor.radio_dj import EventData, parse_radio_scene_graph
from cp2077_extractor.redarchive_reader import REDArchive
from cp2077_extractor.utils import transcode_file
from domdf_python_tools.paths import PathPlus, TemporaryPathPlus
from domdf_python_tools.typing import PathLike
from moviepy.audio.AudioClip import CompositeAudioClip, concatenate_audioclips  # type: ignore[import-untyped]
from moviepy.audio.io.AudioFileClip import AudioFileClip  # type: ignore[import-untyped]
from networkx import Graph

__all__ = ["Extractor"]

advert_scenes = {
		PureWindowsPath(s).stem: s
		for s in [
				r"base\media\animated_billboards\scenes\ab_ad_caliente.scene",
				r"base\media\animated_billboards\scenes\ab_ad_chromanticore.scene",
				r"base\media\animated_billboards\scenes\ab_ad_foreign_body.scene",
				r"base\media\animated_billboards\scenes\ab_ad_mrstud.scene",
				r"base\media\animated_billboards\scenes\ab_ad_mrwhitey.scene",
				r"base\media\animated_billboards\scenes\ab_ad_nicola.scene",
				r"base\media\animated_billboards\scenes\ab_ad_orgiatic.scene",
				r"base\media\animated_billboards\scenes\ab_ad_slaughterhouse.scene",
				r"base\media\animated_billboards\scenes\ab_ad_sojasil.scene",
				r"base\media\animated_billboards\scenes\ab_ad_thrud.scene",
				r"base\media\animated_billboards\scenes\ab_ad_tiancha.scene",
				r"base\media\animated_billboards\scenes\ab_ad_vargas.scene",
				r"base\media\animated_billboards\scenes\ab_ad_watson_whore.scene",
				r"base\media\animated_billboards\scenes\ab_q003_01_all_foods_meat_ad.scene",
				r"base\media\animated_billboards\scenes\ab_q004_01_lizzies_bar_ad.scene",
				r"base\media\animated_billboards\scenes\ab_q104_01_kang_tao_ad.scene",
				r"base\media\animated_billboards\scenes\ab_q114_01_night_corp_ad.scene",
				r"base\media\animated_billboards\scenes\ab_q115_01_arasaka_propaganda.scene",
				r"base\media\animated_billboards\scenes\ab_sq017_01_us_cracks_ad.scene",
				r"base\media\animated_billboards\scenes\ab_sq025_01_delamain_ad.scene",
				r"base\media\animated_billboards\scenes\ab_sq032_01_arasaka_propaganda.scene",
				r"base\media\animated_billboards\scenes\ab_sts_wat_nid_04_televangelist_ad.scene",
				r"base\media\fluff\scenes\jefferson_peralez_ad\jefferson_peralez_ad.scene",
				r"base\media\quests\scenes\q203_01_crystal_palace_info.scene",
				]
		}


class Extractor:
	"""
	Extract game data.

	:param install_directory: Path to the Cyberpunk 2077 installation.
	:param output_directory: Directory to write files to.
	"""

	install_directory: PathPlus
	output_directory: PathPlus
	audio_output_directory: PathPlus
	advert_audio_directory: PathPlus

	gamedata_archive_file: PathPlus
	soundbanks_archive_file: PathPlus
	lang_en_voice_archive_file: PathPlus

	gamedata_archive: REDArchive
	soundbanks_archive: REDArchive
	lang_en_voice_archive: REDArchive

	def __init__(self, install_directory: PathLike, output_directory: PathLike = "data"):
		self.install_directory = PathPlus(install_directory)
		self.output_directory = PathPlus(output_directory)

		self.prepare_directories()

		self.gamedata_archive_file = self.install_directory / "archive/pc/content" / "basegame_4_gamedata.archive"
		assert self.gamedata_archive_file.is_file()

		self.soundbanks_archive_file = self.install_directory / "archive/pc/content" / "audio_2_soundbanks.archive"
		assert self.soundbanks_archive_file.is_file()

		self.lang_en_voice_archive_file = self.install_directory / "archive/pc/content" / "lang_en_voice.archive"
		assert self.lang_en_voice_archive_file.is_file()

		self.gamedata_archive = REDArchive.load_archive(self.gamedata_archive_file)
		self.soundbanks_archive = REDArchive.load_archive(self.soundbanks_archive_file)
		self.lang_en_voice_archive = REDArchive.load_archive(self.lang_en_voice_archive_file)

	def prepare_directories(self) -> None:
		"""
		Create output directories.
		"""

		self.output_directory.maybe_make()
		if not self.output_directory.joinpath(".gitignore").is_file():
			self.output_directory.joinpath(".gitignore").write_clean('*')

		self.audio_output_directory = self.output_directory / "audio"
		self.audio_output_directory.maybe_make()

		self.advert_audio_directory = self.audio_output_directory / "adverts"
		self.advert_audio_directory.maybe_make()

	def concatenate_advert_audio_clips(
			self, events: list[EventData], ad_data: AdvertData, output_file: PathPlus
			) -> None:
		"""
		Extract individual audio files and combine together into a single file.

		:param events:
		:param ad_data:
		:param output_file:
		"""

		audio_filename_prefix = ad_data.audio_filename_prefix + '_'

		with self.lang_en_voice_archive_file.open("rb") as lang_en_voice_fp, TemporaryPathPlus() as tmpdir:
			audio_filenames = []
			for event in events:
				event_filename = fr"base\localization\en-us\vo\{audio_filename_prefix}{event.audio_file_suffix.lower()}.wem"

				if ad_data.scene_file == "ab_ad_nicola":
					if event.audio_file_suffix.lower() == "f_1b8d42f0a04ea000":
						event_filename = event_filename.replace("female", "male")

				mp3_filename = tmpdir / f"{event.audio_file_suffix}.mp3"
				wem_filename = tmpdir / f"{event.audio_file_suffix}.wem"
				file = self.lang_en_voice_archive.file_list.find_filename(event_filename)
				contents = self.lang_en_voice_archive.extract_file(lang_en_voice_fp, file)
				wem_filename.write_bytes(contents)
				transcode_file(wem_filename, mp3_filename)
				audio_filenames.append(mp3_filename)

			clips = [AudioFileClip(c) for c in audio_filenames]
			final_clip: CompositeAudioClip = concatenate_audioclips(clips)
			final_clip.write_audiofile(output_file)

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


