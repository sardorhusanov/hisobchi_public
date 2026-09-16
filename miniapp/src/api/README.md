The typed API facade is in `index.ts`; all HTTP requests pass through `client.ts`.
It attaches Telegram initData and returns safe API errors. Query caching lives in
TanStack Query. Mutations invalidate shared queries so all summaries are refreshed.
No accounting calculation or database access belongs in this directory.
