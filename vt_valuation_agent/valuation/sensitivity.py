"""Two-way sensitivity tables for the DCF."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

from .dcf import dcf_valuation


@dataclass
class SensitivityTable:
    output: str
    row_label: str
    column_label: str
    rows: list[float]
    columns: list[float]
    values: list[list[float | None]]

    def to_dict(self) -> dict:
        return asdict(self)

    def to_markdown(self, fmt: str = "{:,.1f}") -> str:
        header = f"| {self.row_label} \\ {self.column_label} | " + " | ".join(_fmt_axis(c) for c in self.columns) + " |"
        sep = "|" + "---|" * (len(self.columns) + 1)
        lines = [header, sep]
        for r, row in zip(self.rows, self.values):
            cells = ["n/a" if v is None else fmt.format(v) for v in row]
            lines.append(f"| {_fmt_axis(r)} | " + " | ".join(cells) + " |")
        return "\n".join(lines)


def dcf_sensitivity(
    free_cash_flows: Sequence[float],
    discount_rates: Sequence[float],
    terminal_growth_rates: Sequence[float] | None = None,
    exit_multiples: Sequence[float] | None = None,
    terminal_metric: float | None = None,
    output: str = "enterprise_value",
    **dcf_kwargs,
) -> SensitivityTable:
    """Grid of DCF outputs across discount rates (rows) and terminal
    assumptions (columns). ``output`` is any numeric field of ``DcfResult``,
    typically ``enterprise_value``, ``equity_value`` or ``value_per_share``.
    Cells where the DCF is undefined (e.g. g >= r) are ``None``.
    """
    if (terminal_growth_rates is None) == (exit_multiples is None):
        raise ValueError("provide exactly one of terminal_growth_rates or exit_multiples")
    if terminal_growth_rates is not None:
        columns = list(terminal_growth_rates)
        col_label = "terminal growth"
    else:
        columns = list(exit_multiples or [])
        col_label = "exit multiple"
    rows = list(discount_rates)
    if not rows or not columns:
        raise ValueError("discount_rates and the terminal axis must be non-empty")

    values: list[list[float | None]] = []
    for r in rows:
        line: list[float | None] = []
        for c in columns:
            try:
                if terminal_growth_rates is not None:
                    res = dcf_valuation(free_cash_flows, r, terminal_growth=c, terminal_metric=terminal_metric, **dcf_kwargs)
                else:
                    res = dcf_valuation(free_cash_flows, r, exit_multiple=c, terminal_metric=terminal_metric, **dcf_kwargs)
                val = getattr(res, output)
                line.append(None if val is None else float(val))
            except (ValueError, AttributeError):
                line.append(None)
        values.append(line)
    return SensitivityTable(output=output, row_label="discount rate", column_label=col_label, rows=rows, columns=columns, values=values)


def _fmt_axis(v: float) -> str:
    if abs(v) < 1.0:
        return f"{v * 100:.1f}%"
    return f"{v:.1f}x"
