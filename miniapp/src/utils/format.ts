// Format decimal strings exactly. No JavaScript floating-point accounting.
export function formatMoney(value: string): string {
  const negative = value.startsWith("-");
  const [whole, fraction = ""] = value.replace(/^-/, "").split(".");
  let cents =
    BigInt(whole) * 100n + BigInt(fraction.slice(0, 2).padEnd(2, "0"));
  if ((fraction[2] ?? "0") >= "5") cents += 1n;
  const digits = (cents / 100n)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  const decimals = (cents % 100n).toString().padStart(2, "0");
  return `${negative && cents !== 0n ? "-" : ""}${digits}${decimals === "00" ? "" : "." + decimals} so'm`;
}

export function normalizeMoney(text: string): string {
  const value = text.trim();
  if (
    !/^(?:\d+|\d{1,3}(?: \d{3})+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?$/.test(value)
  )
    throw new Error("Summani kiriting: 6 000 000");
  const normalized = value.replace(/[ ,]/g, "");
  const [whole, fraction = ""] = normalized.split(".");
  const cents = BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0"));
  if (cents <= 0n || cents > 999999999999999999n)
    throw new Error("Musbat va ruxsat etilgan summani kiriting.");
  return normalized;
}
export const months = [
  "Yanvar",
  "Fevral",
  "Mart",
  "Aprel",
  "May",
  "Iyun",
  "Iyul",
  "Avgust",
  "Sentabr",
  "Oktabr",
  "Noyabr",
  "Dekabr",
];
export function monthLabel(month: string) {
  const [year, index] = month.split("-");
  return `${months[Number(index) - 1]} ${year}`;
}
export function dateLabel(value: string) {
  const [year, month, day] = value.slice(0, 10).split("-");
  return `${day}.${month}.${year}`;
}
export function today() {
  return new Intl.DateTimeFormat("sv-SE", {
    timeZone: "Asia/Tashkent",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}
export function previousMonth(month: string) {
  const [year, index] = month.split("-").map(Number);
  return `${index === 1 ? year - 1 : year}-${String(index === 1 ? 12 : index - 1).padStart(2, "0")}`;
}
export const roleLabel = {
  OWNER: "Egasi",
  PARTNER: "Hamkor",
  WORKER: "Ishchi",
};
export const categoryLabel = {
  BUSINESS: "Biznes xarajati",
  OWNER: "Egasi uchun",
  PARTNER: "Hamkor uchun",
  OTHER: "Boshqa",
};
