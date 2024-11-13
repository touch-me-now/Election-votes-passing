import logging
from functools import cached_property
from json import JSONDecodeError
from typing import Any
from urllib.parse import urljoin

import httpx

from core.config import settings


class AsyncBaseAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    @cached_property
    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient()

    async def process_request(self, request):
        pass

    async def process_response(self, response):
        try:
            return response.json()
        except (JSONDecodeError, ValueError) as err:
            logging.error(err)
            response.raise_for_status()
            raise

    async def _request(self, method: str, path: str, **kwargs):
        url = urljoin(self.base_url, path)
        request = self.client.build_request(method, url, **kwargs)
        await self.process_request(request)
        response = await self.client.send(request)
        return await self.process_response(response)

    async def _get(self, path: str, params: dict[str, Any] = None) -> Any:
        return await self._request('GET', path, params=params)


class ElectionAPIClient(AsyncBaseAPIClient):
    def __init__(self, election_id: int):
        base_url = settings.election_base_url
        if not settings.election_base_url.endswith("/"):
            base_url += "/"

        super().__init__(base_url=base_url + f"/{election_id}/")

    async def ballot_count(self, election_type: str, division_id: int):
        return await self._get("ballot-count", params={"type": election_type, "id": division_id})
