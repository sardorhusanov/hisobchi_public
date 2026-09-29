import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type {
  ChartPoint,
  FinanceSummary,
  ProjectSummary,
} from "../../types/models";
const compact = (value: number) =>
  new Intl.NumberFormat("uz-UZ", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
const colors = [
  "var(--chart-income)",
  "var(--chart-warning)",
  "var(--chart-secondary)",
  "var(--chart-expense)",
  "var(--chart-neutral)",
];
export function CashChart({ data }: { data: ChartPoint[] }) {
  const values = data.map((p) => ({
    date: p.date.slice(5).split("-").reverse().join("."),
    Tushum: Number(p.income),
    Xarajat: Number(p.expenses),
  }));
  return (
    <section className="card chart-card">
      <div className="section-heading">
        <h2>Pul harakati</h2>
        <span className="muted">Kunlar bo'yicha</span>
      </div>
      <div className="legend">
        <span>
          <i style={{ background: colors[0] }} />
          Tushum
        </span>
        <span>
          <i style={{ background: colors[1] }} />
          Xarajat
        </span>
      </div>
      <div
        className="chart"
        role="img"
        aria-label="Kunlar bo'yicha tushum va xarajatlar grafigi"
      >
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={values}
            margin={{ top: 10, right: 8, left: -16, bottom: 0 }}
          >
            <CartesianGrid
              vertical={false}
              strokeDasharray="3 5"
              stroke="var(--border)"
            />
            <XAxis
              dataKey="date"
              tick={{ fill: "var(--muted)" }}
              tickLine={false}
              axisLine={false}
              minTickGap={25}
            />
            <YAxis
              tick={{ fill: "var(--muted)" }}
              tickFormatter={compact}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              formatter={(value) => compact(Number(value)) + " so'm"}
              contentStyle={{
                background: "var(--surface)",
                borderColor: "var(--border)",
                borderRadius: 12,
              }}
            />
            <Area
              type="monotone"
              dataKey="Tushum"
              stroke={colors[0]}
              fill={colors[0]}
              fillOpacity={0.09}
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="Xarajat"
              stroke={colors[1]}
              fill={colors[1]}
              fillOpacity={0.04}
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
export function Breakdown({ data }: { data: FinanceSummary }) {
  const values = [
    { name: "Biznes", value: Number(data.business_expenses) },
    { name: "Egasi", value: Number(data.owner_withdrawals) },
    { name: "Hamkor", value: Number(data.partner_withdrawals) },
    { name: "Avans", value: Number(data.advances) },
    { name: "Boshqa", value: Number(data.other_expenses) },
  ];
  return (
    <section className="card chart-card">
      <h2>Chiqim tarkibi</h2>
      {values.some((v) => v.value > 0) ? (
        <>
          <div
            className="chart donut"
            role="img"
            aria-label="Chiqimlar toifalar bo'yicha"
          >
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={values}
                  dataKey="value"
                  innerRadius="58%"
                  outerRadius="85%"
                  paddingAngle={3}
                >
                  {values.map((v, i) => (
                    <Cell key={v.name} fill={colors[i]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => compact(Number(value)) + " so'm"}
                  contentStyle={{
                    background: "var(--surface)",
                    borderColor: "var(--border)",
                    borderRadius: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="legend wrap">
            {values.map((v, i) => (
              <span key={v.name}>
                <i style={{ background: colors[i] }} />
                {v.name}
              </span>
            ))}
          </div>
        </>
      ) : (
        <p className="muted">Bu davrda chiqim yo'q.</p>
      )}
    </section>
  );
}
export function ProjectChart({ data }: { data: ProjectSummary[] }) {
  return (
    <section className="card chart-card">
      <h2>Loyiha qoldiqlari</h2>
      <div className="chart" role="img" aria-label="Faol loyihalar qoldig'i">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={data
              .slice(0, 10)
              .map((p) => ({ name: p.project.name, value: Number(p.balance) }))}
            margin={{ left: 0, right: 20 }}
          >
            <XAxis type="number" tickFormatter={compact} />
            <YAxis
              dataKey="name"
              type="category"
              width={85}
              tick={{ fontSize: 11 }}
            />
            <Tooltip formatter={(value) => compact(Number(value)) + " so'm"} />
            <Bar
              dataKey="value"
              name="Qoldiq"
              fill={colors[0]}
              radius={[0, 5, 5, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
