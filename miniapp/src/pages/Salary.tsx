import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api";
import {
  Empty,
  ErrorState,
  Header,
  Loading,
  MoneyStat,
  MonthPicker,
  Select,
  Stat,
} from "../components/common/ui";
import { formatMoney, today } from "../utils/format";
export default function Salary() {
  const [params] = useSearchParams();
  const [month, setMonth] = useState(
    params.get("month") || today().slice(0, 7),
  );
  const [person, setPerson] = useState("");
  const data = useQuery({
    queryKey: ["salaries", month, false],
    queryFn: () => api.salaries(month),
  });
  return (
    <>
      <Header title="Oylik" subtitle="Ishlangan kunlar va avanslar hisobda" />
      <div className="filters">
        <MonthPicker value={month} onChange={setMonth} />
        <Select label="Ishchi" value={person} onChange={setPerson}>
          <option value="">Barcha ishchilar</option>
          {data.data?.items.map((r) => (
            <option key={r.person.id} value={r.person.id}>
              {r.person.name}
            </option>
          ))}
        </Select>
      </div>
      {data.isPending ? (
        <Loading />
      ) : data.error ? (
        <ErrorState error={data.error} retry={() => void data.refetch()} />
      ) : (
        <>
          <div className="stats-grid">
            <Stat
              label="Jami ishchilar"
              value={String(data.data.worker_count)}
            />
            <MoneyStat label="Jami hisoblangan" value={data.data.gross} />
            <MoneyStat label="Jami avans" value={data.data.advances} />
            <MoneyStat label="Jami qolgan" value={data.data.remaining} accent />
          </div>
          {!data.data.items.length ? (
            <Empty
              text="Hozircha ishchilar yo'q."
              action={
                <Link to="/workers" className="secondary">
                  Ishchi qo'shish
                </Link>
              }
            />
          ) : (
            <div className="list">
              {data.data.items
                .filter((r) => !person || r.person.id === person)
                .map((r) => (
                  <Link
                    className="card"
                    to={`/people/${r.person.id}`}
                    key={r.person.id}
                  >
                    <div className="section-heading">
                      <h3>{r.person.name}</h3>
                      <span className="badge">{r.worked_days} kun</span>
                    </div>
                    <dl className="details">
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
        </>
      )}
    </>
  );
}
