import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { api } from "../api";
import { Breakdown, CashChart } from "../components/charts/FinanceCharts";
import { FinanceStats } from "../components/common/FinanceStats";
import { History } from "../components/common/History";
import {
  initialPeriod,
  periodParams,
  PeriodFilter,
} from "../components/common/PeriodFilter";
import {
  ErrorState,
  Header,
  Loading,
  Select,
  Tabs,
} from "../components/common/ui";
import { TransactionForm } from "../components/forms/TransactionForm";
import { categoryLabel } from "../utils/format";
export default function Finance() {
  const [period, setPeriod] = useState(initialPeriod);
  const [tab, setTab] = useState("income");
  const [kind, setKind] = useState<"income" | "expense" | null>(null);
  const [category, setCategory] = useState("");
  const params = periodParams(period);
  const data = useQuery({
    queryKey: ["finance", params],
    queryFn: () => api.finance(params),
  });
  return (
    <>
      <Header title="Moliya" subtitle="Har bir tushum va chiqim aniq" />
      <PeriodFilter value={period} onChange={setPeriod} />
      <div className="actions">
        <button className="primary" onClick={() => setKind("income")}>
          <Plus size={18} /> Tushum
        </button>
        <button className="secondary" onClick={() => setKind("expense")}>
          <Plus size={18} /> Xarajat
        </button>
      </div>
      {data.isPending ? (
        <Loading />
      ) : data.error ? (
        <ErrorState error={data.error} retry={() => void data.refetch()} />
      ) : (
        <>
          <FinanceStats data={data.data.summary} detailed />
          <p className="muted">
            Avanslar haqiqiy to'lov sanasi bo'yicha hisoblangan.
          </p>
          <CashChart data={data.data.chart} />
          <Breakdown data={data.data.summary} />
        </>
      )}
      <Tabs
        value={tab}
        onChange={setTab}
        items={[
          ["income", "Tushumlar"],
          ["expenses", "Xarajatlar"],
          ["advances", "Avanslar"],
        ]}
      />
      {tab === "expenses" && (
        <Select label="Xarajat turi" value={category} onChange={setCategory}>
          <option value="">Barchasi</option>
          {Object.entries(categoryLabel).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </Select>
      )}
      <History
        key={JSON.stringify([tab, params, category])}
        kind={tab as "income" | "expenses" | "advances"}
        filters={{
          ...params,
          category: tab === "expenses" ? category : undefined,
        }}
        cash
      />
      {kind && <TransactionForm kind={kind} onClose={() => setKind(null)} />}
    </>
  );
}
