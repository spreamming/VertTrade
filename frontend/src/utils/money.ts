export function formatMoneyAmount(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "--";
  }

  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";

  if (abs >= 100_000_000) {
    return `${sign}${(abs / 100_000_000).toFixed(2)} 亿`;
  }
  if (abs >= 10_000) {
    return `${sign}${(abs / 10_000).toFixed(2)} 万`;
  }

  return value.toLocaleString(undefined, {
    maximumFractionDigits: 0,
  });
}
