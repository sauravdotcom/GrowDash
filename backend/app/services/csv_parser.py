from __future__ import annotations

import csv
import hashlib
import re
from datetime import date, datetime, time, timedelta
from io import StringIO
from typing import Any

import pandas as pd


COLUMN_ALIASES = {
    "order_id": ["orderid", "order id", "orderno", "order number", "exchange order id"],
    "symbol": ["tradingsymbol", "symbol", "instrument", "scrip", "security"],
    "exchange": ["exchange"],
    "segment": ["segment", "product", "product type"],
    "side": ["side", "trade type", "transaction type", "type", "action"],
    "quantity": ["quantity", "qty", "filled quantity", "traded qty"],
    "price": ["price", "average price", "trade price", "executed price"],
    "datetime": ["datetime", "trade time", "order executed time", "timestamp"],
    "date": ["date", "trade date"],
    "time": ["time"],
    "strike": ["strike", "strike price"],
    "option_type": ["option type", "optiontype", "type cepe"],
    "expiry": ["expiry", "expiry date"],
}

STATEMENT_STOP_TOKENS = {
    "total",
    "summary",
    "charges",
    "disclaimer",
    "realisedtradestradelevel",
    "realisedtradescontractlevel",
}


def _normalize_col(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name).lower().strip())


def _safe_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime().isoformat()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        value = value.item()
    return value


def _map_columns(columns: list[str]) -> dict[str, str]:
    normalized = {_normalize_col(col): col for col in columns}
    mapped: dict[str, str] = {}

    for canonical_name, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            resolved = normalized.get(_normalize_col(alias))
            if resolved:
                mapped[canonical_name] = resolved
                break

    return mapped


def _extract_option_meta(symbol: str) -> tuple[float | None, str | None]:
    if not symbol:
        return None, None

    upper_symbol = symbol.upper()
    compact_symbol = re.sub(r"\s+", "", upper_symbol)

    match = re.search(r"(\d+(?:\.\d+)?)(CE|PE)\b", compact_symbol)
    if match:
        return float(match.group(1)), match.group(2)

    match = re.search(r"(\d+(?:\.\d+)?)\s*(CALL|PUT)\b", upper_symbol)
    if match:
        option_type = "CE" if match.group(2) == "CALL" else "PE"
        return float(match.group(1)), option_type

    return None, None


def _extract_expiry_from_symbol(symbol: str) -> date | None:
    if not symbol:
        return None

    upper_symbol = symbol.upper()
    match = re.search(r"\b(\d{1,2})\s+([A-Z]{3})\s+(\d{2,4})\b", upper_symbol)
    if not match:
        return None

    day = int(match.group(1))
    month_abbr = match.group(2).title()
    year_raw = match.group(3)
    year = int(year_raw)
    if len(year_raw) == 2:
        year += 2000

    parsed = pd.to_datetime(
        f"{day:02d} {month_abbr} {year}",
        format="%d %b %Y",
        errors="coerce",
    )
    if pd.isna(parsed):
        return None

    return parsed.date()


def _parse_datetime(row: pd.Series, column_map: dict[str, str]) -> datetime:
    date_time_col = column_map.get("datetime")
    date_col = column_map.get("date")
    time_col = column_map.get("time")

    parsed = pd.NaT
    if date_time_col:
        parsed = pd.to_datetime(row[date_time_col], errors="coerce")

    if pd.isna(parsed) and date_col and time_col:
        parsed = pd.to_datetime(
            f"{_safe_string(row[date_col])} {_safe_string(row[time_col])}",
            errors="coerce",
            dayfirst=False,
        )

    if pd.isna(parsed) and date_col:
        parsed = pd.to_datetime(row[date_col], errors="coerce", dayfirst=False)

    if pd.isna(parsed):
        raise ValueError("Unable to parse trade timestamp. Ensure CSV has Date/Time columns.")

    return parsed.to_pydatetime().replace(tzinfo=None)


def _parse_numeric(value: Any) -> float | None:
    text = _safe_string(value).replace(",", "")
    if not text:
        return None

    number = pd.to_numeric(text, errors="coerce")
    if pd.isna(number):
        return None

    return float(number)


