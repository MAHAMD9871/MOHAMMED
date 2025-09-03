from __future__ import annotations

import webbrowser


class PrintManager:
    @staticmethod
    def open_in_browser(path: str) -> None:
        webbrowser.open_new_tab(f"file://{path}")

