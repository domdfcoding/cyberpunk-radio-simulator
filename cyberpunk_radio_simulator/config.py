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

# stdlib
import os
from typing import Any

# 3rd party
import dom_toml
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from notify_rs import URGENCY_CRITICAL, URGENCY_LOW, URGENCY_NORMAL

__all__ = ["Config"]

urgency_map = {
		"critical": URGENCY_CRITICAL,
		"low": URGENCY_LOW,
		"normal": URGENCY_NORMAL,
		}


class Config:
	"""
	Access application config.

	:param config_file: File to read config from.
	"""

	def __init__(self, config_file: PathLike = "config.toml"):
		if not os.path.isfile(config_file):
			raise FileNotFoundError(config_file)

		config: dict[str, Any] = dom_toml.load(config_file)

		if "config" not in config:
			raise KeyError(f"'config' table not found in {config_file}")

		self._config = config["config"]

	def get_install_dir(self, override: str | None = None) -> PathPlus:
		"""
		Get the Cyberpunk 2077 install directory.

		:param override: A value to override the one in the config file, e.g. from the command line.
		"""

		path = override or self._config["install_dir"]
		if not isinstance(path, str):
			raise ValueError(f"Invalid install directory {path!r}")

		return PathPlus(path)

	def get_output_dir(self, override: str | None = None) -> PathPlus:
		"""
		Get the directory containing the extracted game files.

		:param override: A value to override the one in the config file, e.g. from the command line.
		"""

		path = override or self._config["output_dir"]
		if not isinstance(path, str):
			raise ValueError(f"Invalid output/data directory {path!r}")

		return PathPlus(path)

	def get_notification_urgency(self) -> int:
		"""
		Get the notification urgency.
		"""

		notifications_table: dict[str, str] = self._config.get("notifications", {})
		notification_urgency = notifications_table.get("urgency", "normal").lower()

		if notification_urgency not in urgency_map:
			raise ValueError(f"Invalid urgency value {notification_urgency!r}")

		return urgency_map[notification_urgency]
