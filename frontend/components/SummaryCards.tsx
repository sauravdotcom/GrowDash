import { SummaryMetrics, TradeStats } from "@/lib/types";

type SummaryCardsProps = {
  summary: SummaryMetrics;
  tradeStats: TradeStats;
};

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
  }).format(value);
}

function formatValue(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "-";
  }
  return value.toFixed(2);
}

export function SummaryCards({ summary, tradeStats }: SummaryCardsProps) {
  return (
    <section className="cards-grid">
      <article className="card">
        <h3>Total P/L</h3>
        <p>{formatCurrency(summary.total_profit_loss)}</p>
      </article>
      <article className="card">
        <h3>Win Rate</h3>
        <p>{formatValue(summary.win_rate)}%</p>
      </article>
      <article className="card">
        <h3>Average Profit</h3>
        <p>{formatCurrency(summary.average_profit)}</p>
      </article>
      <article className="card">
        <h3>Average Loss</h3>
        <p>{formatCurrency(summary.average_loss)}</p>
      </article>
      <article className="card">
        <h3>Risk Reward Ratio</h3>
        <p>{summary.risk_reward_ratio === null ? "-" : formatValue(summary.risk_reward_ratio)}</p>
      </article>
      <article className="card">
        <h3>Max Drawdown</h3>
        <p>{formatCurrency(summary.max_drawdown)}</p>
      </article>
      <article className="card">
        <h3>Total Trades</h3>
        <p>{tradeStats.total_trades}</p>
      </article>
      <article className="card">
        <h3>Closed Lots</h3>
        <p>{tradeStats.closed_lots}</p>
      </article>
    </section>
  );
}
