import { useEffect } from "react";
import { ShieldCheck } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import { useIdentity } from "../hooks/data";
import { initializeTelegram } from "../telegram/webapp";
import { ErrorState } from "../components/common/ui";
import { today } from "../utils/format";
import Router from "./router";
export default function App() {
  useEffect(initializeTelegram, []);
  const queryClient = useQueryClient();
  useEffect(() => {
    if (window.location.pathname !== "/") return;
    const month = today().slice(0, 7);
    void queryClient.prefetchQuery({
      queryKey: ["dashboard", month],
      queryFn: () => api.dashboard(month),
    });
  }, [queryClient]);
  const me = useIdentity();
  if (me.isPending)
    return (
      <div className="launch-screen">
        <span className="brand-symbol" aria-hidden="true">
          h
        </span>
        <h1>hisobchi</h1>
        <p>Ishlaringiz yuklanmoqda</p>
        <span
          className="launch-progress"
          role="status"
          aria-label="Yuklanmoqda"
        />
      </div>
    );
  if (me.error)
    return (
      <div className="auth-screen">
        <ShieldCheck size={36} />
        <h1>Xush kelibsiz</h1>
        <ErrorState error={me.error} retry={() => void me.refetch()} />
        <p className="muted">
          Telegram botdagi «📱 Ilovani ochish» tugmasidan foydalaning.
        </p>
      </div>
    );
  return <Router />;
}
