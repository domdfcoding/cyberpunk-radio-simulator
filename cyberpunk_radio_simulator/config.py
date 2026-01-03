#!/usr/bin/env python3
#
#  config.py
"""
Config file handling.
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

# TODO: use platformdirs and have file (and output data) in .config

# stdlib
from typing import Any

# 3rd party
import attrs
import dom_toml
import platformdirs
from dom_toml import config
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from notify_rs import URGENCY_CRITICAL, URGENCY_LOW, URGENCY_NORMAL
from typing_extensions import Self

__all__ = ["Config", "GuiConfig", "NotificationsConfig", "find_config_file"]

urgency_map = {
		"critical": URGENCY_CRITICAL,
		"low": URGENCY_LOW,
		"normal": URGENCY_NORMAL,
		}


@attrs.define
class GuiConfig(config.Config):
	"""
	Configuration for the Textual-based GUI.
	"""

	resume_last_station: bool | None = None
	last_station: str | None = None
	theme: str | None = None
	playback_animation: str | None = None  # "bars" or "sine"

	# TODO: window size/position?

	# TODO
	# def get_resume_last_station(self, override: bool | None = None, default: bool = False) -> bool:
	# 	"""
	# 	Whether to resume the last station played when opening.

	# 	:param override: A value to override the one in the config file, e.g. from the command line.
	# 	:param default: The default value if not set.
	# 	"""

	# 	if override is not None:
	# 		return override
	# 	elif self.resume_last_station is not None:
	# 		return self.resume_last_station
	# 	else:
	# 		return default

	# TODO
	# def get_last_station(self, override: str | None = None) -> str | None:
	# 	"""
	# 	Get the last station played.

	# 	:param override: A value to override the one in the config file, e.g. from the command line.
	# 	"""

	# 	if not self.get_resume_last_station():
	# 		return None

	# 	station = override or self.last_station

	# 	if station is None:
	# 		return None

	# 	if not isinstance(station, str):
	# 		raise ValueError(f"last_station must be a string.")

	# 	return station

	def get_theme(self, override: str | None = None) -> str | None:
		"""
		Get the theme.

		:param override: A value to override the one in the config file, e.g. from the command line.
		"""

		theme = override or self.theme

		if theme is None:
			return None

		if not isinstance(theme, str):
			raise ValueError(f"Theme must be a string.")

		return theme

	def get_playback_animation(self, override: str | None = None, default: str = "bars") -> str:
		"""
		Get the logo style (white or album art).

		:param override: A value to override the one in the config file, e.g. from the command line.
		:param default: The default value if not set.
		"""

		style = override or self.playback_animation or default

		if not isinstance(style, str):
			raise ValueError("playback_animation must be a string.")

		style = style.lower().replace('_', ' ').strip()

		if style not in {"bars", "sine"}:
			raise ValueError(f"Invalid playback_animation {style!r}")

		return style


@attrs.define
class NotificationsConfig(config.Config):
	"""
	Configuration for notifications.
	"""

	urgency: str | None = None  # "critical" or "low" or "normal"
	logo_style: str | None = None  # "white" or "album art"

	# TODO
	# def get_logo_style(self, override: str | None = None, default: str = "white") -> str:
	# 	"""
	# 	Get the logo style (white or album art).

	# 	:param override: A value to override the one in the config file, e.g. from the command line.
	# 	:param default: The default value if not set.
	# 	"""

	# 	style = override or self.logo_style or default

	# 	if not isinstance(style, str):
	# 		raise ValueError("logo_style must be a string.")

	# 	style = style.lower().replace('_', ' ').strip()

	# 	if style not in {"white", "album art"}:
	# 		raise ValueError(f"Invalid logo_style {style!r}")

	# 	return style

	def get_urgency(self, override: str | None = None, default: str = "normal") -> int:
		"""
		Get the notification urgency.

		:param override: A value to override the one in the config file, e.g. from the command line.
		:param default: The default value if not set.
		"""

		notification_urgency = override or self.urgency or default

		if notification_urgency is None:
			raise ValueError(f"Urgency cannot be None")

		notification_urgency = notification_urgency.lower()

		if notification_urgency not in urgency_map:
			raise ValueError(f"Invalid urgency value {notification_urgency!r}")

		return urgency_map[notification_urgency]


@attrs.define
class Config(config.Config):
	"""
	Application configuration.
	"""

	install_dir: PathPlus | None = None
	output_dir: PathPlus | None = None
	notifications: NotificationsConfig = config.subtable_field(NotificationsConfig)
	gui: GuiConfig = config.subtable_field(GuiConfig)

	#: The file the config was read from.
	config_file: PathPlus | None = None

	@classmethod
	def load(cls: type[Self]) -> Self:
		"""
		Detect the config file and load the configuration from it.
		"""

		file = find_config_file()

		if not file:
			raise FileNotFoundError(f"Config file 'config.toml' or 'radioport.toml' not found.")

		self = cls.from_file(file)
		self.config_file = file
		return self

	@classmethod
	def from_file(cls: type[Self], config_file: PathLike) -> Self:
		"""
		Load configuration from the given file.

		:param config_file:
		"""

		file = PathPlus(config_file)
		if not file.is_file():
			raise FileNotFoundError(f"Config file {file.as_posix()!r} not found.")

		config: dict[str, Any] = dom_toml.load(config_file)

		if "config" not in config:
			raise KeyError(f"'config' table not found in {config_file}")

		return cls.from_dict(config["config"])

	def get_install_dir(self, override: str | None = None) -> PathPlus:
		"""
		Get the Cyberpunk 2077 install directory.

		:param override: A value to override the one in the config file, e.g. from the command line.
		"""

		path = override or self.install_dir

		if not isinstance(path, str):
			raise ValueError(f"Invalid install directory {path!r}")

		return PathPlus(path)

	def get_output_dir(self, override: str | None = None, default: PathLike = "data") -> PathPlus:
		"""
		Get the directory containing the extracted game files.

		:param override: A value to override the one in the config file, e.g. from the command line.
		:param default: The default value if not set.
		"""

		path = override or self.output_dir or default

		if path is None:
			raise ValueError(f"Invalid output/data directory: None")

		path_p = PathPlus(path)

		if not path_p.is_absolute():
			if self.config_file:
				parent = self.config_file.parent
			else:
				parent = PathPlus('.').abspath()

			return parent / path_p

		return path_p


def find_config_file() -> PathPlus | None:
	"""
	Find the config file (``config.toml`` or ``radioport.toml``) in the current directory or its parents.

	Returns :py:obj:`None` if not found.
	"""

	cwd = PathPlus.cwd()
	home_dir = PathPlus.home()
	config_dir = PathPlus(
			platformdirs.user_config_path(
					appname="radioport",
					appauthor="domdfcoding",
					ensure_exists=False,
					)
			)

	for directory in [cwd, *cwd.parents, config_dir]:
		for filename in ("config.toml", "radioport.toml"):
			path = directory / filename
			if path.is_file():
				return path

		if directory == home_dir:
			break

	# TODO: use platformdirs config directory

	return None
