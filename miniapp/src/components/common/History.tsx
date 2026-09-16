import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowDownLeft, ArrowUpRight, Trash2 } from "lucide-react";
import { api, type Filters } from "../../api";
import { useRefresh } from "../../hooks/data";
import type { Advance, Expense, Income, Page } from "../../types/models";
import {
  categoryLabel,
  dateLabel,
  formatMoney,
  monthLabel,
} from "../../utils/format";
import { Confirm, Empty, ErrorState, Loading, Pagination } from "./ui";
export function History({
  kind,
  filters,
  projectContext = false,
  cash = false,
}: {
  kind: "income" | "expenses" | "advances";
  filters: Filters;
  projectContext?: boolean;
  cash?: boolean;
}) {
  const [offset, setOffset] = useState(0);
  const [deleting, setDeleting] = useState<string | null>(null);
  const refresh = useRefresh();
  const people = useQuery({
    queryKey: ["people", "all"],
    queryFn: () => api.people(undefined, false),
  });
  const projects = useQuery({
    queryKey: ["projects", "ACTIVE"],
    queryFn: () => api.projects(),
  });
  const completed = useQuery({
    queryKey: ["projects", "COMPLETED"],
    queryFn: () => api.projects("COMPLETED"),
  });
  const history = useQuery<Page<Income | Expense | Advance>>({
    queryKey: ["history", kind, filters, offset, projectContext, cash],
    queryFn: () => {
      const f = { ...filters, offset };
      if (kind === "income")
        return projectContext
          ? api.projectIncome(String(filters.project_id), offset)
          : api.income(f);
      if (kind === "expenses")
        return projectContext
          ? api.projectExpenses(String(filters.project_id), offset)
          : api.expenses(f);
      return cash ? api.cashAdvances(f) : api.advances(f);
    },
  });
  if (history.isPending) return <Loading />;
  if (history.error)
    return (
      <ErrorState error={history.error} retry={() => void history.refetch()} />
    );
  const projectName = (id: string | null) =>
    [...(projects.data ?? []), ...(completed.data ?? [])].find(
      (p) => p.project.id === id,
    )?.project.name;
  const personName = (id: string | null) =>
    people.data?.find((p) => p.id === id)?.name;
  return (
    <section className="card history">
      <div className="section-heading">
        <h2>Tarix</h2>
        <span className="muted">{history.data.total} ta yozuv</span>
      </div>
      <div className="balance-row">
        <span>Jami</span>
        <strong>{formatMoney(history.data.amount)}</strong>
      </div>
      {!history.data.items.length ? (
        <Empty text="Bu davrda yozuvlar yo'q." />
      ) : (
        history.data.items.map((item) => {
          const date =
            "received_at" in item
              ? item.received_at
              : "expense_date" in item
                ? item.expense_date
                : item.paid_at;
          const title =
            "worker_id" in item
              ? (personName(item.worker_id) ?? "Ishchi avansi")
              : "category" in item
                ? (personName(item.beneficiary_person_id) ??
                  categoryLabel[item.category])
                : "Pul tushumi";
          return (
            <div className="transaction" key={item.id}>
              <span className={`icon-tile ${kind === "income" ? "" : "warm"}`}>
                {kind === "income" ? (
                  <ArrowDownLeft size={18} />
                ) : (
                  <ArrowUpRight size={18} />
                )}
              </span>
              <div className="transaction-body">
                <div className="transaction-top">
                  <strong>{title}</strong>
                  <b>{formatMoney(item.amount)}</b>
                </div>
                <p>
                  {dateLabel(date)}
                  {item.project_id &&
                    ` · ${projectName(item.project_id) ?? "Loyiha"}`}
                </p>
                {"salary_month" in item && (
                  <small>Oylik davri: {monthLabel(item.salary_month)}</small>
                )}
                {item.note && <p className="note">{item.note}</p>}
              </div>
              {kind === "advances" && (
                <button
                  className="icon-button danger"
                  aria-label="Avansni o'chirish"
                  onClick={() => setDeleting(item.id)}
                >
                  <Trash2 size={17} />
                </button>
              )}
            </div>
          );
        })
      )}
      <Pagination
        offset={offset}
        total={history.data.total}
        onChange={setOffset}
      />
      {deleting && (
        <Confirm
          title="Avansni o'chirish?"
          description="Bu yozuv o'chiriladi va tegishli oylik qoldig'i qayta hisoblanadi."
          onClose={() => setDeleting(null)}
          confirm={async () => {
            await api.deleteAdvance(deleting);
            await refresh();
            setDeleting(null);
          }}
        />
      )}
    </section>
  );
}
