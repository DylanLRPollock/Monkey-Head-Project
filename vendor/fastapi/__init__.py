# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for fastapi

"""Tiny FastAPI-compatible shim for the unit tests.

The real framework is extensive, however the tests in this kata only exercise a
handful of features: declaring routes, including routers, basic middleware,
raising :class:`HTTPException`, and accessing a small set of HTTP status
constants. The implementation below keeps state in-memory and exposes a
``handle_request`` helper used by the test-only ``httpx`` shim to execute
routes directly without spinning up an ASGI server.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

__all__ = [
    "APIRouter",
    "FastAPI",
    "HTTPException",
    "Query",
    "Request",
    "Response",
    "status",
]


class HTTPException(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.headers = headers or {}


class _StatusCodes:
    HTTP_200_OK = 200
    HTTP_201_CREATED = 201
    HTTP_202_ACCEPTED = 202
    HTTP_204_NO_CONTENT = 204
    HTTP_401_UNAUTHORIZED = 401
    HTTP_400_BAD_REQUEST = 400
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_500_INTERNAL_SERVER_ERROR = 500


status = _StatusCodes()


@dataclass
class QueryParam:
    default: Any = None
    alias: Optional[str] = None

    def resolve(self, name: str, params: Dict[str, Any]) -> Any:
        key = self.alias or name
        return params.get(key, self.default)


def Query(default: Any = None, *, alias: Optional[str] = None, **_: Any) -> QueryParam:
    return QueryParam(default=default, alias=alias)


@dataclass
class Route:
    path: str
    methods: List[str]
    endpoint: Callable[..., Any]
    status_code: int

    def match(self, method: str, request_path: str) -> Optional[Dict[str, str]]:
        if method.upper() not in self.methods:
            return None
        route_parts = [part for part in self.path.strip("/").split("/") if part]
        request_parts = [part for part in request_path.strip("/").split("/") if part]
        if len(route_parts) != len(request_parts):
            return None
        params: Dict[str, str] = {}
        for route_part, request_part in zip(route_parts, request_parts):
            if route_part.startswith("{") and route_part.endswith("}"):
                params[route_part[1:-1]] = request_part
            elif route_part != request_part:
                return None
        return params


class Request:
    def __init__(
        self,
        path: str,
        *,
        headers: Optional[Dict[str, Any]] = None,
        base_url: str | None = None,
    ) -> None:
        self.headers = {str(key).lower(): str(value) for key, value in (headers or {}).items()}
        self.url = SimpleNamespace(path=path)
        parsed = urlparse(base_url or "")
        host = parsed.hostname or "testclient"
        self.client = SimpleNamespace(host=host)


class _RouteRegistry:
    def __init__(self) -> None:
        self._routes: List[Route] = []

    @property
    def routes(self) -> List[Route]:
        return list(self._routes)

    def get(
        self, path: str, *, status_code: int = status.HTTP_200_OK, **_: Any
    ) -> Callable:
        return self._create_decorator(path, ["GET"], status_code)

    def post(
        self, path: str, *, status_code: int = status.HTTP_200_OK, **_: Any
    ) -> Callable:
        return self._create_decorator(path, ["POST"], status_code)

    def delete(
        self, path: str, *, status_code: int = status.HTTP_200_OK, **_: Any
    ) -> Callable:
        return self._create_decorator(path, ["DELETE"], status_code)

    def put(
        self, path: str, *, status_code: int = status.HTTP_200_OK, **_: Any
    ) -> Callable:
        return self._create_decorator(path, ["PUT"], status_code)

    def _create_decorator(
        self, path: str, methods: List[str], status_code: int
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._routes.append(
                Route(
                    path=path, methods=methods, endpoint=func, status_code=status_code
                )
            )
            return func

        return decorator


class APIRouter(_RouteRegistry):
    def __init__(self, **_: Any) -> None:
        super().__init__()


class FastAPI(_RouteRegistry):
    def __init__(
        self, *, title: str = "", version: str = "", description: str = ""
    ) -> None:
        super().__init__()
        self.title = title
        self.version = version
        self.description = description
        self._middleware_stack: List[Callable[..., Any]] = []

    def include_router(self, router: APIRouter) -> None:
        self._routes.extend(router.routes)

    def middleware(self, _middleware_type: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._middleware_stack.append(func)
            return func

        return decorator

    # request handling ---------------------------------------------------
    def handle_request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        base_url: str | None = None,
    ) -> "Response | asyncio.Future[Response]":
        async def _dispatch() -> Response:
            request = Request(path, headers=headers, base_url=base_url)
            route: Optional[Route] = None
            match_params: Optional[Dict[str, str]] = None
            for candidate in self._routes:
                match = candidate.match(method, path)
                if match is not None:
                    route = candidate
                    match_params = match
                    break

            if route is None or match_params is None:
                return Response(
                    status_code=status.HTTP_404_NOT_FOUND, data={"detail": "Not Found"}
                )

            async def _invoke_endpoint() -> Response:
                try:
                    result = self._invoke(
                        route.endpoint,
                        match_params,
                        params or {},
                        json or {},
                        request,
                    )
                    if asyncio.iscoroutine(result):
                        result = await result
                    if isinstance(result, Response):
                        return result
                    from fastapi.responses import StreamingResponse

                    if isinstance(result, StreamingResponse):
                        return Response(status_code=route.status_code, data=result)
                    return Response(status_code=route.status_code, data=result)
                except HTTPException as exc:
                    return Response(
                        status_code=exc.status_code, data={"detail": exc.detail}
                    )

            async def _run_middleware(index: int, current_request: Request) -> Response:
                if index >= len(self._middleware_stack):
                    return await _invoke_endpoint()

                middleware = self._middleware_stack[index]

                async def call_next(next_request: Request) -> Response:
                    return await _run_middleware(index + 1, next_request)

                result = middleware(current_request, call_next)
                if asyncio.iscoroutine(result):
                    result = await result
                return result

            return await _run_middleware(0, request)

        return _dispatch()

    def _invoke(
        self,
        endpoint: Callable[..., Any],
        path_params: Dict[str, str],
        query_params: Dict[str, Any],
        body: Optional[Dict[str, Any]],
        request: Request,
    ) -> Any:
        import inspect
        from typing import get_type_hints

        from pydantic import BaseModel

        signature = inspect.signature(endpoint)
        type_hints = get_type_hints(
            endpoint, globalns=getattr(endpoint, "__globals__", {})
        )
        kwargs: Dict[str, Any] = {}
        body = body or {}

        for name, parameter in signature.parameters.items():
            annotation = type_hints.get(name, parameter.annotation)

            if name in path_params:
                kwargs[name] = path_params[name]
                continue

            default = parameter.default
            if isinstance(default, QueryParam):
                value = default.resolve(name, query_params)
                kwargs[name] = value
                continue

            if name in query_params:
                kwargs[name] = query_params[name]
                continue

            if issubclass_safe(annotation, BaseModel) or (
                isinstance(annotation, type) and hasattr(annotation, "model_validate")
            ):
                kwargs[name] = annotation(**body)
                continue

            if name in body:
                kwargs[name] = body[name]
                continue

            if annotation is Request or (name == "request" and not body) or name == "http_request":
                kwargs[name] = request
                continue

            if name == "request" and body and isinstance(annotation, type):
                try:
                    kwargs[name] = annotation(**body)
                    continue
                except Exception:
                    pass

            if default is inspect._empty:
                raise TypeError(f"Missing required parameter: {name}")

            kwargs[name] = default

        return endpoint(**kwargs)


def issubclass_safe(cls: Any, target: type) -> bool:
    try:
        return isinstance(cls, type) and issubclass(cls, target)
    except Exception:
        return False


@dataclass
class Response:
    status_code: int
    data: Any

    def json(self) -> Any:
        from fastapi.responses import StreamingResponse
        from pydantic import BaseModel

        if isinstance(self.data, BaseModel):
            return self.data.model_dump()
        if isinstance(self.data, list):
            return [
                item.model_dump() if isinstance(item, BaseModel) else item
                for item in self.data
            ]
        if isinstance(self.data, StreamingResponse):
            return list(self.data)
        return self.data
