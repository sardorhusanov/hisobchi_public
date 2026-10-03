import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { CheckCheck } from "lucide-react";
import { api } from "../api";
import { useRefresh } from "../hooks/data";
import type { AttendanceValue, DayAttendance } from "../types/models";
import { AttendanceCalendar } from "../components/common/AttendanceCalendar";
import {
  Empty,
  ErrorState,
  Form,
  Header,
  Loading,
  MonthPicker,
  Select,
  Tabs,
} from "../components/common/ui";
import { roleLabel, today } from "../utils/format";
function DayEditor({ data }: { data: DayAttendance }) {
  const [values, setValues] = useState<Record<string, AttendanceValue>>(() =>
    Object.fromEntries(
      data.items.map((item) => [
        item.person.id,
        item.value === "0.5" ? "0.5" : item.value ? "1" : null,
      ]),
    ),
  );
  const [saved, setSaved] = useState(false);
  const refresh = useRefresh();
  return (
    <Form
      label="Davomatni saqlash"
      submit={async () => {
        await api.saveAttendance(
          data.date,
          Object.entries(values).map(([person_id, value]) => ({
            person_id,
            value,
          })),
        );
        setSaved(true);
        await refresh();
      }}
    >
      <button
        type="button"
        className="secondary full"
        onClick={() => {
          setValues(
            Object.fromEntries(data.items.map((i) => [i.person.id, "1"])),
          );
          setSaved(false);
        }}
      >
        <CheckCheck size={18} /> Hammasi 1 kun
      </button>
      <div className="attendance-list">
        {data.items.map(({ person }) => (
          <div className="card attendance-row" key={person.id}>
            <div className="person-line">
              <span className="avatar small">{person.name.charAt(0)}</span>
              <div>
                <h3>{person.name}</h3>
                <span className="muted">{roleLabel[person.role]}</span>
              </div>
            </div>
            <div className="attendance-options">
              {(
                [
                  ["1", "1 kun"],
                  ["0.5", "0.5 kun"],
                  [null, "Yo'q"],
                ] as [AttendanceValue, string][]
              ).map(([value, label]) => (
                <button
                  key={label}
                  type="button"
                  aria-pressed={values[person.id] === value}
                  onClick={() => {
                    setValues({ ...values, [person.id]: value });
                    setSaved(false);
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
      {saved && (
        <p className="success" role="status">
          ✓ Davomat saqlandi.
        </p>
      )}
    </Form>
  );
}
export default function Attendance() {
  const [params, setParams] = useSearchParams();
  const date = params.get("date") || today();
  const [tab, setTab] = useState("day");
  const [month, setMonth] = useState(today().slice(0, 7));
  const [person, setPerson] = useState("");
  const day = useQuery({
    queryKey: ["attendance", date],
    queryFn: () => api.attendance(date),
    enabled: tab === "day",
    refetchOnWindowFocus: false,
  });
  const people = useQuery({
    queryKey: ["people", "all"],
    queryFn: () => api.people(undefined, false),
    enabled: tab === "month",
  });
  const personId = person || people.data?.[0]?.id || "";
  const monthly = useQuery({
    queryKey: ["attendance-month", personId, month],
    queryFn: () => api.attendanceMonth(personId, month),
    enabled: tab === "month" && !!personId,
  });
  return (
    <>
      <Header title="Davomat" subtitle="Har bir ish kuni hisobda" />
      <Tabs
        value={tab}
        onChange={setTab}
        items={[
          ["day", "Kunlik"],
          ["month", "Oylik"],
        ]}
      />
      {tab === "day" ? (
        <>
          <div className="filters">
            <label className="filter">
              Sana
              <input
                type="date"
                required
                value={date}
                onChange={(e) =>
                  e.target.value && setParams({ date: e.target.value })
                }
              />
            </label>
            <button
              className="secondary"
              onClick={() => setParams({ date: today() })}
            >
              Bugun
            </button>
          </div>
          {day.isPending ? (
            <Loading />
          ) : day.error ? (
            <ErrorState error={day.error} retry={() => void day.refetch()} />
          ) : day.data.items.length ? (
            <DayEditor key={date} data={day.data} />
          ) : (
            <Empty />
          )}
        </>
      ) : (
        <>
          <div className="filters">
            <MonthPicker value={month} onChange={setMonth} />
            <Select label="Kishi" value={personId} onChange={setPerson}>
              {people.data?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} · {roleLabel[p.role]}
                </option>
              ))}
            </Select>
          </div>
          {people.error ? (
            <ErrorState
              error={people.error}
              retry={() => void people.refetch()}
            />
          ) : monthly.isPending ? (
            <Loading />
          ) : monthly.error ? (
            <ErrorState
              error={monthly.error}
              retry={() => void monthly.refetch()}
            />
          ) : (
            <AttendanceCalendar data={monthly.data} />
          )}
        </>
      )}
    </>
  );
}
