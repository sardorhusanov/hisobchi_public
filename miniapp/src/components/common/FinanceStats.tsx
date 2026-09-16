import type { FinanceSummary } from "../../types/models";
import { MoneyStat } from "./ui";
export function FinanceStats({
  data,
  detailed = false,
}: {
  data: FinanceSummary;
  detailed?: boolean;
}) {
  return (
    <div className="stats-grid">
      <MoneyStat label="Tushum" value={data.income} />
      <MoneyStat
        label={detailed ? "Biznes xarajatlari" : "Xarajat"}
        value={detailed ? data.business_expenses : data.expenses}
      />
      <MoneyStat label="Avans" value={data.advances} />
      <MoneyStat label="Sof pul harakati" value={data.net_cash_flow} accent />
      {detailed && (
        <>
          <MoneyStat label="Egasi olgan" value={data.owner_withdrawals} />
          <MoneyStat label="Hamkor olgan" value={data.partner_withdrawals} />
          <MoneyStat label="Boshqa xarajatlar" value={data.other_expenses} />
          <MoneyStat label="Jami xarajatlar" value={data.expenses} />
        </>
      )}
    </div>
  );
}
