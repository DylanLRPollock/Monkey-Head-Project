"""Tiny FastAPI-compatible shim for the unit tests.

The real framework is extensive, however the tests in this kata only exercise a
handful of features: declaring routes, raising :class:`HTTPException`, and
accessing a small set of HTTP status constants.  The implementation below keeps
state in-memory and exposes a ``handle_request`` helper used by the test-only
``httpx`` shim to execute routes directly without spinning up an ASGI server.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

__all__ = ["FastAPI", "HTTPException", "Query", "status"]


class HTTPException(Exception):
    def __init__(self, *, status_code: int, detail: Any = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class _StatusCodes:
    HTTP_200_OK = 200
    HTTP_201_CREATED = 201
    HTTP_202_ACCEPTED = 202
    HTTP_204_NO_CONTENT = 204
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


class FastAPI:
    def __init__(self, *, title: str = "", version: str = "", description: str = "") -> None:
        self.title = title
        self.version = version
        self.description = description
        self._routes: List[Route] = []

    # route registration -------------------------------------------------
    def get(self, path: str, *, status_code: int = status.HTTP_200_OK, **_: Any) -> Callable:
        return self._create_decorator(path, ["GET"], status_code)

    def post(self, path: str, *, status_code: int = status.HTTP_200_OK, **_: Any) -> Callable:
        return self._create_decorator(path, ["POST"], status_code)

    def delete(self, path: str, *, status_code: int = status.HTTP_200_OK, **_: Any) -> Callable:
        return self._create_decorator(path, ["DELETE"], status_code)

    def put(self, path: str, *, status_code: int = status.HTTP_200_OK, **_: Any) -> Callable:
        return self._create_decorator(path, ["PUT"], status_code)

    def _create_decorator(self, path: str, methods: List[str], status_code: int) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._routes.append(Route(path=path, methods=methods, endpoint=func, status_code=status_code))
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
    ) -> "Response":
        params = params or {}
        for route in self._routes:
            match = route.match(method, path)
            if match is None:
                continue
            try:
                result = self._invoke(route.endpoint, match, params, json)
                if isinstance(result, Response):
                    return result
                from fastapi.responses import StreamingResponse

                if isinstance(result, StreamingResponse):
                    return Response(status_code=route.status_code, data=result)
                return Response(status_code=route.status_code, data=result)
            except HTTPException as exc:
                return Response(status_code=exc.status_code, data={"detail": exc.detail})
        return Response(status_code=status.HTTP_404_NOT_FOUND, data={"detail": "Not Found"})

    def _invoke(
        self,
        endpoint: Callable[..., Any],
        path_params: Dict[str, str],
        query_params: Dict[str, Any],
        body: Optional[Dict[str, Any]],
    ) -> Any:
        import inspect
        from typing import get_type_hints

        from pydantic import BaseModel

        signature = inspect.signature(endpoint)
        type_hints = get_type_hints(endpoint, globalns=getattr(endpoint, "__globals__", {}))
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

            if issubclass_safe(annotation, BaseModel):
                kwargs[name] = annotation(**body)
                continue

            if name in body:
                kwargs[name] = body[name]
                continue

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
        from pydantic import BaseModel
        from fastapi.responses import StreamingResponse

        if isinstance(self.data, BaseModel):
            return self.data.model_dump()
        if isinstance(self.data, list):
            return [item.model_dump() if isinstance(item, BaseModel) else item for item in self.data]
        if isinstance(self.data, StreamingResponse):
            return list(self.data)
        return self.data
