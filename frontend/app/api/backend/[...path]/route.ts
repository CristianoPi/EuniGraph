import { request as httpRequest } from "node:http";
import type { IncomingMessage, RequestOptions } from "node:http";
import { request as httpsRequest } from "node:https";
import { Readable } from "node:stream";

import { NextRequest } from "next/server";

import { getBackendBaseUrl } from "@/lib/config";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export const maxDuration = 300;

const UPSTREAM_TIMEOUT_MS = 300_000;

function proxyUpstreamRequest(
  upstreamUrl: URL,
  request: NextRequest,
  headers: Headers,
  body: ArrayBuffer | undefined,
): Promise<IncomingMessage> {
  const requestImpl = upstreamUrl.protocol === "https:" ? httpsRequest : httpRequest;
  const requestOptions: RequestOptions = {
    protocol: upstreamUrl.protocol,
    hostname: upstreamUrl.hostname,
    port: upstreamUrl.port ? Number(upstreamUrl.port) : undefined,
    path: `${upstreamUrl.pathname}${upstreamUrl.search}`,
    method: request.method,
    headers: Object.fromEntries(headers.entries()),
  };

  return new Promise((resolve, reject) => {
    const upstreamRequest = requestImpl(requestOptions, (upstreamResponse) => {
      resolve(upstreamResponse);
    });

    upstreamRequest.setTimeout(UPSTREAM_TIMEOUT_MS, () => {
      upstreamRequest.destroy(
        new Error(`Upstream backend request timed out after ${UPSTREAM_TIMEOUT_MS}ms.`),
      );
    });
    upstreamRequest.on("error", reject);

    if (body && body.byteLength > 0) {
      upstreamRequest.write(Buffer.from(body));
    }
    upstreamRequest.end();
  });
}

async function proxyRequest(request: NextRequest): Promise<Response> {
  const incomingUrl = new URL(request.url);
  const proxyPrefix = "/api/backend";
  const upstreamPath =
    incomingUrl.pathname.startsWith(proxyPrefix)
      ? incomingUrl.pathname.slice(proxyPrefix.length) || "/"
      : "/";
  const upstreamUrl = new URL(upstreamPath, getBackendBaseUrl());
  upstreamUrl.search = incomingUrl.search;

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("connection");
  headers.delete("content-length");

  const body =
    request.method === "GET" || request.method === "HEAD"
      ? undefined
      : await request.arrayBuffer();

  const upstreamResponse = await proxyUpstreamRequest(upstreamUrl, request, headers, body);

  const responseHeaders = new Headers();
  for (const [key, value] of Object.entries(upstreamResponse.headers)) {
    if (value === undefined) {
      continue;
    }
    if (Array.isArray(value)) {
      for (const item of value) {
        responseHeaders.append(key, item);
      }
      continue;
    }
    responseHeaders.set(key, value);
  }
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("transfer-encoding");

  return new Response(Readable.toWeb(upstreamResponse) as ReadableStream, {
    status: upstreamResponse.statusCode ?? 502,
    headers: responseHeaders,
  });
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PATCH = proxyRequest;
export const PUT = proxyRequest;
export const DELETE = proxyRequest;
export const OPTIONS = proxyRequest;
