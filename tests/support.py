"""Offline credentials and Azure transport shared by SDK contract tests."""

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import click
import requests
from azure.core.credentials import AccessToken
from azure.core.pipeline.transport import RequestsTransport


def leaf_commands(group: click.Group, prefix: str = "") -> set[str]:
    result = set()
    for name, command in group.commands.items():
        path = f"{prefix} {name}".strip()
        if isinstance(command, click.Group):
            result.update(leaf_commands(command, path))
        else:
            result.add(path)
    return result


class Credential:
    def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
        return AccessToken("offline-token", 4102444800)

    def close(self) -> None:
        pass


class Transport(RequestsTransport):
    def __init__(self, responses: list[dict], status: int = 200) -> None:
        self.responses = iter(responses)
        self.status = status
        self.requests: list[Any] = []
        self.bodies: list[Any] = []
        session = MagicMock(spec=requests.Session)
        session.request.side_effect = self.respond
        super().__init__(session=session, session_owner=False)

    def respond(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        self.requests.append(SimpleNamespace(method=method, url=url, headers=kwargs["headers"]))
        body = kwargs.get("data")
        if hasattr(body, "read"):
            body = body.read()
        self.bodies.append(json.loads(body) if body else None)
        response = requests.Response()
        response.status_code = self.status
        response.url = url
        response.raw = MagicMock()
        response.headers["Content-Type"] = "application/json"
        response._content = json.dumps(next(self.responses)).encode() if self.status != 204 else b""
        response._content_consumed = True
        return response
