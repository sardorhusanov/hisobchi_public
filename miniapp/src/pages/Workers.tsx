import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Plus, ChevronRight } from "lucide-react";
import { api } from "../api";
import { PersonForm } from "../components/forms/PersonForm";
import {
  Empty,
  ErrorState,
  Header,
  Loading,
  MonthPicker,
} from "../components/common/ui";
import { formatMoney, today } from "../utils/format";
export default function Workers() {
  const [month, setMonth] = useState(today().slice(0, 7));
  const [add, setAdd] = useState(false);
  const [archive, setArchive] = useState(false);
  const data = useQuery({
    queryKey: ["salaries", month, !archive],
    queryFn: () => api.salaries(month, !archive),
  });
  return (
    <>
      <Header
        title="Ishchilar"
        subtitle="Jamoa va oylik hisoblari"
        action={
          <button className="primary" onClick={() => setAdd(true)}>
            <Plus size={18} /> Qo'shish
          </button>
        }
      />
      <div className="filters">
        <MonthPicker value={month} onChange={setMonth} />
        <label className="check">
          <input
            type="checkbox"
            checked={archive}
            onChange={(e) => setArchive(e.target.checked)}
          />{" "}
          Arxiv bilan
        </label>
      </div>
      {data.isPending ? (
        <Loading />
      ) : data.error ? (
        <ErrorState error={data.error} retry={() => void data.refetch()} />
      ) : !data.data.items.length ? (
        <Empty
          text="Hozircha ishchilar yo'q."
          action={
            <button className="secondary" onClick={() => setAdd(true)}>
              Ishchi qo'shish
            </button>
          }
        />
      ) : (
        <div className="list">
          {data.data.items.map((r) => (
            <Link
              key={r.person.id}
              to={`/people/${r.person.id}`}
              className="card"
            >
              <div className="person-line">
                <span className="avatar small">{r.person.name.charAt(0)}</span>
                <div>
                  <h3>{r.person.name}</h3>
                  <span className="muted">
                    {r.person.is_active ? "Ishchi" : "Arxivlangan"} ·{" "}
                    {r.worked_days} kun
                  </span>
                </div>
                <ChevronRight className="trailing" size={18} />
              </div>
              <dl className="details">
                <div>
                  <dt>Oylik</dt>
                  <dd>{formatMoney(r.monthly_salary)}</dd>
                </div>
                <div>
                  <dt>Hisoblangan</dt>
                  <dd>{formatMoney(r.gross)}</dd>
                </div>
                <div>
                  <dt>Avans</dt>
                  <dd>{formatMoney(r.advances)}</dd>
                </div>
              </dl>
              <div className="balance-row">
                <span>Qolgan</span>
                <strong>{formatMoney(r.remaining)}</strong>
              </div>
            </Link>
          ))}
        </div>
      )}
      {add && <PersonForm role="WORKER" onClose={() => setAdd(false)} />}
    </>
  );
}
