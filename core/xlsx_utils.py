"""Small openpyxl layout helpers shared by tabs that write a whole-script report (labelled
Overview sheet, a findings/stages table, a plain list). Factored out once two tabs
(Plot Hole Editor, Hero's Journey Editor) needed the identical patterns Readability
Editor already had, rather than copy-pasting a third private implementation.
"""
from typing import Iterable, Tuple, Dict


def write_labelled_block(ws, rows: Iterable[Tuple[str, str]]) -> None:
    """Write (label, value) pairs as two columns, one pair per row."""
    for label, value in rows:
        ws.append([label, value])


def write_list(ws, header: str, items: Iterable[str]) -> None:
    """Write a header row followed by one item per row in column A."""
    ws.append([header])
    for item in items:
        ws.append([item])


def set_column_widths(ws, widths: Dict[str, int]) -> None:
    for col, width in widths.items():
        ws.column_dimensions[col].width = width


def enable_autofilter(ws) -> None:
    """Turn on Excel's column filter/sort controls for a table sheet -- useful for reports
    meant to be triaged offline (e.g. filtering findings down to just "Definite plot hole")."""
    if ws.dimensions and ws.dimensions != "A1:A1":
        ws.auto_filter.ref = ws.dimensions