def _parse_statement_date(value: Any) -> date | None:
    text = _safe_string(value)
    if not text:
        return None

    parsed = pd.to_datetime(text, errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        return None

    return parsed.date()


def _build_trade_record(
    *,
    symbol: str,
    side: str,
    quantity: int,
    price: float,
    traded_at: datetime,
    order_id: str | None = None,
    exchange: str | None = None,
    segment: str | None = None,
    strike: float | None = None,
    option_type: str | None = None,
    expiry: date | None = None,
    raw_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dedupe_basis = (
        f"{order_id or ''}|{symbol}|{side}|{quantity}|"
        f"{price:.8f}|{traded_at.isoformat()}"
    )
    trade_hash = hashlib.sha256(dedupe_basis.encode("utf-8")).hexdigest()

    return {
        "trade_hash": trade_hash,
        "order_id": order_id or None,
        "symbol": symbol,
        "exchange": exchange or None,
        "segment": segment or None,
        "side": side,
        "quantity": quantity,
        "price": float(price),
        "traded_at": traded_at,
        "strike": strike,
        "option_type": option_type,
        "expiry": expiry,
        "raw_payload": raw_payload or {},
    }


def _parse_standard_tradebook(content: str) -> list[dict[str, Any]]:
    dataframe = pd.read_csv(StringIO(content))
    dataframe = dataframe.dropna(how="all")

    if dataframe.empty:
        return []

    column_map = _map_columns(dataframe.columns.tolist())
    required_columns = ["symbol", "side", "quantity", "price"]
    missing = [name for name in required_columns if not column_map.get(name)]
    if missing:
        raise ValueError(
            f"CSV is missing required columns for parsing: {', '.join(missing)}"
        )

    trades: list[dict[str, Any]] = []

    for _, row in dataframe.iterrows():
        symbol = _safe_string(row[column_map["symbol"]])
        if not symbol:
            continue

        side_raw = _safe_string(row[column_map["side"]]).upper()
        side = "BUY" if side_raw.startswith("B") else "SELL" if side_raw.startswith("S") else side_raw
        if side not in {"BUY", "SELL"}:
            continue

        quantity_number = _parse_numeric(row[column_map["quantity"]])
        price_number = _parse_numeric(row[column_map["price"]])
        if quantity_number is None or price_number is None:
            continue

        quantity = int(abs(quantity_number))
        price = float(price_number)
        if quantity <= 0:
            continue

        traded_at = _parse_datetime(row, column_map)

        order_id = _safe_string(row[column_map["order_id"]]) if column_map.get("order_id") else None
        exchange = _safe_string(row[column_map["exchange"]]) if column_map.get("exchange") else None
        segment = _safe_string(row[column_map["segment"]]) if column_map.get("segment") else None

        inferred_strike, inferred_option_type = _extract_option_meta(symbol)
        strike = inferred_strike
        if column_map.get("strike"):
            strike_number = _parse_numeric(row[column_map["strike"]])
            if strike_number is not None:
                strike = float(strike_number)

        option_type = inferred_option_type
        if column_map.get("option_type"):
            option_type_raw = _safe_string(row[column_map["option_type"]]).upper()
            if option_type_raw in {"CE", "PE"}:
                option_type = option_type_raw

        expiry = _extract_expiry_from_symbol(symbol)
        if column_map.get("expiry"):
            expiry_ts = pd.to_datetime(row[column_map["expiry"]], errors="coerce", dayfirst=False)
            if not pd.isna(expiry_ts):
                expiry = expiry_ts.date()

        row_payload = {col: _jsonable(row[col]) for col in dataframe.columns}

        trades.append(
            _build_trade_record(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                traded_at=traded_at,
                order_id=order_id or None,
                exchange=exchange or None,
                segment=segment or None,
                strike=strike,
                option_type=option_type,
                expiry=expiry,
                raw_payload=row_payload,
            )
        )

    return trades


def _parse_realized_statement_csv(content: str) -> list[dict[str, Any]]:
    rows = [
        [_safe_string(cell) for cell in csv_row]
        for csv_row in csv.reader(StringIO(content))
    ]

    trades: list[dict[str, Any]] = []
    row_index = 0

    while row_index < len(rows):
        header_row = rows[row_index]
        normalized_header = [_normalize_col(cell) for cell in header_row]
        header_map = {
            key: idx
            for idx, key in enumerate(normalized_header)
            if key
        }

        symbol_idx = header_map.get("scripname")
        quantity_idx = header_map.get("quantity")
        buy_date_idx = header_map.get("buydate")
        sell_date_idx = header_map.get("selldate")
        buy_price_idx = header_map.get("buyprice", header_map.get("avgbuyprice"))
        sell_price_idx = header_map.get("sellprice", header_map.get("avgsellprice"))

        if (
            symbol_idx is None
            or quantity_idx is None
            or buy_price_idx is None
            or sell_price_idx is None
        ):
            row_index += 1
            continue

        source_format = (
            "trade_level"
            if buy_date_idx is not None and sell_date_idx is not None
            else "contract_level"
        )

        data_index = row_index + 1
        while data_index < len(rows):
            data_row = rows[data_index]
            if not any(_safe_string(cell) for cell in data_row):
                break

            symbol = _safe_string(data_row[symbol_idx]) if symbol_idx < len(data_row) else ""
            symbol_token = _normalize_col(symbol)
            if not symbol:
                data_index += 1
                continue
            if symbol_token in {"scripname", "futures", "options"}:
                data_index += 1
                continue
            if symbol_token in STATEMENT_STOP_TOKENS:
                break

            quantity_value = _parse_numeric(data_row[quantity_idx] if quantity_idx < len(data_row) else "")
            buy_price_value = _parse_numeric(data_row[buy_price_idx] if buy_price_idx < len(data_row) else "")
            sell_price_value = _parse_numeric(data_row[sell_price_idx] if sell_price_idx < len(data_row) else "")
            if quantity_value is None or buy_price_value is None or sell_price_value is None:
                data_index += 1
                continue

            quantity = int(abs(quantity_value))
            if quantity <= 0:
                data_index += 1
                continue

            strike, option_type = _extract_option_meta(symbol)
            expiry = _extract_expiry_from_symbol(symbol)
            segment = "OPTIONS" if option_type in {"CE", "PE"} else None

            fallback_date = expiry or date.today()
            buy_date_value = (
                _parse_statement_date(data_row[buy_date_idx])
                if buy_date_idx is not None and buy_date_idx < len(data_row)
                else None
            )
            sell_date_value = (
                _parse_statement_date(data_row[sell_date_idx])
                if sell_date_idx is not None and sell_date_idx < len(data_row)
                else None
            )

            buy_date_value = buy_date_value or fallback_date
            sell_date_value = sell_date_value or buy_date_value

            buy_datetime = datetime.combine(buy_date_value, time(hour=9, minute=15))
            sell_datetime = datetime.combine(sell_date_value, time(hour=15, minute=15))
            if sell_datetime <= buy_datetime:
                sell_datetime = buy_datetime + timedelta(minutes=1)

            row_payload = {
                (_safe_string(header_row[col_idx]) or f"col_{col_idx}"): (
                    _safe_string(data_row[col_idx]) if col_idx < len(data_row) else ""
                )
                for col_idx in range(len(header_row))
            }
            row_payload["source_format"] = source_format

            trades.append(
                _build_trade_record(
                    symbol=symbol,
                    side="BUY",
                    quantity=quantity,
                    price=float(buy_price_value),
                    traded_at=buy_datetime,
                    segment=segment,
                    strike=strike,
                    option_type=option_type,
                    expiry=expiry,
                    raw_payload={**row_payload, "synthetic_side": "BUY"},
                )
            )
            trades.append(
                _build_trade_record(
                    symbol=symbol,
                    side="SELL",
                    quantity=quantity,
                    price=float(sell_price_value),
                    traded_at=sell_datetime,
                    segment=segment,
                    strike=strike,
                    option_type=option_type,
                    expiry=expiry,
                    raw_payload={**row_payload, "synthetic_side": "SELL"},
                )
            )

            data_index += 1

        row_index = data_index

    return trades


def parse_tradebook_csv(file_bytes: bytes) -> list[dict[str, Any]]:
    content = file_bytes.decode("utf-8-sig")

    standard_error: ValueError | None = None
    try:
        standard_trades = _parse_standard_tradebook(content)
        if standard_trades:
            return standard_trades
    except ValueError as exc:
        standard_error = exc
    except Exception as exc:
        standard_error = ValueError(f"Unable to parse CSV: {exc}")

    statement_trades = _parse_realized_statement_csv(content)
    if statement_trades:
        return statement_trades

    if standard_error:
        raise standard_error

    return []
