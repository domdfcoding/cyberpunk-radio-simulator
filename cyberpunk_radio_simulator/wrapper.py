#!/usr/bin/env python3
#
#  wrapper.py
"""
Standalone terminal wrapper for the app.

.. extras-require:: wrapper
	:pyproject:
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
import posixpath
import signal
import sys
import time
from typing import TYPE_CHECKING, Any

# 3rd party
from domdf_python_tools.typing import PathLike
from textual_wrapper.keycodes import CTRL_P
from textual_wrapper.types import MenuOption, Wrapper
from textual_wrapper.wrapper import gtk

# this package
from cyberpunk_radio_simulator.cli import get_subprocess_arguments
from cyberpunk_radio_simulator.media_control import SIGRAISE

if TYPE_CHECKING:
	# 3rd party
	from gi.repository import Vte  # nodep  # noqa: E402

__all__ = ["WrapperWindow", "setup_wrapper"]


def setup_wrapper(theme: str | None = None, output_directory: PathLike = "data") -> Wrapper:
	"""
	Creates the wrapper instance with menu and launcher options.

	:param theme: The Textual theme to use.
	:param output_directory: Directory containing files extracted from the game.
	"""

	arguments = [sys.executable, *get_subprocess_arguments(theme, output_directory)]

	return gtk.WrapperGtk(
			name="Radioport",
			arguments=arguments,
			icon=posixpath.join(output_directory, "artwork/app_icon.png"),
			launcher_options=[
					MenuOption("Play/Pause", 'p'),
					MenuOption("Mute", 'm'),
					MenuOption("Previous Station", '<'),
					MenuOption("Next Station", '>'),
					],
			menu_options={"_File": [MenuOption("Command _Palette", CTRL_P)]},
			wrapper_window_cls=WrapperWindow
			)


class WrapperWindow(gtk.WrapperWindow):
	"""
	Standalone terminal wrapper for the app.

	Displays the app in a libVTE terminal window, like `gnome-terminal` but without the standard terminal functionality.
	Closes when the app exits.
	"""

	def on_child_exited(self, terminal: "Vte.Terminal", status: int) -> None:
		"""
		Handler for the process running in the terminal exiting.

		Closes the wrapper window.

		:param terminal:
		:param status:
		"""

		# print(f"{terminal=}")
		# print(f"{status=}")
		sys.exit(status)

	def on_raise_signal(self, signalnum: int, stack_frame: Any) -> None:
		"""
		Handler for the raise signal (``SIGUSR1``) being sent to the application.

		Brings the application to the foreground.

		:param signalnum: The signal number.
		:param stack_frame:
		"""

		if signalnum == SIGRAISE:
			self.set_keep_above(True)
			self.present()
			time.sleep(0.001)
			self.set_keep_above(False)

	def run(
			self,
			arguments: list[str],
			working_directory: str,
			) -> None:
		"""
		Show the wrapper window and launch the Textual app.

		:param arguments: The app executable and any arguments to pass to it.
		:param working_directory: Directory to execute the application in.
		"""

		self.terminal.hide_cursor()
		# TODO: disable selection (maybe clear selection when selection changes?)

		signal.signal(SIGRAISE, self.on_raise_signal)
		super().run(arguments=arguments, working_directory=working_directory)
