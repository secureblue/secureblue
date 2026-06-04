#!/usr/bin/python3

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Auditing utilities for containers-policy.json. For documentation on the format, see:
https://github.com/containers/image/blob/main/docs/containers-policy.json.5.md
"""

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ContainersPolicyError(Exception):
    """The provided containers policy is invalid."""


def policy_requirements_secure(requirements: Sequence[Mapping[str, Any]]) -> bool:
    """Assess if a list of container policy requirements are secure."""
    try:
        return any(req["type"] in ("reject", "signedBy", "sigstoreSigned") for req in requirements)
    except (KeyError, TypeError) as e:
        raise ContainersPolicyError('container policy requirements must have a "type" field') from e


@dataclass
class TransportPolicyAudit:
    """Audit of container policy for a specific transport."""

    default_secure: bool
    insecure_scopes: list[str]

    @staticmethod
    def from_data(scopes: Mapping[str, Sequence[Mapping[str, Any]]]) -> "TransportPolicyAudit":
        """Analyze container transport policy from given JSON data."""
        default_secure = True
        insecure_scopes = []

        for scope, scope_policy in scopes.items():
            if scope == "":
                default_secure = policy_requirements_secure(scope_policy)
            elif not policy_requirements_secure(scope_policy):
                insecure_scopes.append(scope)

        insecure_scopes.sort()

        return TransportPolicyAudit(default_secure, insecure_scopes)


@dataclass
class ContainersPolicyAudit:
    """Audit of contents of containers-policy.json"""

    default_secure: bool
    transports: dict[str, TransportPolicyAudit]

    @staticmethod
    def from_data(policy: Mapping[str, Any]) -> "ContainersPolicyAudit":
        """Parse containers policy from JSON data."""
        try:
            default = policy["default"]
        except KeyError as e:
            raise ContainersPolicyError(
                'key "default" is mandatory for containers-policy.json'
            ) from e

        default_secure = policy_requirements_secure(default)

        transports = policy.get("transports", {})
        transport_audits = {
            name: TransportPolicyAudit.from_data(scopes) for name, scopes in transports.items()
        }
        return ContainersPolicyAudit(default_secure, transport_audits)

    @staticmethod
    def from_file(path: str | Path) -> "ContainersPolicyAudit":
        """Parse containers policy from a file."""
        try:
            with open(path, "rb") as f:
                policy = json.load(f)
        except json.decoder.JSONDecodeError as e:
            raise ContainersPolicyError from e

        return ContainersPolicyAudit.from_data(policy)
