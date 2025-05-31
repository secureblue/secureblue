#!/usr/bin/python3

"""
Framework for system auditing.
"""

import enum
import inspect
import json

from collections.abc import Callable, Sequence
from typing import Any, AsyncGenerator, Generator, Self


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


class Report:
    """A result of a check to be reported."""

    def __init__(
        self,
        desc: str,
        status: Status,
        *,
        warnings: str | list[str] | None = None,
        recs: str | list[str] | None = None,
    ):
        self.description = desc
        self.status = status
        if warnings is None:
            self.warnings = []
        elif isinstance(warnings, str):
            self.warnings = [warnings]
        else:
            self.warnings = warnings
        if recs is None:
            self.recs = []
        elif isinstance(recs, str):
            self.recs = [recs]
        else:
            self.recs = recs

    def to_str(self, width: int = 80) -> str:
        """Represent the report as a string formatted to the given width."""
        status_tag = f" [ {self.status.to_str_in_color()} ]"
        desc_width = width - len(self.status.name) - 5
        gray_start = "\x1b[38;5;241m"
        reset_color = "\x1b[39m"
        desc_with_sep = f"{self.description} {gray_start}".ljust(desc_width, "…") + reset_color
        report_str = desc_with_sep + status_tag
        for warning in self.warnings:
            report_str += f"\n> {warning}"
        return report_str


class Check:
    """A single check done as part of an audit."""

    def __init__(
        self,
        name: str,
        callback: Callable[..., AsyncGenerator[Report]],
        *,
        stateful: bool = False,
        category: str | None = None,
        dependencies: Sequence[str] | None = None,
    ):
        self.name = name
        self.callback = callback
        self.category = category
        self.stateful = stateful
        if dependencies is None:
            self.dependencies = []
        else:
            self.dependencies = dependencies
        self.done = False
        self.reports: list[Report] = []
        self.recs: list[str] = []

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


class Audit:
    """A system audit."""

    def __init__(self):
        self.checks: list[Check] = []
        self.state: dict[str, Any] = {}
        self.recs: list[str] = []
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
            except Exception as e:
                yield check, e
            else:
                self.recs += check.recs
        print_heading("Recommendations", width=width)
        for rec in self.recs:
            rec_lines = [line.strip() for line in rec.split("\n")]
            for i, line in enumerate(rec_lines):
                if not line:
                    continue
                if line[0] in ["$", "#"]:
                    rec_lines[i] = bold(line)
            print("\n  ".join(rec_lines) + "\n")

    async def run_json(self, exclude: list[str] | None = None) -> AsyncGenerator[str]:
        """Runs each stored check and prints the results as JSON."""
        if exclude is None:
            exclude = []
        for check in self.checks:
            if check.category in exclude:
                continue
            async for report in check.run(self.state):
                yield json.dumps(
                    {
                        "name": check.name,
                        "category": check.category,
                        "description": report.description,
                        "status": report.status.name.lower(),
                        "warnings": report.warnings,
                        "recommendations": report.recs,
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
        check.dependencies = dependencies
        return check

    return add_dependencies


def categorize(cat: str) -> Callable[..., Check]:
    """Mark a check as belonging to a given category."""

    def add_category(f) -> Check:
        check = make_check(f)
        check.category = cat
        return check

    return add_category
