"""§8 matched control-alarm-budget operating points.

Detector fires on high score; ties broken by ASCENDING userId (§8). At budget b,
matched control-alarm count = round(b · n_eval_controls); event TPR is read at the
threshold admitting exactly that many control alarms.
"""
from __future__ import annotations
import numpy as np


def matched_count(budget: float, n_controls: int) -> int:
    """§8: count = round(b · n_controls)."""
    return int(round(budget * n_controls))


def matched_tpr(score: np.ndarray, is_event: np.ndarray, user_id: np.ndarray, count: int) -> float:
    """Event TPR at the operating point admitting exactly `count` control alarms.

    Total order = (score desc, userId asc). Alarm set = units ranked at/above the
    `count`-th control. TPR = events_alarmed / total_events.
    """
    score = np.asarray(score, float); is_event = np.asarray(is_event, bool)
    user_id = np.asarray(user_id)
    total_events = int(is_event.sum())
    if total_events == 0:
        return float("nan")
    order = np.lexsort((user_id, -score))          # primary: -score; tie: userId asc
    is_ctrl_ordered = ~is_event[order]
    ctrl_positions = np.flatnonzero(is_ctrl_ordered)
    if count <= 0:
        cutoff = ctrl_positions[0] if ctrl_positions.size else len(order)  # units above 1st control
        alarmed = order[:cutoff]
    else:
        if count > ctrl_positions.size:
            count = ctrl_positions.size
        pos = ctrl_positions[count - 1]            # index of the count-th control (inclusive)
        alarmed = order[: pos + 1]
    events_alarmed = int(is_event[alarmed].sum())
    return events_alarmed / total_events
