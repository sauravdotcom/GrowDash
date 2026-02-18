export type UploadResponse = {
  total_rows: number;
  imported_rows: number;
  skipped_rows: number;
};

export type SummaryMetrics = {
  total_profit_loss: number;
  win_rate: number;
  average_profit: number;
  average_loss: number;
  risk_reward_ratio: number | null;
  max_drawdown: number;
};

export type DailyPnlPoint = {
  date: string;
  pnl: number;
};

export type MonthlyPnlPoint = {
  month: string;
  pnl: number;
};

export type CePePoint = {
  option_type: string;
  pnl: number;
};

export type StrikePoint = {
  strike: string;
  quantity: number;
};

export type HoldingTime = {
  average_minutes: number;
  median_minutes: number;
  min_minutes: number;
  max_minutes: number;
};

export type TradeStats = {
  total_trades: number;
  closed_lots: number;
};

export type AnalyticsResponse = {
  summary: SummaryMetrics;
  daily_pnl: DailyPnlPoint[];
  monthly_pnl: MonthlyPnlPoint[];
  ce_vs_pe: CePePoint[];
  most_traded_strike: StrikePoint[];
  holding_time: HoldingTime;
  trade_stats: TradeStats;
};

export type CopilotRequest = {
  question: string;
};

export type CopilotResponse = {
  provider: string;
  model: string | null;
  answer: string;
  action_items: string[];
  risk_flags: string[];
  disclaimer: string;
};
