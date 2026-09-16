import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { Pencil, Plus } from "lucide-react";
import { api } from "../api";
import { useRefresh } from "../hooks/data";
import { AttendanceCalendar } from "../components/common/AttendanceCalendar";
import { History } from "../components/common/History";
import {
  Confirm,
  ErrorState,
  Header,
  Loading,
  MoneyStat,
  MonthPicker,
  Stat,
  Tabs,
} from "../components/common/ui";
import { PersonForm } from "../components/forms/PersonForm";
import { TransactionForm } from "../components/forms/TransactionForm";
import { roleLabel, today } from "../utils/format";
export default function WorkerDetails() {
  const { id = "" } = useParams();
  const [month, setMonth] = useState(today().slice(0, 7));
  const [tab, setTab] = useState("overview");
  const [edit, setEdit] = useState(false);
  const [advance, setAdvance] = useState(false);
  const [deactivate, setDeactivate] = useState(false);
  const refresh = useRefresh();
  const data = useQuery({
    queryKey: ["person", id, month],
    queryFn: () => api.person(id, month),
  });
  if (data.isPending) return <Loading />;
  if (data.error)
    return <ErrorState error={data.error} retry={() => void data.refetch()} />;
  const { person, salary, attendance } = data.data;
  const worker = person.role === "WORKER";
  return (
    <>
      <Header
        title={person.name}
        subtitle={`${roleLabel[person.role]}${person.is_active ? "" : " · Arxivlangan"}`}
        back={worker ? "/workers" : "/partners"}
        action={
          <button
            className="icon-button"
            aria-label="Tahrirlash"
            onClick={() => setEdit(true)}
          >
            <Pencil size={19} />
          </button>
        }
      />
      <MonthPicker value={month} onChange={setMonth} />
      <Tabs
        value={tab}
        onChange={setTab}
        items={
          worker
            ? [
                ["overview", "Umumiy"],
                ["attendance", "Davomat"],
                ["advances", "Avanslar"],
                ["salary", "Oylik tarixi"],
              ]
            : [
                ["overview", "Umumiy"],
                ["attendance", "Davomat"],
                ["withdrawals", "Olingan pullar"],
              ]
        }
      />
      {(tab === "overview" || tab === "salary") && (
        <>
          {salary ? (
            <div className="stats-grid">
              <MoneyStat label="Oylik" value={salary.monthly_salary} />
              <MoneyStat label="1 kunlik" value={salary.daily_rate} />
              <Stat label="Ishlagan" value={`${salary.worked_days} kun`} />
              <MoneyStat label="Hisoblangan" value={salary.gross} />
              <MoneyStat label="Avans" value={salary.advances} />
              <MoneyStat label="Qolgan" value={salary.remaining} accent />
            </div>
          ) : (
            <div className="stats-grid">
              <Stat label="Ishlagan" value={`${attendance.worked_days} kun`} />
              <Stat
                label="To'liq kunlar"
                value={String(attendance.full_days)}
              />
            </div>
          )}
          {worker && person.is_active && (
            <button className="primary full" onClick={() => setAdvance(true)}>
              <Plus size={18} /> Avans berish
            </button>
          )}
          {tab === "salary" && (
            <p className="muted">
              Tarixni ko'rish uchun oyni tanlang. Hisob-kitob amaldagi oylik
              bo'yicha.
            </p>
          )}
        </>
      )}
      {tab === "attendance" && <AttendanceCalendar data={attendance} />}{" "}
      {tab === "advances" && (
        <History
          key={month}
          kind="advances"
          filters={{ month, worker_id: id }}
        />
      )}
      {tab === "withdrawals" && (
        <History
          key={month}
          kind="expenses"
          filters={{ month, person_id: id }}
        />
      )}
      {person.role !== "OWNER" && person.is_active && (
        <button
          className="text-button danger full"
          onClick={() => setDeactivate(true)}
        >
          Arxivlash
        </button>
      )}
      {edit && (
        <PersonForm
          person={person}
          role={person.role}
          onClose={() => setEdit(false)}
        />
      )}{" "}
      {advance && (
        <TransactionForm
          kind="advance"
          workerId={id}
          onClose={() => setAdvance(false)}
        />
      )}{" "}
      {deactivate && (
        <Confirm
          title="Kishini arxivlash?"
          description="Tarixiy davomat, avanslar va hisobotlar saqlanadi. Yangi davomat va avans kiritilmaydi."
          onClose={() => setDeactivate(false)}
          confirm={async () => {
            await api.editPerson(id, { is_active: false });
            await refresh();
            setDeactivate(false);
          }}
        />
      )}
    </>
  );
}
