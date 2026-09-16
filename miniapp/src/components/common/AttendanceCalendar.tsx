import { Link } from "react-router-dom";
import type { MonthlyAttendance } from "../../types/models";
import { Stat } from "./ui";
export function AttendanceCalendar({ data }: { data: MonthlyAttendance }) {
  return (
    <>
      <div className="stats-grid three">
        <Stat label="Ishlagan" value={`${data.worked_days} kun`} />
        <Stat label="To'liq kun" value={String(data.full_days)} />
        <Stat label="Yarim kun" value={`${data.half_days} × 0.5`} />
      </div>
      <section className="card">
        <h2>Kunlik davomat</h2>
        <div className="calendar">
          {data.items.map((day) => (
            <Link
              key={day.date}
              to={`/attendance?date=${day.date}`}
              className={day.value ? "present" : ""}
            >
              <span>{day.date.slice(8)}</span>
              <b>{day.value ? `${day.value} kun` : "—"}</b>
            </Link>
          ))}
        </div>
        <p className="muted">Sanani bosib davomatni o'zgartirish mumkin.</p>
      </section>
    </>
  );
}
