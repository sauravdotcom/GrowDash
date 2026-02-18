"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { AnalyticsResponse } from "@/lib/types";

type ChartsPanelProps = {
  analytics: AnalyticsResponse;
};

export function ChartsPanel({ analytics }: ChartsPanelProps) {
  return (
    <section className="charts-grid">
      <article className="chart-card">
        <h3>Daily PnL</h3>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={analytics.daily_pnl}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="pnl" stroke="#1f7a8c" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </article>

      <article className="chart-card">
        <h3>Monthly PnL</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={analytics.monthly_pnl}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="pnl" fill="#f4a259" />
          </BarChart>
        </ResponsiveContainer>
      </article>

      <article className="chart-card">
        <h3>CE vs PE Performance</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={analytics.ce_vs_pe}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="option_type" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="pnl" fill="#bf5f82" />
          </BarChart>
        </ResponsiveContainer>
      </article>

      <article className="chart-card">
        <h3>Most Traded Strikes</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={analytics.most_traded_strike}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="strike" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="quantity" fill="#2a9d8f" />
          </BarChart>
        </ResponsiveContainer>
      </article>
    </section>
  );
}
