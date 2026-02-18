"use client";

import { useEffect, useState } from "react";

import { ChartsPanel } from "@/components/ChartsPanel";
import { AiCopilotPanel } from "@/components/AiCopilotPanel";
import { SummaryCards } from "@/components/SummaryCards";
import { UploadPanel } from "@/components/UploadPanel";
import { fetchAnalytics, uploadTradebook } from "@/lib/api";
import { AnalyticsResponse } from "@/lib/types";

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");

  async function loadAnalytics() {
    try {
      setLoading(true);
      const data = await fetchAnalytics();
      setAnalytics(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch analytics data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadAnalytics();
  }, []);

  async function handleUpload(file: File): Promise<boolean> {
    try {
      setUploading(true);
      setMessage("");
      setError("");

      const result = await uploadTradebook(file);
      setMessage(
        `Imported ${result.imported_rows} rows (${result.skipped_rows} duplicates skipped from ${result.total_rows} parsed rows).`
      );
      await loadAnalytics();
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
      return false;
    } finally {
      setUploading(false);
    }
  }

  return (
    <main className="page">
      <section className="header">
        <div>
          <h1>GrowDash Personal Trading Analytics</h1>
          <p>
            Upload your Groww Tradebook CSV files and track PnL, drawdown, win-rate, CE/PE performance,
            most traded strikes, and holding behavior.
          </p>
        </div>
      </section>

      <UploadPanel uploading={uploading} onUpload={handleUpload} />

      {message ? <p className="message success">{message}</p> : null}
      {error ? <p className="message error">{error}</p> : null}

      {loading ? <p>Loading analytics...</p> : null}

      <AiCopilotPanel />

      {!loading && analytics ? (
        <>
          <SummaryCards summary={analytics.summary} tradeStats={analytics.trade_stats} />

          <section className="holding-card">
            <h3>Holding Time Analysis (minutes)</h3>
            <div className="holding-grid">
              <p>
                <span>Average</span>
                {analytics.holding_time.average_minutes}
              </p>
              <p>
                <span>Median</span>
                {analytics.holding_time.median_minutes}
              </p>
              <p>
                <span>Min</span>
                {analytics.holding_time.min_minutes}
              </p>
              <p>
                <span>Max</span>
                {analytics.holding_time.max_minutes}
              </p>
            </div>
          </section>

          <ChartsPanel analytics={analytics} />
        </>
      ) : null}
    </main>
  );
}
