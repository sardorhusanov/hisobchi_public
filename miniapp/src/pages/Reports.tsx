import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api";
import {
  Breakdown,
  CashChart,
  ProjectChart,
} from "../components/charts/FinanceCharts";
import { AttendanceCalendar } from "../components/common/AttendanceCalendar";
import { FinanceStats } from "../components/common/FinanceStats";
import { History } from "../components/common/History";
import { ProjectCard } from "../components/common/ProjectCard";
import {
  Empty,
  ErrorState,
  Header,
  Loading,
  MonthPicker,
  Select,
  Stat,
} from "../components/common/ui";
import { today } from "../utils/format";
export default function Reports() {
  const [month, setMonth] = useState(today().slice(0, 7));
  const [report, setReport] = useState("finance");
  const [person, setPerson] = useState("");
  const [project, setProject] = useState("");
  const finance = useQuery({
    queryKey: ["finance", { month }],
    queryFn: () => api.finance({ month }),
    enabled: report === "finance",
  });
  const attendance = useQuery({
    queryKey: ["attendance-report", month],
    queryFn: () => api.attendanceReport(month),
    enabled: report === "attendance",
  });
  const calendar = useQuery({
    queryKey: ["attendance-month", person, month],
    queryFn: () => api.attendanceMonth(person, month),
    enabled: report === "attendance" && !!person,
  });
  const projects = useQuery({
    queryKey: ["projects", "ACTIVE"],
    queryFn: () => api.projects(),
    enabled: report === "projects",
  });
  const completed = useQuery({
    queryKey: ["projects", "COMPLETED"],
    queryFn: () => api.projects("COMPLETED"),
    enabled: report === "projects",
  });
  const allProjects = [...(projects.data ?? []), ...(completed.data ?? [])];
  return (
    <>
      <Header title="Hisobotlar" subtitle="Raqamlarni yaxshiroq tushuning" />
      <Select label="Hisobot turi" value={report} onChange={setReport}>
        <option value="finance">Oylik moliya</option>
        <option value="attendance">Oylik davomat</option>
        <option value="salary">Ishchilar oyligi</option>
        <option value="advances">Avanslar</option>
        <option value="projects">Loyihalar</option>
      </Select>
      {report !== "projects" && (
        <MonthPicker value={month} onChange={setMonth} />
      )}{" "}
      {report === "finance" &&
        (finance.isPending ? (
          <Loading />
        ) : finance.error ? (
          <ErrorState
            error={finance.error}
            retry={() => void finance.refetch()}
          />
        ) : (
          <>
            <FinanceStats data={finance.data.summary} detailed />
            <CashChart data={finance.data.chart} />
            <Breakdown data={finance.data.summary} />
            <h2>Tushumlar</h2>
            <History key={"income" + month} kind="income" filters={{ month }} />
            <h2>Xarajatlar</h2>
            <History
              key={"expenses" + month}
              kind="expenses"
              filters={{ month }}
            />
            <h2>To'langan avanslar</h2>
            <History
              key={"advances" + month}
              kind="advances"
              filters={{ month }}
              cash
            />
          </>
        ))}
      {report === "attendance" &&
        (attendance.isPending ? (
          <Loading />
        ) : attendance.error ? (
          <ErrorState
            error={attendance.error}
            retry={() => void attendance.refetch()}
          />
        ) : (
          <>
            <Select label="Kishi" value={person} onChange={setPerson}>
              <option value="">Barcha kishilar</option>
              {attendance.data.items.map((r) => (
                <option key={r.person.id} value={r.person.id}>
                  {r.person.name}
                </option>
              ))}
            </Select>
            {person ? (
              calendar.isPending ? (
                <Loading />
              ) : calendar.error ? (
                <ErrorState
                  error={calendar.error}
                  retry={() => void calendar.refetch()}
                />
              ) : (
                <AttendanceCalendar data={calendar.data} />
              )
            ) : (
              <>
                <Stat
                  label="Jami ishlangan"
                  value={`${attendance.data.worked_days} kun`}
                />
                <section className="card">
                  {attendance.data.items.map((r) => (
                    <div className="balance-row" key={r.person.id}>
                      <Link to={`/people/${r.person.id}`}>{r.person.name}</Link>
                      <b>{r.worked_days} kun</b>
                    </div>
                  ))}
                </section>
              </>
            )}
          </>
        ))}
      {report === "salary" && (
        <section className="card">
          <h2>Oylik hisoboti</h2>
          <p className="muted">
            Har bir ishchining hisoblangan oyligi, avansi va qoldig'i.
          </p>
          <Link className="primary" to={`/salary?month=${month}`}>
            Oylik hisobotini ochish
          </Link>
        </section>
      )}
      {report === "advances" && (
        <>
          <History key={month} kind="advances" filters={{ month }} />
          <Link className="secondary full" to="/advances">
            Ishchi va loyiha bo'yicha filtrlash
          </Link>
        </>
      )}
      {report === "projects" && (
        <>
          {projects.isPending || completed.isPending ? (
            <Loading />
          ) : projects.error || completed.error ? (
            <ErrorState
              error={(projects.error || completed.error)!}
              retry={() => {
                void projects.refetch();
                void completed.refetch();
              }}
            />
          ) : (
            <>
              <Select label="Loyiha" value={project} onChange={setProject}>
                <option value="">Barcha loyihalar</option>
                {allProjects.map((p) => (
                  <option key={p.project.id} value={p.project.id}>
                    {p.project.name}
                  </option>
                ))}
              </Select>
              {!allProjects.length ? (
                <Empty text="Loyihalar yo'q." />
              ) : (
                <>
                  {!project && <ProjectChart data={projects.data ?? []} />}
                  <div className="list">
                    {allProjects
                      .filter((p) => !project || p.project.id === project)
                      .map((p) => (
                        <ProjectCard key={p.project.id} data={p} />
                      ))}
                  </div>
                  {project && (
                    <>
                      <History
                        key={"i" + project}
                        kind="income"
                        filters={{ project_id: project }}
                        projectContext
                      />
                      <History
                        key={"e" + project}
                        kind="expenses"
                        filters={{ project_id: project }}
                        projectContext
                      />
                    </>
                  )}
                </>
              )}
            </>
          )}
        </>
      )}
    </>
  );
}
