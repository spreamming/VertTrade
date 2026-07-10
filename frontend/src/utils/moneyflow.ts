import type { MoneyflowBar } from "../types/stock";

export type MoneyflowView = "main" | "super_large" | "wide" | "retail";

export const MONEYFLOW_VIEW_STORAGE_KEY = "verttrade-moneyflow-view";

export type MoneyflowViewOption = {
  value: MoneyflowView;
  label: string;
  shortLabel: string;
  description: string;
  needsBreakdown: boolean;
};

export const MONEYFLOW_VIEW_OPTIONS: MoneyflowViewOption[] = [
  {
    value: "main",
    label: "主力（超大+大）",
    shortLabel: "主力",
    description: "数据商口径下的主力净流入，通常对应超大单与大单合计。",
    needsBreakdown: false,
  },
  {
    value: "super_large",
    label: "仅超大单",
    shortLabel: "超大单",
    description: "只看超大单净流入，更接近机构/核心资金动向。",
    needsBreakdown: true,
  },
  {
    value: "wide",
    label: "宽口径（超+大+中）",
    shortLabel: "宽口径",
    description: "超大、大、中单合计，覆盖更广的资金行为。",
    needsBreakdown: true,
  },
  {
    value: "retail",
    label: "散户（小单）",
    shortLabel: "小单",
    description: "小单净流入，用于与主力侧资金对比观察。",
    needsBreakdown: true,
  },
];

function sumDefined(values: Array<number | null | undefined>): number | null {
  const defined = values.filter((value): value is number => value != null);
  if (defined.length !== values.length) {
    return null;
  }
  return defined.reduce((total, value) => total + value, 0);
}

export function isMoneyflowView(value: string): value is MoneyflowView {
  return MONEYFLOW_VIEW_OPTIONS.some((option) => option.value === value);
}

export function getMoneyflowViewOption(view: MoneyflowView): MoneyflowViewOption {
  return (
    MONEYFLOW_VIEW_OPTIONS.find((option) => option.value === view) ??
    MONEYFLOW_VIEW_OPTIONS[0]
  );
}

export function readStoredMoneyflowView(): MoneyflowView {
  if (typeof window === "undefined") {
    return "main";
  }
  const saved = window.localStorage.getItem(MONEYFLOW_VIEW_STORAGE_KEY);
  if (saved && isMoneyflowView(saved)) {
    return saved;
  }
  return "main";
}

export function storeMoneyflowView(view: MoneyflowView): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(MONEYFLOW_VIEW_STORAGE_KEY, view);
}

export function hasMoneyflowBreakdown(bars: MoneyflowBar[]): boolean {
  return bars.some(
    (bar) =>
      bar.super_large_net_inflow != null ||
      bar.large_net_inflow != null ||
      bar.medium_net_inflow != null ||
      bar.small_net_inflow != null,
  );
}

export function resolveMoneyflowNet(
  bar: MoneyflowBar,
  view: MoneyflowView,
): number | null {
  switch (view) {
    case "super_large":
      return bar.super_large_net_inflow ?? null;
    case "wide":
      return sumDefined([
        bar.super_large_net_inflow,
        bar.large_net_inflow,
        bar.medium_net_inflow,
      ]);
    case "retail":
      return bar.small_net_inflow ?? null;
    case "main":
    default: {
      const breakdown = sumDefined([
        bar.super_large_net_inflow,
        bar.large_net_inflow,
      ]);
      if (breakdown != null) {
        return breakdown;
      }
      return bar.main_net_inflow ?? null;
    }
  }
}

export function resolveMoneyflowNetRatio(
  bar: MoneyflowBar,
  view: MoneyflowView,
): number | null {
  if (view === "main") {
    return bar.main_net_ratio ?? null;
  }
  return null;
}

export function moneyflowFlowLabel(view: MoneyflowView, value: number): string {
  const option = getMoneyflowViewOption(view);
  return value >= 0 ? `${option.shortLabel}净流入` : `${option.shortLabel}净流出`;
}

export function isMoneyflowViewAvailable(
  bars: MoneyflowBar[],
  view: MoneyflowView,
): boolean {
  const option = getMoneyflowViewOption(view);
  if (!option.needsBreakdown) {
    return true;
  }
  if (!hasMoneyflowBreakdown(bars)) {
    return false;
  }
  return bars.some((bar) => resolveMoneyflowNet(bar, view) != null);
}
