import type { Filters } from "../../api";
import { previousMonth, today } from "../../utils/format";
import { MonthPicker, Tabs } from "./ui";
export interface PeriodState {
  mode: string;
  month: string;
  start: string;
  end: string;
}
export const initialPeriod = (): PeriodState => ({
  mode: "month",
  month: today().slice(0, 7),
  start: today().slice(0, 7) + "-01",
  end: today(),
});
export const periodParams = (period: PeriodState): Filters =>
  period.mode === "custom"
    ? { start: period.start, end: period.end }
    : { month: period.month };
export function PeriodFilter({
  value,
  onChange,
}: {
  value: PeriodState;
  onChange: (v: PeriodState) => void;
}) {
  return (
    <div className="period-filter">
      <Tabs
        value={value.mode}
        items={[
          ["month", "Oy"],
          ["previous", "O'tgan oy"],
          ["custom", "Davr"],
        ]}
        onChange={(mode) =>
          onChange({
            ...value,
            mode,
            month:
              mode === "previous"
                ? previousMonth(today().slice(0, 7))
                : today().slice(0, 7),
          })
        }
      />
      {value.mode === "custom" ? (
        <div className="filters">
          <label className="filter">
            Boshlanish
            <input
              type="date"
              required
              value={value.start}
              max={value.end}
              onChange={(e) =>
                e.target.value && onChange({ ...value, start: e.target.value })
              }
            />
          </label>
          <label className="filter">
            Tugash
            <input
              type="date"
              required
              value={value.end}
              min={value.start}
              onChange={(e) =>
                e.target.value && onChange({ ...value, end: e.target.value })
              }
            />
          </label>
        </div>
      ) : (
        <MonthPicker
          value={value.month}
          onChange={(month) => onChange({ ...value, month })}
        />
      )}
    </div>
  );
}
