#!/usr/bin/env python3
#
#  notifications.py
"""
Desktop notification support.
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
import sys
from typing import NamedTuple, TypeVar

# 3rd party
from domdf_python_tools.typing import PathLike
from notify_rs import URGENCY_NORMAL, Notification, NotificationHandle

__all__ = ["NotificationMessage", "NotificationSender"]

if sys.platform == "win32":
	_N = TypeVar("_N", bound=Notification)
else:
	_N = TypeVar("_N", Notification, NotificationHandle, covariant=True)


class NotificationMessage(NamedTuple):
	"""
	A message to show in the notification popup.
	"""

	#: Single line to summarize the content.
	summary: str

	#: Set the content of the body field.
	body: str

	#: Path to an icon to show in the notification.
	icon_file: PathLike

	def as_notification(self) -> Notification:
		"""
		Convert to a :class:`notify_rs.Notification`, but does not show it.
		"""

		return self.update(Notification())

	def update(self, notification: _N) -> _N:
		"""
		Updates the values in a :class:`notify_rs.Notification`, but does not show it.
		"""

		return notification.body(self.body).summary(self.summary).icon(self.icon_file)


class NotificationSender:
	"""
	Show notifications, reusing existing popups where possible.
	"""

	# TODO: support for Textual's notifications
	# TODO: I think macOS returns NotificationHandle but it can't do updates. Need a can_update flag.
	if sys.platform == "win32":
		notification_handle: None = None
	else:
		notification_handle: NotificationHandle | None = None

	@classmethod
	def send_message(cls, message: NotificationMessage, urgency: int = URGENCY_NORMAL) -> None:
		"""
		Send a notification with the given message.

		:param message:
		:param urgency:
		"""

		if cls.notification_handle:
			message.update(cls.notification_handle).timeout(5000).urgency(urgency).update()
		else:
			cls.notification_handle = message.as_notification().timeout(5000).urgency(urgency).show()

	@classmethod
	def send(cls, summary: str, body: str, icon_file: PathLike, urgency: int = URGENCY_NORMAL) -> None:
		"""
		Send a notification with the given summary, body and icon.

		:param summary:
		:param body:
		:param icon_file:
		:param urgency:
		"""

		cls.send_message(NotificationMessage(summary=summary, body=body, icon_file=icon_file), urgency)
