import os
import webbrowser


class PrintManager:
    @staticmethod
    def open_in_browser(path: str) -> None:
        if not path or not os.path.exists(path):
            return
        url = 'file://' + os.path.abspath(path)
        webbrowser.open(url)