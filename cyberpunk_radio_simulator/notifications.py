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
from typing import NamedTuple, TypeVar

# 3rd party
from notify_rs import URGENCY_CRITICAL, Notification, NotificationHandle

__all__ = ["NotificationMessage", "NotificationSender"]

_N = TypeVar("_N", Notification, NotificationHandle)


class NotificationMessage(NamedTuple):
	"""
	A message to show in the notification popup.
	"""

	#: Single line to summarize the content.
	summary: str

	#: Set the content of the body field.
	body: str

	#: Path to an icon to show in the notification.
	icon_file: str

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
	notification_handle: NotificationHandle | None = None

	@classmethod
	def send_message(cls, message: NotificationMessage) -> None:
		"""
		Send a notification with the given message.
		"""

		if cls.notification_handle:
			message.update(cls.notification_handle).timeout(5000).urgency(URGENCY_CRITICAL).update()
		else:
			cls.notification_handle = message.as_notification().timeout(5000).urgency(URGENCY_CRITICAL).show()

	@classmethod
	def send(cls, summary: str, body: str, icon_file: str) -> None:
		"""
		Send a notification with the given summary, body and icon.
		"""

		cls.send_message(NotificationMessage(summary=summary, body=body, icon_file=icon_file))
