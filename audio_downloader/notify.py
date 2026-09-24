"""SMTP notification policy. Secrets never enter messages or logs."""
from __future__ import annotations

import smtplib
from collections.abc import Iterable
from email.message import EmailMessage
from typing import Protocol

from .models import Outcome, SourceResult
from .settings import Settings


class NotificationSink(Protocol):
    def send(self, subject: str, body: str) -> None: ...


FAILURES = frozenset({Outcome.FAILED, Outcome.STALE, Outcome.UNVERIFIED})
FAILURE_VALUES = frozenset(str(outcome) for outcome in FAILURES)


def safe_send(notifier: NotificationSink, subject: str, body: str) -> None:
    """Notification transport failure cannot turn a published run into a failed run."""
    try:
        notifier.send(subject, body)
    except (OSError, smtplib.SMTPException, ValueError):
        return


class Notifier:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return bool(self.settings.smtp_host)

    def send(self, subject: str, body: str) -> None:
        if not self.enabled:
            return
        message = EmailMessage()
        message["From"], message["To"], message["Subject"] = self.settings.alert_from, self.settings.alert_to, subject
        message.set_content(body)
        password, host, username = self.settings.smtp_password, self.settings.smtp_host, self.settings.smtp_username
        if password is None or host is None or username is None:
            raise ValueError("SMTP configuration unavailable")
        with smtplib.SMTP(host, self.settings.smtp_port, timeout=30) as client:
            client.starttls()
            client.login(username, password.get_secret_value())
            client.send_message(message)


def notify_batch(notifier: NotificationSink, command: str, results: Iterable[SourceResult]) -> None:
    """Send post-retry alerts without including provider URLs or credentials."""
    completed = list(results)
    failures = [result for result in completed if result.outcome in FAILURES]
    if command == "weekly-run":
        for result in failures:
            safe_send(notifier, f"Audio weekly source failure: {result.source}", f"Outcome: {result.outcome}")
        summary = "\n".join(f"{result.source}: {result.outcome}" for result in completed)
        safe_send(notifier, "Audio weekly run summary", summary or "No sources ran")
    elif command == "nightly-retry":
        for result in failures:
            safe_send(notifier, f"Audio nightly retry failure: {result.source}", f"Outcome: {result.outcome}")


def notify_nbc_transition(notifier: NotificationSink, result: SourceResult, recent_outcomes: list[str]) -> None:
    """Alert once at second consecutive failure and once on recovery."""
    current, previous, before_previous = (recent_outcomes + [None, None, None])[:3]
    if result.outcome in FAILURES:
        if current in FAILURE_VALUES and previous in FAILURE_VALUES and before_previous not in FAILURE_VALUES:
            safe_send(notifier, "Audio NBC poll failure", "Two consecutive NBC polls failed.")
    elif result.outcome in {Outcome.SUCCESS, Outcome.IDLE} and previous in FAILURE_VALUES:
        safe_send(notifier, "Audio NBC poll recovered", f"NBC poll outcome: {result.outcome}")
