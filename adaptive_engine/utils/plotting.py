from __future__ import annotations

import io
from typing import List, Tuple, Optional

import numpy as np

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    matplotlib = None  # type: ignore
    plt = None  # type: ignore


def theta_se_curve(
    theta_values: List[float], se_values: List[float], title: Optional[str] = None
) -> bytes:
    """Render a theta–SE curve to PNG bytes.

    Returns PNG image bytes suitable for embedding in reports.
    """
    if matplotlib is None or plt is None:
        raise RuntimeError("matplotlib is not available")
    if len(theta_values) != len(se_values):
        raise ValueError("theta_values and se_values must have the same length")
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(theta_values, se_values, marker="o", linewidth=2)
    ax.set_xlabel("Ability (theta)")
    ax.set_ylabel("Standard Error (SE)")
    if title:
        ax.set_title(title)
    ax.grid(True, linestyle=":", alpha=0.6)
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    return buf.getvalue()
