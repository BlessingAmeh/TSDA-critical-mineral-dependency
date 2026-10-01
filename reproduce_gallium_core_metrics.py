#!/usr/bin/env python3
"""Reproduce/check core TSDA gallium outputs from the public v10 workbook.

Usage:
    python reproduce_gallium_core_metrics.py TSDA_gallium_trace_master_v10.xlsx

Important: the workbook's public summary groups small supplier countries into an
"Other countries" category. HHI cannot be recomputed exactly after that grouping,
because squaring an aggregate residual differs from summing squared country shares.
Accordingly, this script reads the exact full-country direct-supplier HHI preserved
in the workbook's Section 10 output, while independently checking dominant shares,
production concentration, attribution scenarios, and Section 8 validation metrics.
"""
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd

SUPPLIERS = ["Canada", "Germany", "Japan", "China", "Taiwan", "Other countries"]


def find_row(df, value, col=0):
    matches = df.index[df.iloc[:, col].astype(str).str.strip() == value].tolist()
    if not matches:
        raise KeyError(f"Could not find row {value!r}")
    return matches[0]


def main(path: str) -> None:
    book = Path(path)
    if not book.exists():
        raise SystemExit(f"Workbook not found: {book}")

    prelim = pd.read_excel(book, sheet_name="Preliminary TSDA Result", header=None)

    # Exact direct HHI is preserved in the Section 10 output.
    hhi_row = find_row(prelim, "Direct-supplier HHI")
    direct_hhi_base = float(prelim.iloc[hhi_row, 1])
    direct_hhi_post = float(prelim.iloc[hhi_row, 2])

    # Dominant shares can be checked from the displayed pooled supplier shares.
    baseline, post = [], []
    for supplier in SUPPLIERS:
        r = find_row(prelim, supplier)
        baseline.append(float(prelim.iloc[r, 1]))
        post.append(float(prelim.iloc[r, 2]))

    print("DIRECT U.S. SUPPLIER CONCENTRATION")
    print(f"2019-2022 pooled HHI: {direct_hhi_base:,.1f}")
    print(f"2023-2025 pooled HHI: {direct_hhi_post:,.1f}")
    print(f"Change: {direct_hhi_post-direct_hhi_base:+,.1f}")
    print(f"Dominant baseline supplier share: {max(baseline)*100:.2f}%")
    print(f"Dominant post-shock supplier share: {max(post)*100:.2f}%")
    print("Note: exact HHI uses the underlying full-country distribution; the public summary groups smaller countries as 'Other'.")
    print()

    prod = pd.read_excel(book, sheet_name="Production HHI", header=None)
    rows = prod.index[prod.iloc[:,0].astype(str).str.strip() == "Principal latest-revised"].tolist()
    if len(rows) < 2:
        raise KeyError("Could not find both principal pooled production rows")
    p_base, p_post = prod.iloc[rows[0]], prod.iloc[rows[1]]

    print("PRIMARY PRODUCTION CONCENTRATION")
    print(f"2019-2022 pooled HHI: {float(p_base.iloc[5]):,.1f}")
    print(f"2023-2025 pooled HHI: {float(p_post.iloc[5]):,.1f}")
    print(f"Change: {float(p_post.iloc[6]):+,.1f}")
    print(f"China share, baseline: {float(p_base.iloc[4])*100:.2f}%")
    print(f"China share, post-shock: {float(p_post.iloc[4])*100:.2f}%")
    print()

    bounds = pd.read_excel(book, sheet_name="True-Source Bounds", header=None)
    rb = find_row(bounds, "2019–2022 baseline")
    rp = find_row(bounds, "2023–2025 post-shock")
    print("TRUE-SOURCE ATTRIBUTION SCENARIOS (NOT FORMAL IDENTIFICATION BOUNDS)")
    print(f"Baseline: {float(bounds.iloc[rb,1]):,.1f} to {float(bounds.iloc[rb,2]):,.1f}")
    print(f"Post-shock: {float(bounds.iloc[rp,1]):,.1f} to {float(bounds.iloc[rp,2]):,.1f}")
    print()

    val = pd.read_excel(book, sheet_name="Section 8 Validation")
    keep = [
        "Route", "Annualized qty change", "Unit-value change",
        "Route unit-value change relative to market", "Validation status"
    ]
    routes = ["China", "Germany", "Canada", "Japan", "Taiwan", "Russia", "Slovakia", "All U.S. imports (market reference)"]
    out = val[val["Route"].isin(routes)][keep].copy()
    for c in ["Annualized qty change", "Unit-value change", "Route unit-value change relative to market"]:
        out[c] = out[c].map(lambda x: f"{float(x)*100:+.1f}%")
    print("SECTION 8 VALIDATION SUMMARY")
    print(out.to_string(index=False))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python reproduce_gallium_core_metrics.py TSDA_gallium_trace_master_v10.xlsx")
    main(sys.argv[1])
