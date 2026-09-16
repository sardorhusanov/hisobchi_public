import { useState } from "react";
import { Pencil, ShieldCheck } from "lucide-react";
import { useIdentity } from "../hooks/data";
import { ErrorState, Header, Loading } from "../components/common/ui";
import { PersonForm } from "../components/forms/PersonForm";
export default function Settings() {
  const me = useIdentity();
  const [edit, setEdit] = useState(false);
  if (me.isPending) return <Loading />;
  if (me.error)
    return <ErrorState error={me.error} retry={() => void me.refetch()} />;
  return (
    <>
      <Header title="Sozlamalar" subtitle="Shaxsiy ma'lumotlar" />
      <section className="card">
        <div className="person-line">
          <span className="avatar">{me.data.owner.name.charAt(0)}</span>
          <div>
            <h2>{me.data.owner.name}</h2>
            <span className="muted">Biznes egasi</span>
          </div>
          <button
            className="icon-button trailing"
            aria-label="Ismni o'zgartirish"
            onClick={() => setEdit(true)}
          >
            <Pencil size={19} />
          </button>
        </div>
        <dl className="details">
          <div>
            <dt>Telegram hisob</dt>
            <dd>{me.data.telegram_user_id}</dd>
          </div>
          <div>
            <dt>Ilova versiyasi</dt>
            <dd>{me.data.version}</dd>
          </div>
          <div>
            <dt>Vaqt mintaqasi</dt>
            <dd>Asia/Tashkent</dd>
          </div>
        </dl>
      </section>
      <section className="card security-note">
        <ShieldCheck size={22} />
        <p>Ma'lumotlaringiz Telegram hisobingizga bog'langan.</p>
      </section>
      {edit && (
        <PersonForm
          person={me.data.owner}
          role="OWNER"
          onClose={() => setEdit(false)}
        />
      )}
    </>
  );
}
