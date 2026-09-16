import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
export function useIdentity() {
  return useQuery({ queryKey: ["me"], queryFn: api.me, staleTime: 60_000 });
}
export function useRefresh() {
  const client = useQueryClient();
  return () => client.invalidateQueries();
}
