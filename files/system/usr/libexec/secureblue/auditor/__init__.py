#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Framework for system auditing.
"""

import dataclasses
import enum
import gettext
import inspect
import json
from collections.abc import AsyncGenerator, Callable, Generator, Sequence
from typing import Any, ClassVar, Final, Self


def gettext_marker() -> Callable[[str], str]:
    """Get the _ function used by gettext to mark translatable strings."""
    return gettext.translation("audit_secureblue", "/usr/share/locale", fallback=True).gettext


_: Final = gettext_marker()


class AuditError(Exception):
    """Base class for audit errors."""


class Status(enum.Enum):
    """Status of a system check."""

    PASS = 0
    INFO = 1
    WARN = 2
    FAIL = 3
    UNKNOWN = 4

    def local_name(self) -> str:
        """Get localized name."""
        match self:
            case Status.PASS:
                return _("PASS")
            case Status.INFO:
                return _("INFO")
            case Status.WARN:
                return _("WARN")
            case Status.FAIL:
                return _("FAIL")
            case Status.UNKNOWN:
                return _("UNKNOWN")

    def to_str_in_color(self) -> str:
        """Colored text representation of the status."""
        match self:
            case Status.PASS:
                color_code = 32  # green
            case Status.INFO:
                color_code = 36  # cyan
            case Status.WARN:
                color_code = 33  # yellow
            case Status.FAIL:
                color_code = 31  # red
            case Status.UNKNOWN:
                color_code = 37  # white
        return f"\x1b[{color_code}m{self.local_name()}\x1b[39m"

    def icon(self) -> str:
        """Colored icon associated with status."""
        match self:
            case Status.PASS:
                icon = "✅"
            case Status.INFO:
                icon = "ℹ️"  # noqa: RUF001
            case Status.WARN:
                icon = "⚠️"
            case Status.FAIL:
                icon = "❌"
            case Status.UNKNOWN:
                icon = "❔"
        return icon

    def width(self) -> int:
        """Printable width of status."""
        return len(self.local_name())

    def downgrade_to(self, other: Self) -> Self:
        """Returns the more severe of the two statuses."""
        return max(self, other, key=lambda status: status.value)


@dataclasses.dataclass
class Note:
    """A line with additional info and optionally a status."""

    text: str
    status: Status | None = None

    def __init__(self, note: str | Self, status: Status | None = None):
        self.text = note.text if isinstance(note, Note) else str(note)
        if status is not None:
            self.status = status
        elif isinstance(note, Note):
            self.status = note.status
        else:
            self.status = None


@dataclasses.dataclass
class Recommendation:
    """A recommendation for user action to be taken."""

    text: str
    mergeable_name: str | None = None
    NAMES_PLACEHOLDER: ClassVar[Final[str]] = "[[NAMES_PLACEHOLDER]]"

    def __init__(self, rec: str | Self, mergeable_name: str | None = None):
        self.text = rec.text if isinstance(rec, Recommendation) else str(rec)
        if mergeable_name is not None:
            self.mergeable_name = mergeable_name
        elif isinstance(rec, Recommendation):
            self.mergeable_name = rec.mergeable_name
        else:
            self.mergeable_name = None


class Report:
    """A result of a check to be reported."""

    description: str
    status: Status
    notes: list[Note]
    recs: list[Recommendation]

    def __init__(
        self,
        desc: str,
        status: Status,
        *,
        notes: str | Note | Sequence[str | Note] | None = None,
        recs: str | Recommendation | Sequence[str | Recommendation] | None = None,
    ):
        self.description = desc
        self.status = status
        if notes is None:
            self.notes = []
        elif isinstance(notes, (str, Note)):
            self.notes = [Note(notes)]
        else:
            self.notes = [Note(note) for note in notes]
        if recs is None:
            self.recs = []
        elif isinstance(recs, (str, Recommendation)):
            self.recs = [Recommendation(recs)]
        else:
            self.recs = [Recommendation(rec) for rec in recs]

    def to_str(self, width: int = 80) -> str:
        """Represent the report as a string formatted to the given width."""
        status_tag = f" [ {self.status.to_str_in_color()} ]"
        gray_start = "\x1b[38;5;241m"
        desc_width = width - self.status.width() - 5 + len(gray_start)
        reset_color = "\x1b[39m"
        desc_with_sep = f"{self.description} {gray_start}".ljust(desc_width, "…") + reset_color
        report_str = desc_with_sep + status_tag
        for note in self.notes:
            note_lines = [line.strip() for line in note.text.splitlines() if line.strip()]
            if note_lines:
                icon = ">" if note.status is None else note.status.icon()
                report_str += f"\n{icon} " + note_lines[0]
            for line in note_lines[1:]:
                report_str += "\n  " + line
        return report_str


@dataclasses.dataclass
class Check:
    """A single check done as part of an audit."""

    name: str
    callback: Callable[..., AsyncGenerator[Report]]
    category: str | None = None
    stateful: bool = False
    dependencies: list[str] = dataclasses.field(default_factory=list)
    done: bool = False
    reports: list[Report] = dataclasses.field(default_factory=list)
    recs: list[Recommendation] = dataclasses.field(default_factory=list)

    async def run(
        self, state: dict[str, Any] | None = None, rerun: bool = False
    ) -> AsyncGenerator[Report]:
        """Run the check and store the results."""
        if self.done and not rerun:
            return
        if self.stateful:
            if state is None:
                state = {}
            gen = (self.callback)(state)
        else:
            gen = (self.callback)()
        async for report in gen:
            self.reports.append(report)
            self.recs += report.recs
            yield report
        self.done = True


def bold(text: str) -> str:
    """Bolds the text using ANSI escape codes."""
    return f"\x1b[1m{text}\x1b[22m"


def print_heading(text: str, width: int = 80) -> None:
    """Formats the text as a heading and prints to the terminal."""
    print(f"\n\x1b[1;38;5;228m\x1b[48;5;63m{text}\x1b[0m")
    print("=" * width)


class DependencyError(AuditError):
    """A check's dependency requirements were not satisfied."""


