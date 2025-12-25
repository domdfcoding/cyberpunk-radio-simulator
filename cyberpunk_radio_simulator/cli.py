#!/usr/bin/env python3
#
#  cli.py
"""
Helper functions for the click command line.
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
from collections.abc import Callable, Iterable, Sequence
from typing import TypeVar

# 3rd party
import click
from consolekit.input import choice
from natsort import natsorted

__all__ = [
		"ChoiceOption",
		"LazyChoice",
		"get_stations",
		"get_subprocess_arguments",
		"get_textual_themes",
		"output_dir_option",
		"station_option",
		"theme_option",
		]

_C = TypeVar("_C", bound=click.Command)


class LazyChoice(click.Choice[str]):
	"""
	Modified choice type that lazily loads the data.

	Useful for expensive operations that need not happen if the option is not provided or the help text is not being displayed.

	:param getter: Function that returns the actual choices.
	:param case_sensitive: Set to :py:obj:`False` to make choices case insensitive.
	"""

	_choices: Sequence[str] | None = None

	def __init__(
			self,
			getter: Callable[[], Iterable[str]],
			case_sensitive: bool = True,
			) -> None:
		self._getter = getter

		self.case_sensitive = case_sensitive

	@property
	def choices(self) -> Sequence[str]:  # type: ignore[override]
		"""
		The choices, obtained from the getter function and cached.
		"""

		if self._choices is None:
			choices = tuple(self._getter())
			self._choices = choices

		return self._choices


def get_stations() -> list[str]:
	"""
	Returns the sorted list of radio station names.
	"""

	# this package
	from cyberpunk_radio_simulator.data import stations

	return natsorted(stations.keys())


def get_textual_themes() -> list[str]:
	"""
	Returns the sorted list of available Textual themes.
	"""

	# 3rd party
	from textual.app import App
	from textual.theme import BUILTIN_THEMES

	themes = getattr(App, "_registered_themes", {})
	themes.update(BUILTIN_THEMES)
	return sorted(themes)


def station_option() -> Callable[[_C], _C]:
	"""
	Adds the ``--station`` option to the decorated command.

	The parameter is available as ``station_name`` in the command's function signature.
	"""

	return click.option(
			"-s",
			"--station",
			"station_name",
			help="The station to play.",
			type=LazyChoice(get_stations, case_sensitive=False),
			cls=ChoiceOption,
			prompt="Select a station",
			)


def theme_option() -> Callable[[_C], _C]:
	"""
	Adds the ``--theme`` option to the decorated command.
	"""

	return click.option(
			"-t", "--theme", help="The theme to use.", type=LazyChoice(get_textual_themes, case_sensitive=False)
			)


def output_dir_option(help_text: str = "Path to the extracted game files.") -> Callable[[_C], _C]:
	"""
	Adds the ``--output-dir`` option to the decorated command.

	:param help_text:
	"""

	return click.option("-o", "--output-dir", default="data", help=help_text)


def get_subprocess_arguments(theme: str | None = None, output_directory: str = "data") -> list[str]:
	"""
	Returns arguments to use when invoking the program through a wrapper.

	:param theme: The Textual theme to use.
	:param output_directory: Directory containing files extracted from the game.
	"""

	arguments = ["-m", "cyberpunk_radio_simulator", "gui", "-o", output_directory]

	if theme:
		arguments.extend(["--theme", theme])

	return arguments


class ChoiceOption(click.Option):
	"""
	:class:`click.Option` subclass for a string choice.

	If a value is not provided a prompt (where the user chooses the corresponding number) is shown.

	:param param_decls: The parameter declarations for this option.
	:param type: The type that should be used.
	:param show_default: Show the default value for this option in its help text.
		Values are not shown by default, unless :attr:`Context.show_default` is :py:obj:`True`.
		If this value is a string, it shows that string in parentheses instead of the actual value.
		This is particularly useful for dynamic options.
		For single option boolean flags, the default remains hidden if its value is :py:obj:`False`.
	:param prompt: The prompt text. Defaults to the option name (capitalised and with spaces) if unset.
	:param help: The help text.
	:param hidden: Hide this option from help outputs.
	:param show_choices:
	:param deprecated: If :py:obj:`True` or a non-empty string, issues a message indicating that the argument is deprecated
		and highlights its deprecation in --help.
		The message can be customized by using a string as the value.
		A deprecated parameter cannot be required, a ValueError will be raised otherwise.
	"""

	type: click.Choice[str]
	prompt: str

	def __init__(
			self,
			param_decls: Sequence[str],
			type: click.Choice[str],  # noqa: A002  # pylint: disable=redefined-builtin
			show_default: bool | str | None = None,
			prompt: str = '',
			help: str | None = None,  # noqa: A002  # pylint: disable=redefined-builtin
			hidden: bool = False,
			show_choices: bool = True,
			deprecated: bool | str = False,
			) -> None:

		super().__init__(
				param_decls=param_decls,
				show_default=show_default,
				prompt=prompt or True,
				help=help,
				hidden=hidden,
				show_choices=show_choices,
				deprecated=deprecated,
				type=type,
				default=None,
				)

	def prompt_for_value(self, ctx: click.Context) -> str:
		"""
		Show the prompt if a value was not provided.

		:param ctx:
		"""
		choices = list(self.type.choices)
		return choices[choice(choices, text=self.prompt, start_index=1)]
