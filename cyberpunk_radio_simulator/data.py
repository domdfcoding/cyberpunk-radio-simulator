#!/usr/bin/env python3
#
#  data.py
"""
Data for extraction and simulation.
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
from pathlib import PureWindowsPath
from typing import NamedTuple

# 3rd party
from cp2077_extractor.radio_dj import DJData

__all__ = ["djs", "advert_scenes", "dj_scenes", "StationData", "stations"]


class StationData(NamedTuple):
	"""
	Data about a radio station.
	"""

	#: The name of the radio station
	name: str

	#: The station's DJ, if any.
	dj: DJData | None = None

	#: Whether the station has adverts.
	has_ads: bool = True

	#: Whether the station has jingles.
	has_jingles: bool = True


# Has to be this way otherwise the linters and formats fight eachother.
djs: dict[str, DJData] = {}
djs["Ash"] = DJData(
		scene_file=r"radio_growl",
		station_name="89.7 Growl FM",
		audio_filename_prefix="ash_radio_growl",
		)
djs["Max Mike"] = DJData(
		scene_file=r"radio_01_conspiracy",
		station_name="107.3 Morro Rock Radio",
		audio_filename_prefix="radio_max_mike_radio_ad_00_test",
		general_audio=True,
		)
djs["Stanley"] = DJData(
		scene_file=r"radio_00_news",
		station_name="Stanley",
		audio_filename_prefix="stanley_media_radio_radio_ad_00_test",
		)

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

dj_scenes = {
		PureWindowsPath(s).stem: s
		for s in [
				r"base\media\radio\scenes\radio_00_news.scene",
				r"base\media\radio\scenes\radio_01_conspiracy.scene",
				# r"base\media\radio\scenes\radio_02_police.scene",
				r"base\media\radio\scenes\radio_growl.scene",
				]
		}

stations: dict[str, StationData] = {
		sd.name: sd
		for sd in [
				StationData("88.9 Pacific Dreams"),
				StationData("89.3 Radio Vexelstrom"),
				StationData("89.7 Growl FM", dj=djs["Ash"], has_ads=False),
				StationData("91.9 Royal Blue Radio"),
				StationData("92.9 Night FM"),
				StationData("95.2 Samizdat Radio"),
				StationData("96.1 Ritual FM"),
				StationData("98.7 Body Heat Radio"),
				StationData("99.9 Impulse", has_ads=False, has_jingles=False),
				StationData("101.9 The Dirge"),
				StationData("103.5 Radio PEBKAC"),
				StationData("106.9 30 Principales"),
				StationData(
						"107.3 Morro Rock Radio",
						dj=djs["Max Mike"],
						),  # TODO: filter out (and later program separately) the song intros/outros. TODO: played 274 as link on its own out of context
				StationData("107.5 Dark Star"),
				]
		}

# # See also ...\scenes\versions\gold\...
# target_scenes = {
# 		PureWindowsPath(s).stem: s
# 		for s in [

# 				# r"base\media\fluff\scenes\n54_news\n54_news_1_radio.scene",
# 				# r"base\media\fluff\scenes\n54_news\n54_news_10_radio.scene",
# 				# r"base\media\fluff\scenes\n54_news\n54_news_2_radio.scene",
# 				# r"base\media\fluff\scenes\n54_news\n54_news_3_radio.scene",
# 				# r"base\media\fluff\scenes\n54_news\n54_news_4_radio.scene",
# 				# r"base\media\fluff\scenes\n54_news\n54_news_5_radio.scene",
# 				# r"base\media\fluff\scenes\n54_news\n54_news_6_radio.scene",
# 				# r"base\media\fluff\scenes\n54_news\n54_news_7_radio.scene",
# 				# r"base\media\fluff\scenes\n54_news\n54_news_8_radio.scene",
# 				# r"base\media\fluff\scenes\n54_news\n54_news_9_radio.scene",
# 				# r"base\media\fluff\scenes\wns_news\wns_news_01_radio.scene",
# 				# r"base\media\fluff\scenes\wns_news\wns_news_02_radio.scene",
# 				# r"base\media\fluff\scenes\wns_news\wns_news_04_radio.scene",
# 				# r"base\media\fluff\scenes\wns_news\wns_news_05_radio.scene",
# 				# r"base\media\fluff\scenes\wns_news\wns_news_06_radio.scene",
# 				# r"base\media\fluff\scenes\wns_news\wns_news_07_radio.scene",
# 				# r"base\media\fluff\scenes\wns_news\wns_news_08_radio.scene",
# 				# r"base\media\fluff\scenes\wns_news\wns_news_09_radio.scene",
# 				# r"base\media\fluff\scenes\wns_news\wns_news_10_radio.scene",
# 				# r"base\media\fluff\scenes\ybimb\ybimb_1_radio.scene",
# 				# r"base\media\fluff\scenes\ybimb\ybimb_2_radio.scene",

# 				# r"base\open_world\scenes\ncpd_radio\ncpd_radio.scene",
# 				# r"base\sound\radio\radio_station_03_aggro_ind\advert\radio_station_03_aggro_ind_adver_test_001.scene",
# 				# r"ep1\media\radio\scenes\ep1_radio_03_kurt.scene",
# 				# r"ep1\media\radio\scenes\ep1_radio_04_mike.scene",
# 				# r"ep1\media\radio\scenes\ep1_radio_05_news.scene",
# 				# r"ep1\media\radio\scenes\ep1_radio_06_n54.scene",
# 				# r"ep1\media\radio\scenes\ep1_radio_07_wns.scene",
# 				#
# 				# # r"base\media\radio\radio_content.questphase",
# 				# # r"base\open_world\phases\radio\open_world_radio.questphase",
# 				# # r"base\quest\main_quests\prologue\q000\phases\q000_nomad_03_radio_tower.questphase",
# 				# # r"base\open_world\city_scenes\templates\noncombat\cs_kids_hitting_broken_advert\cs_kids_hitting_broken_advert.questphase",
# 				# # r"ep1\openworld\sandbox_activities\courier_spot\loop_phases\courier_droppoint_phases\courier_droppoint_ad.questphase",
# 				# # r"ep1\openworld\sandbox_activities\courier_spot\loop_phases\sa_ep1_additional_content_randomizer_advanced.questphase",
# 				# # r"ep1\openworld\sandbox_activities\courier_spot\loop_phases\sa_ep1_additional_content_randomizer_basic.questphase",
# 				# # r"ep1\openworld\sandbox_activities\courier_spot\loop_phases\sa_ep1_additional_content_randomizer.questphase",
# 				# # r"ep1\openworld\sandbox_activities\courier_spot\loop_phases\sa_ep1_courier_advanced_spots_reactivation.questphase",
# 				# # r"ep1\quest\bugfixing\ep1_additional_content_bugfixing.questphase",
# 				# # r"ep1\quest\ep1_additional_game_elements.questphase",
# 				]
# 		}
