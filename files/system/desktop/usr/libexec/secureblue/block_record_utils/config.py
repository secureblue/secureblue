#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 Commenter25
#
# SPDX-License-Identifier: Apache-2.0

"""Class that represents a block-record config file, and manages R/W operations."""

import sys
from dataclasses import asdict, dataclass, field
from json import JSONDecodeError
from json import dump as write_json
from json import load as load_json
from typing import Final, TypeAlias, get_type_hints

from . import SCRIPT_CONFIG_PATH, ask_yes_no, is_tty, print_err

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None


@dataclass(slots=True)
class _ScriptConfig:
    """Represents the config state, and functions to manipulate it."""

    block_by_default: bool = field(init=False, default=False)
    allowed: list[str] = field(init=False, default_factory=list)
    blocked: list[str] = field(init=False, default_factory=list)

    def load(self) -> None:
        """Tries to load or create the config file."""
        try:
            with SCRIPT_CONFIG_PATH.open("r", encoding="utf-8") as f:
                loaded_file = load_json(f)
                self._validate_json(loaded_file)
                for key, value in loaded_file.items():
                    setattr(self, key, value)
                return None
        except FileNotFoundError:
            return self._create()
        except (JSONDecodeError, ValueError, TypeError) as e:
            print_err("Configuration invalid: " + e.args[0])
            if not is_tty:
                raise
        except (OSError, UnicodeDecodeError):
            print_err("Unable to open and parse configuration")
            if not is_tty:
                raise
        return self._no_config_found()

    def _no_config_found(self) -> None:
        """Asks if the user wants to reset the config, or if non-interactive, throws."""
        if not is_tty:
            raise RuntimeError("Unknown error occurred loading config")

        # in case the user wishes to recover the file
        if ask_yes_no("Would you like to continue with a blank configuration?"):
            return self._create()
        sys.exit(1)

    def _validate_json(self, loaded_file: dict[str, JSON]) -> None:
        """Ensures the structure of the config file is correct."""
        hints = get_type_hints(type(self))
        unknown_keys = loaded_file.keys() - hints.keys()
        if unknown_keys:
            raise ValueError("Unknown keys: " + str(unknown_keys))

        found_default = loaded_file.get("block_by_default")
        if type(found_default) is not bool:
            raise TypeError(f"Default must be true or false, but {found_default} was found")

        for name in ("allowed", "blocked"):
            to_check = loaded_file.get(name)
            if not isinstance(to_check, list):
                raise TypeError(f"{name} must be a list, but is {type(to_check)}")
            if not all(isinstance(v, str) for v in to_check):
                raise TypeError(f"All members of {name} must be a string")

    def _create(self) -> None:
        """Creates the config file."""
        SCRIPT_CONFIG_PATH.parent.mkdir(0o700, parents=True, exist_ok=True)
        SCRIPT_CONFIG_PATH.touch(0o600, exist_ok=True)
        self.write()

    def write(self) -> None:
        """Writes to the config file."""
        no_configuration = (
            (not CONFIG.block_by_default)
            and (len(CONFIG.blocked) == 0)
            and (len(CONFIG.allowed) == 0)
        )
        if no_configuration:
            # delete file to prevent unnecessary checks
            SCRIPT_CONFIG_PATH.unlink(missing_ok=True)
            return
        try:
            with SCRIPT_CONFIG_PATH.open("w", encoding="utf-8") as f:
                write_json(asdict(self), f, indent="\t")
        except Exception:
            print_err("Error writing to script config file?!")


CONFIG: Final[_ScriptConfig] = _ScriptConfig()
