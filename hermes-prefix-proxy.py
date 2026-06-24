#!/usr/bin/env python3
"""Small path-prefix proxy for Hermes Dashboard behind Tailscale Serve.

Browser path:
  /hermes/sessions

Backend path:
  /sessions

The X-Forwarded-Prefix header lets Hermes generate prefixed redirects,
cookie paths, asset URLs, API URLs, and websocket URLs.
"""

from __future__ import annotations

import asyncio
import os
from typing import Iterable

from aiohttp import ClientSession, WSMsgType, web


PREFIX = os.environ.get("HERMES_PREFIX_PROXY_PREFIX", "/hermes").rstrip("/")
TARGET = os.environ.get("HERMES_PREFIX_PROXY_TARGET", "http://127.0.0.1:9119").rstrip("/")
LISTEN_HOST = os.environ.get("HERMES_PREFIX_PROXY_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("HERMES_PREFIX_PROXY_PORT", "9120"))

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def strip_prefix(path: str) -> str | None:
    if path == PREFIX:
        return "/"
    if path.startswith(PREFIX + "/"):
        return path[len(PREFIX):] or "/"
    return None


def target_url(request: web.Request, backend_path: str) -> str:
    url = f"{TARGET}{backend_path}"
    if request.rel_url.query_string:
        url += "?" + request.rel_url.query_string
    return url


def request_headers(request: web.Request) -> dict[str, str]:
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in HOP_BY_HOP and k.lower() != "host"
    }
    headers["Host"] = request.host
    headers["X-Forwarded-Prefix"] = PREFIX
    headers["X-Forwarded-Host"] = request.host
    headers["X-Forwarded-Proto"] = "https"
    if request.remote:
        prior = headers.get("X-Forwarded-For")
        headers["X-Forwarded-For"] = f"{prior}, {request.remote}" if prior else request.remote
    return headers


def response_headers(items: Iterable[tuple[str, str]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in items:
        lower = key.lower()
        if lower in HOP_BY_HOP or lower == "content-length":
            continue
        if lower == "location" and value.startswith("/") and not value.startswith(PREFIX + "/"):
            value = PREFIX + value
        out[key] = value
    return out


def rewrite_body(body: bytes, content_type: str) -> bytes:
    if "text/html" not in content_type.lower():
        return body
    text = body.decode("utf-8", errors="replace")
    text = text.replace("fetch('/auth/password-login'", f"fetch('{PREFIX}/auth/password-login'")
    text = text.replace('href="/auth/login?', f'href="{PREFIX}/auth/login?')
    for asset_dir in ("/fonts/", "/fonts-terminal/", "/ds-assets/", "/assets/"):
        text = text.replace(f"url({asset_dir}", f"url({PREFIX}{asset_dir}")
        text = text.replace(f"url(\"{asset_dir}", f"url(\"{PREFIX}{asset_dir}")
        text = text.replace(f"url('{asset_dir}", f"url('{PREFIX}{asset_dir}")
        text = text.replace(f'href="{asset_dir}', f'href="{PREFIX}{asset_dir}')
        text = text.replace(f'src="{asset_dir}', f'src="{PREFIX}{asset_dir}')
    text = text.replace(
        "window.location.assign((data && data.next) || '/');",
        (
            "var next = (data && data.next) || '/';"
            f" if (next.charAt(0) === '/') {{ next = '{PREFIX}' + next; }}"
            " window.location.assign(next);"
        ),
    )
    return text.encode("utf-8")


async def proxy_http(request: web.Request, backend_path: str) -> web.StreamResponse:
    async with request.app["client"].request(
        request.method,
        target_url(request, backend_path),
        headers=request_headers(request),
        data=await request.read(),
        allow_redirects=False,
    ) as upstream:
        body = await upstream.read()
        headers = response_headers(upstream.headers.items())
        body = rewrite_body(body, upstream.headers.get("content-type", ""))
        return web.Response(status=upstream.status, headers=headers, body=body)


async def proxy_ws(request: web.Request, backend_path: str) -> web.WebSocketResponse:
    downstream = web.WebSocketResponse()
    await downstream.prepare(request)
    async with request.app["client"].ws_connect(
        target_url(request, backend_path),
        headers=request_headers(request),
    ) as upstream:
        async def client_to_backend() -> None:
            async for msg in downstream:
                if msg.type == WSMsgType.TEXT:
                    await upstream.send_str(msg.data)
                elif msg.type == WSMsgType.BINARY:
                    await upstream.send_bytes(msg.data)
                elif msg.type == WSMsgType.CLOSE:
                    await upstream.close()

        async def backend_to_client() -> None:
            async for msg in upstream:
                if msg.type == WSMsgType.TEXT:
                    await downstream.send_str(msg.data)
                elif msg.type == WSMsgType.BINARY:
                    await downstream.send_bytes(msg.data)
                elif msg.type == WSMsgType.CLOSE:
                    await downstream.close()

        await asyncio.wait(
            {asyncio.create_task(client_to_backend()), asyncio.create_task(backend_to_client())},
            return_when=asyncio.FIRST_COMPLETED,
        )
    return downstream


async def handle(request: web.Request) -> web.StreamResponse:
    backend_path = strip_prefix(request.rel_url.path)
    if backend_path is None:
        raise web.HTTPNotFound(text=f"Expected path under {PREFIX}")
    if request.headers.get("upgrade", "").lower() == "websocket":
        return await proxy_ws(request, backend_path)
    return await proxy_http(request, backend_path)


async def on_startup(app: web.Application) -> None:
    app["client"] = ClientSession()


async def on_cleanup(app: web.Application) -> None:
    await app["client"].close()


app = web.Application()
app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)
app.router.add_route("*", "/{tail:.*}", handle)


if __name__ == "__main__":
    web.run_app(app, host=LISTEN_HOST, port=LISTEN_PORT, access_log=None)
