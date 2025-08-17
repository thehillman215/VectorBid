from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.export_export_post_payload import ExportExportPostPayload
from ...models.export_export_post_response_export_export_post import (
    ExportExportPostResponseExportExportPost,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: ExportExportPostPayload,
    api_key: Union[None, Unset, str] = UNSET,
    x_api_key: Union[None, Unset, str] = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_api_key, Unset):
        headers["x-api-key"] = x_api_key

    params: dict[str, Any] = {}

    json_api_key: Union[None, Unset, str]
    if isinstance(api_key, Unset):
        json_api_key = UNSET
    else:
        json_api_key = api_key
    params["api_key"] = json_api_key

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/export",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ExportExportPostResponseExportExportPost, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = ExportExportPostResponseExportExportPost.from_dict(
            response.json()
        )

        return response_200
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ExportExportPostResponseExportExportPost, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ExportExportPostPayload,
    api_key: Union[None, Unset, str] = UNSET,
    x_api_key: Union[None, Unset, str] = UNSET,
) -> Response[Union[ExportExportPostResponseExportExportPost, HTTPValidationError]]:
    r"""Export

     Protected when VECTORBID_API_KEY is set.
    Accepts: {\"artifact\": {...}}
    Writes JSON to $EXPORT_DIR (or ./exports) and returns a filesystem path.

    Args:
        api_key (Union[None, Unset, str]):
        x_api_key (Union[None, Unset, str]):
        body (ExportExportPostPayload):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ExportExportPostResponseExportExportPost, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        body=body,
        api_key=api_key,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ExportExportPostPayload,
    api_key: Union[None, Unset, str] = UNSET,
    x_api_key: Union[None, Unset, str] = UNSET,
) -> Optional[Union[ExportExportPostResponseExportExportPost, HTTPValidationError]]:
    r"""Export

     Protected when VECTORBID_API_KEY is set.
    Accepts: {\"artifact\": {...}}
    Writes JSON to $EXPORT_DIR (or ./exports) and returns a filesystem path.

    Args:
        api_key (Union[None, Unset, str]):
        x_api_key (Union[None, Unset, str]):
        body (ExportExportPostPayload):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ExportExportPostResponseExportExportPost, HTTPValidationError]
    """

    return sync_detailed(
        client=client,
        body=body,
        api_key=api_key,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ExportExportPostPayload,
    api_key: Union[None, Unset, str] = UNSET,
    x_api_key: Union[None, Unset, str] = UNSET,
) -> Response[Union[ExportExportPostResponseExportExportPost, HTTPValidationError]]:
    r"""Export

     Protected when VECTORBID_API_KEY is set.
    Accepts: {\"artifact\": {...}}
    Writes JSON to $EXPORT_DIR (or ./exports) and returns a filesystem path.

    Args:
        api_key (Union[None, Unset, str]):
        x_api_key (Union[None, Unset, str]):
        body (ExportExportPostPayload):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ExportExportPostResponseExportExportPost, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        body=body,
        api_key=api_key,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ExportExportPostPayload,
    api_key: Union[None, Unset, str] = UNSET,
    x_api_key: Union[None, Unset, str] = UNSET,
) -> Optional[Union[ExportExportPostResponseExportExportPost, HTTPValidationError]]:
    r"""Export

     Protected when VECTORBID_API_KEY is set.
    Accepts: {\"artifact\": {...}}
    Writes JSON to $EXPORT_DIR (or ./exports) and returns a filesystem path.

    Args:
        api_key (Union[None, Unset, str]):
        x_api_key (Union[None, Unset, str]):
        body (ExportExportPostPayload):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ExportExportPostResponseExportExportPost, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            api_key=api_key,
            x_api_key=x_api_key,
        )
    ).parsed
