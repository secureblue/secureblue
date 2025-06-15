#!/usr/bin/python3

# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Framework for system auditing.
"""

import dataclasses
import enum
import inspect
import json

from collections.abc import Callable, Sequence
from typing import Any, AsyncGenerator, ClassVar, Final, Generator, Self


class AuditError(Exception):
    """Base class for audit errors."""


class Status(enum.Enum):
    """Status of a system check."""

    PASS = 0
    INFO = 1
    WARN = 2
    FAIL = 3
    UNKNOWN = 4

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
        return f"\x1b[{color_code}m{self.name}\x1b[39m"

    def downgrade_to(self, other: Self) -> Self:
        """Returns the more severe of the two statuses."""
        return max(self, other, key=lambda status: status.value)


@dataclasses.dataclass
class Recommendation:
    """A recommendation for user action to be taken."""

    text: str
    mergeable_name: str | None = None
    NAMES_PLACEHOLDER: ClassVar[Final[str]] = "[[NAMES_PLACEHOLDER]]"

    def __init__(self, rec: str | Self, mergeable_name: str | None = None):
        self.text = rec.text if isinstance(rec, Recommendation) else str(rec)
        if isinstance(rec, Recommendation):
            self.text = rec.text
        else:
            self.text = str(rec)
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
    warnings: list[str]
    recs: list[Recommendation]

    def __init__(
        self,
        desc: str,
        status: Status,
        *,
        warnings: str | Sequence[str] | None = None,
        recs: str | Recommendation | Sequence[str | Recommendation] | None = None,
    ):
        self.description = desc
        self.status = status
        if warnings is None:
            self.warnings = []
        elif isinstance(warnings, str):
            self.warnings = [warnings]
        else:
            self.warnings = list(warnings)
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
        desc_width = width - len(self.status.name) - 5 + len(gray_start)
        reset_color = "\x1b[39m"
        desc_with_sep = f"{self.description} {gray_start}".ljust(desc_width, "…") + reset_color
        report_str = desc_with_sep + status_tag
        for warning in self.warnings:
            warning_lines = [line.strip() for line in warning.splitlines() if line.strip()]
            if warning_lines:
                report_str += "\n> " + warning_lines[0]
            for line in warning_lines[1:]:
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


def print_heading(text: str, width: int = 80):
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


def _print_recs(recs: list[Recommendation], width: int = 80):
    print_heading("Recommendations", width=width)
    merged_recs_data = {rec.text: [] for rec in recs if rec.mergeable_name is not None}
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

    def add_check(self, check: Check):
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
        if exclude is None:
            exclude = []
        print_heading("Audit", width=width)
        if exclude:
            category_word = "category" if len(exclude) == 1 else "categories"
            print(f"Skipping checks in the following {category_word}: {', '.join(exclude)}")
        for check in self.checks:
            if check.category in exclude:
                continue
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
                recs = [
                    {"text": rec.text, "mergeable_name": rec.mergeable_name} for rec in report.recs
                ]
                yield json.dumps(
                    {
                        "name": check.name,
                        "category": check.category,
                        "description": report.description,
                        "status": report.status.name.lower(),
                        "warnings": report.warnings,
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

        async def f_async(*args, **kwargs):
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

    def add_dependencies(f) -> Check:
        check = make_check(f)
        check.dependencies += list(dependencies)
        return check

    return add_dependencies


def categorize(cat: str) -> Callable[..., Check]:
    """Mark a check as belonging to a given category."""

    def add_category(f) -> Check:
        check = make_check(f)
        check.category = cat
        return check

    return add_category
