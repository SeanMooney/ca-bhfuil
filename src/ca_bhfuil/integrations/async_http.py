"""Asynchronous HTTP client using httpx."""

import typing

import httpx

class AsyncHTTPClient:
    """An asynchronous HTTP client with connection pooling."""

    def __init__(self, base_url: str = "", headers: dict[str, str] | None = None):
        self._base_url = base_url
        self._headers = headers or {}
        self._client = httpx.AsyncClient(base_url=self._base_url, headers=self._headers)

    async def get(self, url: str, params: dict[str, typing.Any] | None = None) -> httpx.Response:
        """Perform an async GET request."""
        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            # Handle HTTP errors (e.g., 404, 500)
            raise e
        except httpx.RequestError as e:
            # Handle network errors (e.g., connection refused)
            raise e

    async def close(self):
        """Close the underlying httpx client."""
        await self._client.aclose()
