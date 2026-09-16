import { useEffect } from "react";
import { ShieldCheck } from "lucide-react";
import { useIdentity } from "../hooks/data";
import { initializeTelegram } from "../telegram/webapp";
import { ErrorState, Loading } from "../components/common/ui";
import Router from "./router";
export default function App() {
  useEffect(initializeTelegram, []);
  const me = useIdentity();
  if (me.isPending)
    return (
      <div className="auth-screen">
        <span className="brand-symbol">h</span>
        <h1>hisobchi</h1>
        <p>Biznesingiz bir joyda</p>
        <Loading />
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
