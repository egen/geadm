"""Shared offline test doubles — no GCP access anywhere in the suite."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
import requests


def http_error(status: int) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status
    return requests.HTTPError(response=response)


class FakeDiscoveryClient:
    def __init__(self, engines: list | None = None, data_stores: list | None = None):
        self._engines = engines or []
        self._data_stores = data_stores or []

    def list_engines(self, parent: str):
        return list(self._engines)

    def list_data_stores(self, parent: str):
        return list(self._data_stores)


class FakeClients:
    """Duck-type of geadm.auth.Clients for collector tests."""

    def __init__(
        self,
        engines: list | None = None,
        data_stores: list | None = None,
        rest_responses: dict[str, Any] | None = None,
        log_entries: list | None = None,
    ):
        self.project = "test-project"
        self.location = "global"
        self._discovery = FakeDiscoveryClient(engines, data_stores)
        # path -> dict response, int -> raise HTTPError(status)
        self._rest = rest_responses or {}
        self.rest_calls: list[str] = []
        self.logging = SimpleNamespace(
            list_entries=lambda **kwargs: list(log_entries or [])
        )

    @property
    def collection_path(self) -> str:
        return (
            f"projects/{self.project}/locations/{self.location}"
            "/collections/default_collection"
        )

    @property
    def monitoring_project_path(self) -> str:
        return f"projects/{self.project}"

    def discoveryengine(self, client_cls: type) -> Any:
        return self._discovery

    def rest_get(self, path: str, params=None, host=None) -> dict:
        self.rest_calls.append(path)
        for key, value in self._rest.items():
            if key in path:
                if isinstance(value, int):
                    raise http_error(value)
                return value
        raise http_error(404)


def engine(engine_id: str, display_name: str = "An Engine") -> SimpleNamespace:
    return SimpleNamespace(
        name=f"projects/p/locations/global/collections/default_collection/engines/{engine_id}",
        display_name=display_name,
        solution_type=SimpleNamespace(name="SOLUTION_TYPE_SEARCH"),
        industry_vertical=SimpleNamespace(name="GENERIC"),
        data_store_ids=["ds-1"],
        create_time=None,
    )


@pytest.fixture
def app_runner():
    from typer.testing import CliRunner

    return CliRunner()
