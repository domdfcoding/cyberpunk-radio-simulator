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
import signal
import sys
from typing import Any, cast

# 3rd party
import gi  # nodep
from textual_wrapper.types import MenuOption  # nodep
from textual_wrapper.wrapper import Wrapper as WrapperCls  # nodep
from textual_wrapper.wrapper.gtk import MainWindow, Terminal, WrapperWindow  # nodep
from textual_wrapper.wrapper.unity import WrapperWindow  # nodep

# this package
from cyberpunk_radio_simulator.media_control import SIGRAISE

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Vte", "2.91")  # vte-0.38 (gnome-3.14)

# 3rd party
from gi.repository import Gdk, Gtk, Vte  # nodep  # noqa: E402

__all__ = ["Wrapper"]


class Wrapper(WrapperWindow):
	"""
	Standalone terminal wrapper for the app.

	Displays the app in a libVTE terminal window, like `gnome-terminal` but without the standard terminal functionality.
	Closes when the app exits.
	"""

	def __init__(self):
		wrapper = WrapperCls(
				name="Radioport",
				arguments=[],
				icon="data/artwork/app_icon.png",
				launcher_options=[
						MenuOption("Play/Pause", 'p'),
						MenuOption("Mute", 'm'),
						MenuOption("Next Station", '>'),
						MenuOption("Previous Station", '<'),
						],
				menu_options={"_File": [MenuOption("Command _Palette", '\x10')]},
				)

		Gtk.Window.__init__(self, title=wrapper.name)

		self.terminal = Terminal.new()
		self.terminal.set_color_background(Gdk.RGBA(0.071, 0.071, 0.071, 1.0))
		# Matches background colour of default textual theme.

		self.menu_options: dict[Gtk.MenuItem, bytes] = {}
		menubar = self.create_menu_options(wrapper.menu_options)

		self.launcher_options: dict[str, bytes] = {
				"Play/Pause": b"p",
				"Mute": b"m",
				"Next Station": b">",
				"Previous Station": b"<",
				}

		box = Gtk.HBox()
		self.add(box)
		box.pack_start(menubar, False, True, 0)
		box.add(MainWindow().add_widget(cast(Gtk.Widget, self.terminal)))

		self.set_window_size((805, 600))
		self.set_border_width(0)
		if wrapper.icon:
			self.set_icon_from_file(wrapper.icon)
		self.set_wmclass(wrapper.name.lower(), wrapper.name)

	def on_child_exited(self, terminal: Vte.Terminal, status: int) -> None:
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
			# TODO: this doesn't always bring it to the foreground, only wiggle the tray icon.
			self.present()

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

		signal.signal(SIGRAISE, self.on_raise_signal)
		super().run(arguments=arguments, working_directory=working_directory)
