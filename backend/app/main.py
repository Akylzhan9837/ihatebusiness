from contextlib import asynccontextmanager
from importlib import import_module
import logging

from anyio import Semaphore

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from app.api.routes import make_router
from app.api.errors import ApiError
from app.config import Settings
from app.models import Offer
from app.services.extraction import OpenAIExtractor
from app.services.extraction.files import MAX_FILE_BYTES
from app.storage import Store


class RequestLimits:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith("/api/"):
            await self.app(scope, receive, send)
            return

        async def no_store(message):
            if message["type"] == "http.response.start":
                message["headers"].extend([
                    (b"cache-control", b"no-store"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"x-content-type-options", b"nosniff"),
                ])
            await send(message)

        if scope["method"] not in {"POST", "PATCH"}:
            await self.app(scope, receive, no_store)
            return

        upload = scope["method"] == "POST" and scope["path"].rstrip("/").endswith("/documents")
        limit = MAX_FILE_BYTES + 65536 if upload else 65536
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(chunk) + len(body) > limit:
                error = ApiError(413, "request_too_large", "The request exceeds the allowed size.")
                await JSONResponse(error.payload(), status_code=413)(scope, receive, no_store)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        async def replay():
            nonlocal body
            if body is None:
                return await receive()
            payload = bytes(body)
            body = None
            return {"type": "http.request", "body": payload, "more_body": False}

        await self.app(scope, replay, no_store)


def optional_plugin(module: str, attribute: str):
    try:
        plugin = import_module(module)
    except ModuleNotFoundError as exc:
        if exc.name == module:
            return None
        raise
    return getattr(plugin, attribute, None)


def create_app(settings: Settings | None = None, *, extractor=None, evaluate=None, render_pdf=None):
    settings = settings or Settings.from_env()
    store = Store(settings.db, Offer(mode="demo" if settings.demo_access else "unavailable"))
    extractor = extractor if extractor is not None else OpenAIExtractor(settings.ai_key, settings.ai_model)
    evaluate = evaluate if evaluate is not None else optional_plugin("app.rules", "evaluate")
    render_pdf = render_pdf if render_pdf is not None else optional_plugin("app.export", "render_pdf")

    @asynccontextmanager
    async def lifespan(_app):
        await run_in_threadpool(store.initialize)
        yield

    app = FastAPI(title="TicketClear", version="1.0.0", lifespan=lifespan, redirect_slashes=False)
    app.add_middleware(RequestLimits)
    if settings.origins:
        app.add_middleware(
            CORSMiddleware, allow_origins=list(settings.origins),
            allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"],
            expose_headers=["Content-Disposition"],
        )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("pypdf").setLevel(logging.CRITICAL)

    @app.exception_handler(ApiError)
    async def api_error(_request: Request, error: ApiError):
        return JSONResponse(error.payload(), status_code=error.status)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request: Request, _error: RequestValidationError):
        error = ApiError(422, "invalid_input", "Check the required fields and input formats.")
        return JSONResponse(error.payload(), status_code=error.status)

    @app.exception_handler(HTTPException)
    async def http_error(_request: Request, exc: HTTPException):
        error = ApiError(exc.status_code, "request_failed", "The requested operation could not be completed.")
        return JSONResponse(error.payload(), status_code=error.status)

    @app.exception_handler(Exception)
    async def server_error(_request: Request, _exc: Exception):
        error = ApiError(500, "internal_error", "TicketClear could not complete this request. Try again.", retryable=True)
        return JSONResponse(error.payload(), status_code=500, headers={"Cache-Control": "no-store"})

    app.include_router(make_router(store, settings, extractor, Semaphore(2), evaluate, render_pdf))
    return app


app = create_app()
