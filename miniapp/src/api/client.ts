import { telegram } from "../telegram/webapp";
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
const base = (import.meta.env.VITE_API_URL || "/api/v1").replace(/\/$/, "");
export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  const initData = telegram()?.initData;
  if (initData) headers.set("Authorization", `tma ${initData}`);
  else if (import.meta.env.DEV && import.meta.env.VITE_DEV_AUTH === "true")
    headers.set("X-Dev-Auth", "1");
  if (options.body) headers.set("Content-Type", "application/json");
  let response: Response;
  try {
    response = await fetch(`${base}${path}`, {
      ...options,
      headers,
      credentials: "omit",
      cache: "no-store",
    });
  } catch {
    throw new ApiError("Serverga ulanib bo'lmadi. Internetni tekshiring.", 0);
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: unknown;
    } | null;
    throw new ApiError(
      typeof body?.detail === "string"
        ? body.detail
        : "Ma'lumotni saqlab bo'lmadi. Qayta urinib ko'ring.",
      response.status,
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
export function query(
  params: Record<string, string | number | boolean | undefined>,
) {
  const values = Object.entries(params).filter(
    ([, value]) => value !== undefined && value !== "",
  );
  return (
    "?" +
    new URLSearchParams(
      values.map(([key, value]) => [key, String(value)]),
    ).toString()
  );
}
export const json = (method: string, body: unknown): RequestInit => ({
  method,
  body: JSON.stringify(body),
});
