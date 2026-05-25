from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout


def render_steps(container: QVBoxLayout, steps, width: int) -> str:
    """Render guide steps into a QVBoxLayout.

    Clears existing widgets, creates zone headers, step labels with
    tag-based styling, and hint sub-labels.

    Returns the last zone name rendered (needed for EXP display).
    """
    while container.count():
        child = container.takeAt(0)
        if child is not None and child.widget() is not None:
            child.widget().deleteLater()

    current_zone = ""
    for step in steps:
        if step.zone != current_zone:
            current_zone = step.zone
            zone_label = QLabel(f"{step.zone}")
            zone_label.setStyleSheet(
                "color: #888888; font-size: 10px; font-weight: bold; margin-top: 2px;"
            )
            container.addWidget(zone_label)

        step_label = QLabel(step.description)
        step_label.setWordWrap(True)
        step_label.setMinimumWidth(width - 24)
        if "optional" in step.tags:
            step_label.setStyleSheet("color: #cccccc; font-size: 11px;")
        elif "permanent_buff" in step.tags:
            step_label.setStyleSheet("color: #00ffff; font-size: 11px;")
        else:
            step_label.setStyleSheet("color: white; font-size: 11px;")
        container.addWidget(step_label)

        if step.hint:
            hint_label = QLabel(step.hint)
            hint_label.setWordWrap(True)
            hint_label.setMinimumWidth(width - 24)
            hint_label.setStyleSheet(
                "color: #888888; font-size: 10px; padding-left: 4px;"
            )
            container.addWidget(hint_label)

    return current_zone
