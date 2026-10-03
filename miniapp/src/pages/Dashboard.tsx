import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CheckCheck, Plus } from "lucide-react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useIdentity } from "../hooks/data";
import { CashChart } from "../components/charts/CashChart";
import { FinanceStats } from "../components/common/FinanceStats";
import { ProjectCard } from "../components/common/ProjectCard";
import {
  Empty,
  ErrorState,
  Header,
  Loading,
  MonthPicker,
} from "../components/common/ui";
import { monthLabel, today } from "../utils/format";
export default function Dashboard() {
  const me = useIdentity();
  const [month, setMonth] = useState(today().slice(0, 7));
  const result = useQuery({
    queryKey: ["dashboard", month],
    queryFn: () => api.dashboard(month),
  });
  return (
    <>
      <Header
        title={`Salom, ${me.data?.owner.name ?? ""}`}
        subtitle="Biznesingiz, bir qarashda"
        action={
          <Link to="/settings" className="avatar" aria-label="Sozlamalar">
            {me.data?.owner.name.charAt(0)}
          </Link>
        }
      />
      <div className="section-heading">
        <div>
          <span className="eyebrow">MOLIYAVIY KO'RINISH</span>
          <h2>{monthLabel(month)}</h2>
        </div>
        <MonthPicker value={month} onChange={setMonth} />
      </div>
      {result.isPending ? (
        <Loading />
      ) : result.error ? (
        <ErrorState error={result.error} retry={() => void result.refetch()} />
      ) : (
        <>
          <FinanceStats data={result.data.summary} />
          <Link to="/attendance" className="card attendance-callout">
            <span className="icon-tile">
              <CheckCheck />
            </span>
            <div>
              <h3>Bugungi davomat</h3>
              <p>
                {result.data.attendance.marked} /{" "}
                {result.data.attendance.total_people} belgilangan
              </p>
            </div>
            <ArrowRight className="trailing" size={19} />
          </Link>
          <div className="section-heading">
            <h2>Faol loyihalar</h2>
            <Link to="/projects">
              Barchasi <ArrowRight size={15} />
            </Link>
          </div>
          {result.data.projects.length ? (
            <div className="project-grid">
              {result.data.projects.map((p) => (
                <ProjectCard key={p.project.id} data={p} compact />
              ))}
            </div>
          ) : (
            <Empty
              text="Hozircha loyihalar mavjud emas."
              action={
                <Link className="secondary" to="/projects">
                  <Plus size={16} /> Loyiha qo'shish
                </Link>
              }
            />
          )}
          <CashChart data={result.data.cash_flow_chart} />
        </>
      )}
    </>
  );
}
