"use client";

import { FormEvent, useState } from "react";

import { fetchCopilotAdvice } from "@/lib/api";
import { CopilotResponse } from "@/lib/types";

export function AiCopilotPanel() {
  const [question, setQuestion] = useState(
    "How can I reduce drawdown while keeping consistent returns?"
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [response, setResponse] = useState<CopilotResponse | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmed = question.trim();
    if (!trimmed || loading) {
      return;
    }

    try {
      setLoading(true);
      setError("");
      const data = await fetchCopilotAdvice({ question: trimmed });
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch AI guidance.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="copilot-card">
      <h3>AI Trading Copilot</h3>
      <p>
        Ask performance and risk-management questions based on your uploaded tradebook analytics.
      </p>

      <form onSubmit={handleSubmit} className="copilot-form">
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Example: What should I change if my win rate is low but average profit is high?"
          rows={4}
        />
        <button type="submit" disabled={loading || !question.trim()}>
          {loading ? "Thinking..." : "Ask Copilot"}
        </button>
      </form>

      {error ? <p className="message error">{error}</p> : null}

      {response ? (
        <div className="copilot-response">
          <p className="copilot-meta">
            Source: {response.provider}
            {response.model ? ` (${response.model})` : ""}
          </p>
          <p>{response.answer}</p>

          <div className="copilot-grid">
            <article>
              <h4>Action Items</h4>
              <ul>
                {response.action_items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>
            <article>
              <h4>Risk Flags</h4>
              <ul>
                {response.risk_flags.length ? (
                  response.risk_flags.map((item) => <li key={item}>{item}</li>)
                ) : (
                  <li>No critical risk flags detected from current metrics.</li>
                )}
              </ul>
            </article>
          </div>

          <p className="copilot-disclaimer">{response.disclaimer}</p>
        </div>
      ) : null}
    </section>
  );
}