def _format_recommendation_text(rec_text: str, mergeable_names: list[str] | None = None) -> str:
    rec_lines_raw = [line.strip() for line in rec_text.splitlines() if line.strip()]
    rec_lines_formatted = []
    name_text_lines = [] if mergeable_names is None else ["  " + name for name in mergeable_names]
    for line in rec_lines_raw:
        if line == Recommendation.NAMES_PLACEHOLDER:
            rec_lines_formatted += name_text_lines
        elif line[0] in ("$", "#"):
            rec_lines_formatted.append(bold(line))
        else:
            rec_lines_formatted.append(line)
    return "\n  ".join(rec_lines_formatted) + "\n"


def _print_recs(recs: list[Recommendation], width: int = 80) -> None:
    print_heading(_("Recommendations"), width=width)
    merged_recs_data: dict[str, list[str]] = {
        rec.text: [] for rec in recs if rec.mergeable_name is not None
    }
    for rec in recs:
        if rec.mergeable_name is None:
            # Print non-mergeable recommendations first
            print(_format_recommendation_text(rec.text))
        else:
            merged_recs_data[rec.text].append(rec.mergeable_name)
    for rec_template, names in merged_recs_data.items():
        print(_format_recommendation_text(rec_template, mergeable_names=names))


class Audit:
    """A system audit."""

    def __init__(self):
        self.checks: list[Check] = []
        self.state: dict[str, Any] = {}
        self.recs: list[Recommendation] = []
        self.categories: set[str] = set()

    def names(self) -> list[str]:
        """Get a list of the names of all checks."""
        return [check.name for check in self.checks]

    def add_check(self, check: Check) -> None:
        """Add the check to the queue to be run."""
        names = self.names()
        for dep in check.dependencies:
            if dep not in names:
                raise DependencyError(f"'{check.name}' requires '{dep}' to be run first.")
        if check.category is not None:
            self.categories.add(check.category)
        self.checks.append(check)

    async def run(
        self, *, exclude: list[str] | None = None, width: int = 80
    ) -> AsyncGenerator[tuple[Check, Exception]]:
        """Runs each stored check, prints their reports, then prints their recommendations."""
        print_heading(_("Audit"), width=width)
        if exclude is None:
            exclude = []
        elif len(exclude) == 1:
            print(_("Skipping checks in the following category:"), ", ".join(exclude))
        elif len(exclude) > 1:
            print(_("Skipping checks in the following categories:"), ", ".join(exclude))
        checks = [check for check in self.checks if check.category not in exclude]
        for check in checks:
            try:
                async for report in check.run(self.state):
                    print(report.to_str(width=width))
            # pylint: disable=broad-exception-caught
            except Exception as e:
                yield check, e
            else:
                self.recs += check.recs
        _print_recs(self.recs)

    async def run_json(self, exclude: list[str] | None = None) -> AsyncGenerator[str]:
        """Runs each stored check and prints the results as JSON."""
        if exclude is None:
            exclude = []
        for check in self.checks:
            if check.category in exclude:
                continue
            async for report in check.run(self.state):
                notes = [
                    {
                        "text": note.text,
                        "status": None if note.status is None else note.status.name.lower(),
                    }
                    for note in report.notes
                ]
                recs = [
                    {"text": rec.text, "mergeable_name": rec.mergeable_name} for rec in report.recs
                ]
                yield json.dumps(
                    {
                        "name": check.name,
                        "category": check.category,
                        "description": report.description,
                        "status": report.status.name.lower(),
                        "notes": notes,
                        "recommendations": recs,
                    }
                )


global_audit = Audit()


def make_check(
    f: Check | Callable[..., AsyncGenerator[Report]] | Callable[..., Generator[Report]],
) -> Check:
    """Make a Check object from a generator."""
    if isinstance(f, Check):
        return f
    stateful = bool(len(inspect.signature(f).parameters))
    if inspect.isasyncgenfunction(f):
        return Check(name=f.__name__, callback=f, stateful=stateful)

    if inspect.isgeneratorfunction(f):

        async def f_async(*args: Any, **kwargs: Any) -> AsyncGenerator:
            for item in f(*args, **kwargs):
                yield item

        return Check(name=f.__name__, callback=f_async, stateful=stateful)

    raise TypeError("invalid input to make_check")


def audit(
    f: Check | Callable[..., AsyncGenerator[Report]] | Callable[..., Generator[Report]],
) -> Check:
    """Add a check to the global audit system."""
    check = make_check(f)
    global_audit.add_check(check)
    return check


def depends_on(*dependencies: str) -> Callable[..., Check]:
    """Add a dependency to a check."""

    def add_dependencies(f: Check | Callable) -> Check:
        check = make_check(f)
        check.dependencies += list(dependencies)
        return check

    return add_dependencies


def categorize(cat: str) -> Callable[..., Check]:
    """Mark a check as belonging to a given category."""

    def add_category(f: Check | Callable) -> Check:
        check = make_check(f)
        check.category = cat
        return check

    return add_category
