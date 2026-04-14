import { NextRequest } from "next/server";

import { getBackendBaseUrl } from "@/lib/config";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

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

  const upstreamResponse = await fetch(upstreamUrl, {
    method: request.method,
    headers,
    body,
    cache: "no-store",
  });

  const responseHeaders = new Headers(upstreamResponse.headers);
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("transfer-encoding");

  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    headers: responseHeaders,
  });
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PATCH = proxyRequest;
export const PUT = proxyRequest;
export const DELETE = proxyRequest;
export const OPTIONS = proxyRequest;
