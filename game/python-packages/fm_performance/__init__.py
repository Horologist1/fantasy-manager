"""Performance helpers shared by Ren'Py runtime and Python tests."""

from .reporting import copy_report_without_worker, report_page_window

__all__ = ["copy_report_without_worker", "report_page_window"]
