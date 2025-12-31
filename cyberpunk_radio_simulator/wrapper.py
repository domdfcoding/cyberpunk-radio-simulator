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
from domdf_python_tools.paths import PathPlus
from textual_wrapper.wrapper.gtk import MainWindow, Terminal, WrapperWindow

# this package
from cyberpunk_radio_simulator.cli import get_subprocess_arguments
from cyberpunk_radio_simulator.media_control import SIGRAISE

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Vte", "2.91")  # vte-0.38 (gnome-3.14)
gi.require_version("Unity", "7.0")
gi.require_version("Dbusmenu", "0.4")

# 3rd party
from gi.repository import Dbusmenu, Gdk, Gtk, Unity, Vte  # nodep  # noqa: E402

__all__ = ["Wrapper"]


class Wrapper(WrapperWindow):
	"""
	Standalone terminal wrapper for the app.

	Displays the app in a libVTE terminal window, like `gnome-terminal` but without the standard terminal functionality.
	Closes when the app exits.
	"""

	def __init__(self):
		Gtk.Window.__init__(self, title="Radioport")

		self.terminal = Terminal.new()
		self.terminal.set_color_background(Gdk.RGBA(0.071, 0.071, 0.071, 1.0))
		# Matches background colour of default textual theme.

		menubar = self.create_menu_options()

		box = Gtk.HBox()
		self.add(box)
		box.pack_start(menubar, False, True, 0)
		box.add(MainWindow().add_widget(cast(Gtk.Widget, self.terminal)))

		self.set_window_size((805, 600))
		self.set_border_width(0)
		self.set_icon_from_file("data/artwork/app_icon.png")
		self.set_wmclass("radioport", "Radioport")

	def on_menu_command_palette_clicked(self, item: Gtk.MenuItem) -> None:
		"""
		Handler for the ``File`` -> ``Command Palette`` button being clicked.

		:param item:
		"""

		self.terminal.feed_child(b"\x10")  # Ctrl+p

	def on_launcher_menuitem_clicked(self, item: Dbusmenu.Menuitem, timestamp: int) -> None:
		"""
		Handler for a Unity Launcher rightclick menu item being clicked.

		:param item: The clicked item.
		:param timestamp:
		"""

		action = item.property_get(Dbusmenu.MENUITEM_PROP_LABEL)
		print("Clicked", action, timestamp)

		if action == "Play/Pause":
			self.terminal.feed_child(b"p")
		elif action == "Mute":
			self.terminal.feed_child(b"m")
		elif action == "Next Station":
			self.terminal.feed_child(b">")
		elif action == "Previous Station":
			self.terminal.feed_child(b"<")
			# self.terminal.feed_child(b"\x10")  # Ctrl+p
			# self.terminal.feed_child(b"\x1b[21~")  # F10

	def create_menu_options(self) -> Gtk.MenuBar:
		"""
		Create the menubar options.
		"""

		menubar = Gtk.MenuBar()
		menuitem = Gtk.MenuItem.new_with_mnemonic(label="_File")
		submenu = Gtk.Menu()
		submenuitem = Gtk.MenuItem.new_with_mnemonic(label="Command _Palette")
		submenuitem.connect("activate", self.on_menu_command_palette_clicked)
		submenu.append(submenuitem)
		menuitem.set_submenu(submenu)
		menubar.append(menuitem)

		return menubar

	def create_launcher_options(self) -> None:
		"""
		Create the Unity launcher rightclick menu options.
		"""

		# TODO: gate on desktop file existing and us launching in way to use it (no spaces in install path)
		launcher = Unity.LauncherEntry.get_for_desktop_id("radioport.desktop")

		ql = Dbusmenu.Menuitem.new()

		for action in ["Play/Pause", "Mute", "Next Station", "Previous Station"]:
			menuitem = Dbusmenu.Menuitem.new()
			menuitem.property_set(Dbusmenu.MENUITEM_PROP_LABEL, action)
			menuitem.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, True)
			menuitem.connect(Dbusmenu.MENUITEM_SIGNAL_ITEM_ACTIVATED, self.on_launcher_menuitem_clicked)
			ql.child_append(menuitem)

		launcher.set_property("quicklist", ql)

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

	def run(self, theme: str | None = None, output_directory: str = "data") -> None:
		"""
		Show the wrapper window and launch the Textual app.

		:param theme: The Textual theme to use.
		:param output_directory: Directory containing files extracted from the game.
		"""

		signal.signal(SIGRAISE, self.on_raise_signal)
		arguments = [sys.executable, *get_subprocess_arguments(theme, output_directory)]
		working_directory = PathPlus(__file__).parent.parent.abspath().as_posix()
		super().run(arguments, working_directory)
