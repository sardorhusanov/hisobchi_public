import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { ApiError } from "../api/client";
const client = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: (count, error) =>
        !(
          error instanceof ApiError &&
          [401, 403, 404, 422].includes(error.status)
        ) && count < 1,
    },
    mutations: { retry: false },
  },
});
export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
}
