/**
 * Standardized Formatting Helpers for SarmayaSaaz
 * Enforces exact 2 decimal precision (1.23, 17.00%) site-wide.
 */

export function formatNumber(val: number | null | undefined, decimals = 2): string {
  if (val === null || val === undefined || isNaN(val)) return `0.${'0'.repeat(decimals)}`;
  return val.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatPercent(
  val: number | null | undefined,
  decimals = 2,
  showSign = false
): string {
  if (val === null || val === undefined || isNaN(val)) return `0.${'0'.repeat(decimals)}%`;
  const formatted = Math.abs(val).toFixed(decimals);
  const sign = showSign && val > 0 ? '+' : val < 0 ? '-' : '';
  return `${sign}${formatted}%`;
}

export function formatCurrency(
  val: number | null | undefined,
  currency = '$',
  decimals = 2
): string {
  if (val === null || val === undefined || isNaN(val)) return `${currency}0.${'0'.repeat(decimals)}`;
  const formatted = val.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  return `${currency}${formatted}`;
}
