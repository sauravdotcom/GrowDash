from __future__ import annotations

import json
from typing import Any
from urllib import error, request

from app.config import settings


def generate_copilot_response(question: str, analytics: dict[str, Any]) -> dict[str, Any]:
    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("Question is required.")

    base = _build_rule_based_guidance(cleaned_question, analytics)
    response = {
        "provider": "rule_based",
        "model": None,
        "answer": base["answer"],
        "action_items": base["action_items"],
        "risk_flags": base["risk_flags"],
        "disclaimer": _disclaimer_text(),
    }

    if not settings.openai_api_key:
        return response

    try:
        ai_answer = _query_openai(cleaned_question, analytics, base)
        response["provider"] = "openai"
        response["model"] = settings.openai_model
        response["answer"] = ai_answer
    except Exception:
        # Keep the dashboard usable even when external model calls fail.
        pass

    return response


def _build_rule_based_guidance(question: str, analytics: dict[str, Any]) -> dict[str, Any]:
    summary = analytics.get("summary", {})
    trade_stats = analytics.get("trade_stats", {})
    ce_vs_pe = analytics.get("ce_vs_pe", [])
    holding = analytics.get("holding_time", {})

    total_pnl = float(summary.get("total_profit_loss", 0.0))
    win_rate = float(summary.get("win_rate", 0.0))
    avg_profit = float(summary.get("average_profit", 0.0))
    avg_loss = float(summary.get("average_loss", 0.0))
    rr_ratio = summary.get("risk_reward_ratio")
    max_drawdown = float(summary.get("max_drawdown", 0.0))
    total_trades = int(trade_stats.get("total_trades", 0))

    action_items: list[str] = []
    risk_flags: list[str] = []

    if total_trades < 20:
        action_items.append("Collect at least 20-30 closed trades before changing strategy aggressively.")

    if win_rate < 45:
        action_items.append("Tighten your entry filter; avoid low-conviction setups to improve hit rate.")
        risk_flags.append("Win rate below 45% indicates selection quality risk.")

    if avg_loss > avg_profit:
        action_items.append("Use a stricter stop-loss and partial profit booking to improve average R-multiple.")
        risk_flags.append("Average loss is larger than average profit.")

    if rr_ratio is not None and float(rr_ratio) < 1.0:
        action_items.append("Target trades with at least 1:1.2 risk-reward profile before execution.")
        risk_flags.append("Risk-reward ratio is below 1.")

    if max_drawdown > max(abs(total_pnl), 1.0) * 0.6:
        action_items.append("Reduce position size by 20-30% until equity curve stabilizes.")
        risk_flags.append("Drawdown is too high relative to realized PnL.")

    if not action_items:
        action_items.append("Keep current process but review setup quality weekly with a trade journal.")

    option_bias = _option_bias_text(ce_vs_pe)
    holding_avg = float(holding.get("average_minutes", 0.0))

    answer = (
        f"Based on your uploaded trades: total PnL is {total_pnl:.2f}, win rate is {win_rate:.2f}%, "
        f"max drawdown is {max_drawdown:.2f}, and average holding time is {holding_avg:.2f} minutes. "
        f"{option_bias} For your question '{question}', focus first on execution consistency, "
        "risk-per-trade limits, and eliminating low edge entries."
    )

    return {
        "answer": answer,
        "action_items": action_items[:5],
        "risk_flags": risk_flags[:5],
    }


def _option_bias_text(ce_vs_pe: list[dict[str, Any]]) -> str:
    if not ce_vs_pe:
        return "CE/PE split is not yet available."

    ranked = sorted(ce_vs_pe, key=lambda item: float(item.get("pnl", 0.0)), reverse=True)
    leader = ranked[0]
    option_type = str(leader.get("option_type", "UNKNOWN"))
    pnl_value = float(leader.get("pnl", 0.0))
    return f"Best side currently is {option_type} with realized PnL {pnl_value:.2f}."


def _query_openai(question: str, analytics: dict[str, Any], base: dict[str, Any]) -> str:
    prompt_payload = {
        "question": question,
        "analytics": {
            "summary": analytics.get("summary", {}),
            "trade_stats": analytics.get("trade_stats", {}),
            "ce_vs_pe": analytics.get("ce_vs_pe", []),
            "most_traded_strike": analytics.get("most_traded_strike", [])[:5],
            "holding_time": analytics.get("holding_time", {}),
        },
        "base_guidance": base,
    }

    body = {
        "model": settings.openai_model,
        "input": [
            {
                "role": "system",
                "content": (
                    "You are a trading performance coach. Use only the provided analytics context, "
                    "be concise, and avoid guaranteed-return language."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Analyze the trading dashboard context and answer the user's question. "
                    "Return concise, practical guidance in plain text.\n\n"
                    + json.dumps(prompt_payload)
                ),
            },
        ],
    }

    encoded = json.dumps(body).encode("utf-8")
    req = request.Request(
        "https://api.openai.com/v1/responses",
        data=encoded,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        raise RuntimeError(f"OpenAI request failed with status {exc.code}") from exc
    except error.URLError as exc:
        raise RuntimeError("OpenAI request network failure") from exc

    payload = json.loads(raw)
    text = payload.get("output_text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    return _extract_text_from_output(payload)


def _extract_text_from_output(payload: dict[str, Any]) -> str:
    output_items = payload.get("output", [])
    if not isinstance(output_items, list):
        raise RuntimeError("Unexpected OpenAI response payload.")

    parts: list[str] = []
    for item in output_items:
        content_list = item.get("content", []) if isinstance(item, dict) else []
        if not isinstance(content_list, list):
            continue
        for content in content_list:
            if not isinstance(content, dict):
                continue
            text_value = content.get("text")
            if isinstance(text_value, str) and text_value.strip():
                parts.append(text_value.strip())

    combined = "\n".join(parts).strip()
    if not combined:
        raise RuntimeError("No text returned by model.")

    return combined


def _disclaimer_text() -> str:
    return (
        "AI guidance is educational, based on your uploaded historical trades, and not investment advice. "
        "Always validate with your own risk rules."
    )
