"""A transient overlay label for visual feedback when cycling through regexes.

Shows the active regex name briefly (1.5 seconds) then auto-hides,
matching the overlay's dark theme.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QWidget


class RegexWidget(QLabel):
    """A QLabel that briefly displays the active regex name when cycling.

    Styled to match the overlay's dark theme: white text on a
    semi-transparent black background, centered alignment.

    Usage:
        widget = RegexWidget(parent_overlay)
        widget.show_regex(entry)   # entry is a RegexEntry or None
    """

    DISPLAY_DURATION_MS: int = 1500

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setVisible(False)
        self.setStyleSheet("""
            RegexWidget {
                color: white;
                background-color: rgba(0, 0, 0, 180);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 4px;
                font-size: 12px;
                font-family: 'Segoe UI', 'Ubuntu', sans-serif;
                padding: 4px 12px;
            }
        """)

    def show_regex(self, entry: object | None) -> None:
        """Display a regex entry's name briefly, then auto-hide.

        If *entry* is ``None``, the widget is hidden immediately.

        Args:
            entry: A ``RegexEntry`` instance (or any object with a ``name``
                attribute), or ``None`` to hide.
        """
        if entry is None:
            self.hide()
            return

        name: str = getattr(entry, "name", str(entry))
        self.setText(f"\U0001F4CB {name}")
        self.show()
        QTimer.singleShot(self.DISPLAY_DURATION_MS, self.hide)
