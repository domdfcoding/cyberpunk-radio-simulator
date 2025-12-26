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
import os
import signal
import sys
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

# 3rd party
import gi  # nodep
from domdf_python_tools.paths import PathPlus

# this package
from cyberpunk_radio_simulator.cli import get_subprocess_arguments
from cyberpunk_radio_simulator.media_control import SIGRAISE

gi.require_version("Gtk", "3.0")

if TYPE_CHECKING:
	# 3rd party
	from gi.repository import _Gtk3 as Gtk
else:
	# 3rd party
	from gi.repository import Gtk

gi.require_version("Vte", "2.91")  # vte-0.38 (gnome-3.14)

# 3rd party
from gi.repository import Gdk, Gio, GLib, Vte  # nodep  # noqa: E402

__all__ = ["MainWindow", "Terminal", "Wrapper"]


class Terminal(Vte.Terminal):
	"""
	Terminal for displaying a Textual app.
	"""

	can_use_sixel: bool = False

	@classmethod
	def new(cls) -> "Terminal":
		"""
		Create the terminal widget.
		"""

		self = Terminal()
		self.set_mouse_autohide(True)
		self.set_scroll_on_output(False)
		self.set_audible_bell(False)
		self.set_pty(self.pty_new_sync(Vte.PtyFlags.DEFAULT, None))
		self.set_word_char_exceptions("-,./?%&#:_")

		if hasattr(self, "set_enable_sixel"):
			self.set_enable_sixel(True)
			self.can_use_sixel = True

		return self

	def spawn_app(
			self,
			theme: str | None = None,
			output_directory: str = "data",
			callback: Callable[["Terminal", int, Any], None] | None = None,
			) -> None:
		"""
		Launch the Textual app in the terminal.

		:param theme: The Textual theme to use.
		:param output_directory: Directory containing files extracted from the game.
		:param callback: Function to call when the app has launched, which is passed the terminal, the child process id, and any errors.
		"""

		terminal_pty = self.get_pty()
		fd = cast(Gio.Cancellable, Vte.Pty.get_fd(terminal_pty))
		arguments = [sys.executable, *get_subprocess_arguments(theme, output_directory)]

		env = ["PS1='Radioport'", f"CPRS_WRAPPER_PID={os.getpid()}"]
		if self.can_use_sixel:
			env.append("CPRS_SIXEL=1")

		self.spawn_async(
				Vte.PtyFlags.DEFAULT,
				PathPlus(__file__).parent.parent.abspath().as_posix(),  # Working directory
				arguments,
				env,
				GLib.SpawnFlags.DO_NOT_REAP_CHILD,
				None,
				-1,
				fd,
				callback=callback,
				)


class MainWindow(Gtk.ScrolledWindow):
	"""
	The main window, containing the terminal widget.
	"""

	def __init__(self) -> None:
		super().__init__()

		self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		self.set_border_width(0)

	def add_widget(self, widget: Gtk.Widget) -> "MainWindow":
		"""
		Add a widget to the window.

		:param widget:
		"""

		Gtk.Container.add(self, widget)
		return self


class Wrapper(Gtk.Window):
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

		self.add(MainWindow().add_widget(cast(Gtk.Widget, self.terminal)))

		char_width, char_height = self.terminal.get_char_width(), self.terminal.get_char_height()
		width, height = 805, 600
		# print(char_width, char_height)
		# print(width, height)
		width = (width // char_width) * char_width + 2
		height = (height // char_height) * char_height + 2
		# print(width, height)

		self.set_default_size(width, height)
		self.set_border_width(0)
		self.set_icon_from_file("data/artwork/app_icon.png")

	def spawn_callback(self, terminal: Vte.Terminal, pid: int, error: Any | None) -> None:
		"""
		Handler for the app finishing spawning.

		Sets up a watcher for the process later exiting.

		:param terminal:
		:param pid: Process ID of the Textual app.
		:param error:
		"""

		if error:
			print(f"{terminal=}")
			print(f"{pid=}")
			print(f"{error=}")

		terminal.watch_child(pid)
		terminal.connect("child_exited", self.on_child_exited)

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
		self.terminal.spawn_app(theme=theme, output_directory=output_directory, callback=self.spawn_callback)
		self.connect("destroy", Gtk.main_quit)
		self.show_all()
		try:
			Gtk.main()
		except KeyboardInterrupt:
			sys.exit()
