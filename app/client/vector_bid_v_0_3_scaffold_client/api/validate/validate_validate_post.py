from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.validate_validate_post_payload import ValidateValidatePostPayload
from ...models.validate_validate_post_response_validate_validate_post import (
    ValidateValidatePostResponseValidateValidatePost,
)
from ...types import Response


def _get_kwargs(
    *,
    body: ValidateValidatePostPayload,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/validate",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[HTTPValidationError, ValidateValidatePostResponseValidateValidatePost]
]:
    if response.status_code == 200:
        response_200 = ValidateValidatePostResponseValidateValidatePost.from_dict(
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
) -> Response[
    Union[HTTPValidationError, ValidateValidatePostResponseValidateValidatePost]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ValidateValidatePostPayload,
) -> Response[
    Union[HTTPValidationError, ValidateValidatePostResponseValidateValidatePost]
]:
    r"""Validate

     Body:
      {
        \"preference_schema\": {...},
        \"context\": {...},
        \"pairings\": {\"pairings\":[...] }
      }
    Returns: {\"violations\":[...], \"feasible_pairings\":[...]}

    Args:
        body (ValidateValidatePostPayload):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, ValidateValidatePostResponseValidateValidatePost]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ValidateValidatePostPayload,
) -> Optional[
    Union[HTTPValidationError, ValidateValidatePostResponseValidateValidatePost]
]:
    r"""Validate

     Body:
      {
        \"preference_schema\": {...},
        \"context\": {...},
        \"pairings\": {\"pairings\":[...] }
      }
    Returns: {\"violations\":[...], \"feasible_pairings\":[...]}

    Args:
        body (ValidateValidatePostPayload):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, ValidateValidatePostResponseValidateValidatePost]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ValidateValidatePostPayload,
) -> Response[
    Union[HTTPValidationError, ValidateValidatePostResponseValidateValidatePost]
]:
    r"""Validate

     Body:
      {
        \"preference_schema\": {...},
        \"context\": {...},
        \"pairings\": {\"pairings\":[...] }
      }
    Returns: {\"violations\":[...], \"feasible_pairings\":[...]}

    Args:
        body (ValidateValidatePostPayload):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, ValidateValidatePostResponseValidateValidatePost]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ValidateValidatePostPayload,
) -> Optional[
    Union[HTTPValidationError, ValidateValidatePostResponseValidateValidatePost]
]:
    r"""Validate

     Body:
      {
        \"preference_schema\": {...},
        \"context\": {...},
        \"pairings\": {\"pairings\":[...] }
      }
    Returns: {\"violations\":[...], \"feasible_pairings\":[...]}

    Args:
        body (ValidateValidatePostPayload):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, ValidateValidatePostResponseValidateValidatePost]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
