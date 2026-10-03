import { useState } from "react";
import { Palette, Pencil, ShieldCheck } from "lucide-react";
import { useIdentity } from "../hooks/data";
import { ErrorState, Header, Loading, Select } from "../components/common/ui";
import { PersonForm } from "../components/forms/PersonForm";
import {
  getAppearance,
  setAppearance,
  type Appearance,
} from "../telegram/webapp";
export default function Settings() {
  const me = useIdentity();
  const [edit, setEdit] = useState(false);
  const [appearance, updateAppearance] = useState(getAppearance);
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
      <section className="card appearance-card">
        <div className="person-line">
          <span className="icon-tile">
            <Palette size={20} />
          </span>
          <div>
            <h2>Ko'rinish</h2>
            <span className="muted">Sizga qulay rangni tanlang</span>
          </div>
        </div>
        <Select
          label="Rang mavzusi"
          value={appearance}
          onChange={(value) => {
            updateAppearance(value as Appearance);
            setAppearance(value as Appearance);
          }}
        >
          <option value="light">Yorug'</option>
          <option value="telegram">Telegramga mos</option>
          <option value="dark">Tungi</option>
        </Select>
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
