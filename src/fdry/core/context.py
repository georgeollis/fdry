"""Per-invocation settings and deterministic SDK client lifetimes."""

from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass, field
from typing import Any

import click
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from openai import OpenAI

from fdry.core.config import SETTING_ENV, validate_endpoint
from fdry.core.output import emit


@dataclass
class Runtime:
    profile: str
    settings: dict[str, str]
    output: str = "json"
    preview: bool = False
    stack: ExitStack = field(default_factory=ExitStack)
    _credential: DefaultAzureCredential | None = field(default=None, init=False, repr=False)
    _project: AIProjectClient | None = field(default=None, init=False, repr=False)
    _management: CognitiveServicesManagementClient | None = field(
        default=None, init=False, repr=False
    )
    _openai: OpenAI | None = field(default=None, init=False, repr=False)

    def require(self, key: str) -> str:
        value = self.settings.get(key)
        if not value or not value.strip():
            option = key.replace("_", "-")
            raise click.UsageError(
                f"Set --{option}, {SETTING_ENV[key]}, or config set {key} VALUE."
            )
        return value

    def credential(self) -> DefaultAzureCredential:
        if self._credential is None:
            self._credential = DefaultAzureCredential()
            self.stack.callback(self._credential.close)
        return self._credential

    def project_client(self) -> AIProjectClient:
        if self._project is None:
            endpoint = validate_endpoint(self.require("endpoint"))
            self._project = self.stack.enter_context(
                AIProjectClient(
                    endpoint=endpoint, credential=self.credential(), allow_preview=self.preview
                )
            )
        return self._project

    def management_client(self) -> CognitiveServicesManagementClient:
        if self._management is None:
            subscription = self.require("subscription")
            self._management = self.stack.enter_context(
                CognitiveServicesManagementClient(self.credential(), subscription)
            )
        return self._management

    def openai_client(self) -> OpenAI:
        if self._openai is None:
            self._openai = self.stack.enter_context(self.project_client().get_openai_client())
        return self._openai

    def account_args(self) -> tuple[str, str]:
        return self.require("resource_group"), self.require("account")

    def connection_args(self) -> tuple[str, str, str]:
        return (*self.account_args(), self.require("project"))

    def emit(self, value: Any) -> None:
        emit(value, self.output)


pass_runtime = click.make_pass_decorator(Runtime)
