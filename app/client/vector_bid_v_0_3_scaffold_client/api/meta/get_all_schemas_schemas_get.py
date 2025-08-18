from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_schemas_schemas_get_response_get_all_schemas_schemas_get import (
    GetAllSchemasSchemasGetResponseGetAllSchemasSchemasGet,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/schemas",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[GetAllSchemasSchemasGetResponseGetAllSchemasSchemasGet]:
    if response.status_code == 200:
        response_200 = GetAllSchemasSchemasGetResponseGetAllSchemasSchemasGet.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[GetAllSchemasSchemasGetResponseGetAllSchemasSchemasGet]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[GetAllSchemasSchemasGetResponseGetAllSchemasSchemasGet]:
    """Get All Schemas

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetAllSchemasSchemasGetResponseGetAllSchemasSchemasGet]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[GetAllSchemasSchemasGetResponseGetAllSchemasSchemasGet]:
    """Get All Schemas

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetAllSchemasSchemasGetResponseGetAllSchemasSchemasGet
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[GetAllSchemasSchemasGetResponseGetAllSchemasSchemasGet]:
    """Get All Schemas

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetAllSchemasSchemasGetResponseGetAllSchemasSchemasGet]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[GetAllSchemasSchemasGetResponseGetAllSchemasSchemasGet]:
    """Get All Schemas

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetAllSchemasSchemasGetResponseGetAllSchemasSchemasGet
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
