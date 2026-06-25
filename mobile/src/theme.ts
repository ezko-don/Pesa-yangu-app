export const colors = {
  primary: "#0E9F6E",
  primaryDark: "#0B7D57",
  primaryLight: "#E7F6EF",
  bg: "#F3F5F7",
  card: "#FFFFFF",
  text: "#14202B",
  muted: "#6B7785",
  border: "#E6EAEE",
  success: "#16A34A",
  successBg: "#E7F6EF",
  danger: "#E5484D",
  dangerBg: "#FCEBEB",
  warning: "#D97706",
  warningBg: "#FDF3E7",
  blue: "#2563EB",
  white: "#FFFFFF",
  trackBg: "#EDF0F2",
};

export const spacing = (n: number) => n * 4;

export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 22,
  pill: 999,
};

export const shadow = {
  shadowColor: "#0B2030",
  shadowOpacity: 0.06,
  shadowRadius: 12,
  shadowOffset: { width: 0, height: 4 },
  elevation: 2,
};

export function formatKES(value: number | string, withSymbol = true): string {
  const n = typeof value === "string" ? parseFloat(value) : value;
  const safe = Number.isFinite(n) ? n : 0;
  const formatted = Math.round(safe).toLocaleString("en-KE");
  return withSymbol ? `KES ${formatted}` : formatted;
}

export function compactKES(value: number | string): string {
  const n = typeof value === "string" ? parseFloat(value) : value;
  const safe = Number.isFinite(n) ? n : 0;
  const abs = Math.abs(safe);
  if (abs >= 1_000_000) return `KES ${(safe / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `KES ${Math.round(safe / 1_000)}K`;
  return `KES ${Math.round(safe)}`;
}
