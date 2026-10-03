import type { ChartPoint } from "../../types/models";

const LEFT = 12;
const RIGHT = 308;
const TOP = 16;
const BOTTOM = 128;

export function CashChart({ data }: { data: ChartPoint[] }) {
  const values = data.map((item) => ({
    income: Number(item.income),
    expenses: Number(item.expenses),
  }));
  const maximum = Math.max(
    1,
    ...values.flatMap((item) => [item.income, item.expenses]),
  );
  const x = (index: number) =>
    LEFT + (index / Math.max(values.length - 1, 1)) * (RIGHT - LEFT);
  const y = (value: number) => BOTTOM - (value / maximum) * (BOTTOM - TOP);
  const points = (key: "income" | "expenses") =>
    values.map((item, index) => `${x(index)},${y(item[key])}`).join(" ");

  return (
    <section className="card chart-card">
      <div className="section-heading">
        <h2>Pul harakati</h2>
        <span className="muted">Kunlar bo'yicha</span>
      </div>
      <div className="legend">
        <span>
          <i className="income-dot" />
          Tushum
        </span>
        <span>
          <i className="expense-dot" />
          Xarajat
        </span>
      </div>
      {values.length ? (
        <svg
          className="cash-chart"
          viewBox="0 0 320 160"
          preserveAspectRatio="none"
          role="img"
          aria-label="Kunlar bo'yicha tushum va xarajatlar grafigi"
        >
          {[TOP, (TOP + BOTTOM) / 2, BOTTOM].map((position) => (
            <line
              key={position}
              x1={LEFT}
              x2={RIGHT}
              y1={position}
              y2={position}
              stroke="var(--border)"
              strokeDasharray="3 5"
            />
          ))}
          <polyline points={points("income")} stroke="var(--chart-income)" />
          <polyline points={points("expenses")} stroke="var(--chart-expense)" />
          <text x={LEFT} y="153" textAnchor="start">
            {data[0].date.slice(5).split("-").reverse().join(".")}
          </text>
          <text x={RIGHT} y="153" textAnchor="end">
            {data.at(-1)?.date.slice(5).split("-").reverse().join(".")}
          </text>
        </svg>
      ) : (
        <p className="muted chart-empty">Bu davrda harakat yo'q.</p>
      )}
    </section>
  );
}
