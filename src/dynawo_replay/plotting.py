from typing import Literal

import pandas as pd
import plotly.graph_objects as go
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from plotly.subplots import make_subplots

from .metrics import compare_curves


def plot_curves_comparison(
    reference_df: pd.DataFrame,
    replayed_df: pd.DataFrame,
    curve_name: str,
    show_metrics: list[str] = [
        "ptp_diff",
        "ss_value_diff",
        "ss_time_diff",
    ],
    engine: Literal["matlpotlibt", "plotly"] = "matplotlib",
) -> go.Figure:
    """
    Plot comparison of curves with a table displaying metrics below the graph.

    Parameters
    ----------
    reference_df : pd.DataFrame
        Dataframe containing the original curves obtained with regular execution.
    replayed_df : pd.DataFrame
        Dataframe containing the reconstructed curves obtained with local replay.
    curve_name : str
        The name of the curve to plot and analyze.
    show_metrics : list[str]
        List of metrics to show in the table below the figure.
    engine: 'matplotlib' | 'plotly'
        Plotting engine to use.
    """
    metrics = compare_curves(
        reference_df[curve_name],
        replayed_df[curve_name],
    )
    if engine == "matplotlib":
        fig = Figure(figsize=(10, 6))
        gs = GridSpec(2, 1, height_ratios=[4, 1])
        ax1 = fig.add_subplot(gs[0])
        ax1.plot(reference_df.index, reference_df[curve_name], label="Reference")
        ax1.plot(
            replayed_df.index,
            replayed_df[curve_name],
            label="Replayed",
            linestyle="dotted",
        )
        ax1.set_title(curve_name)
        ax1.set_xlabel("Time")
        ax1.legend()
        ax2 = fig.add_subplot(gs[1])
        ax2.axis("off")
        col_labels = [m for m in show_metrics if hasattr(metrics, m)]
        cell_text = [[f"{getattr(metrics, m):.2f}" for m in col_labels]]
        table = ax2.table(
            cellText=cell_text,
            colLabels=col_labels,
            loc="center",
            cellLoc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.5)
        for key, cell in table.get_celld().items():
            if key[0] == 0:
                cell.set_facecolor("#cccccc")
                cell.set_text_props(weight="bold")
            else:
                cell.set_facecolor("#f7f7f7")
        return fig
    elif engine == "plotly":
        fig = make_subplots(
            rows=2,
            cols=1,
            row_heights=[0.8, 0.2],
            subplot_titles=(curve_name, None),
            specs=[[{"type": "xy"}], [{"type": "table"}]],
        )
        fig.add_trace(
            go.Scatter(
                x=reference_df.index,
                y=reference_df[curve_name],
                mode="lines",
                name="Reference",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=replayed_df.index,
                y=replayed_df[curve_name],
                mode="lines",
                line=dict(dash="dot"),
                name="Replayed",
            ),
            row=1,
            col=1,
        )
        fig.update_layout(xaxis_title="Time")
        fig.add_trace(
            go.Table(
                header=dict(values=show_metrics),
                cells=dict(values=[f"{getattr(metrics, m):.2f}" for m in show_metrics]),
            ),
            row=2,
            col=1,
        )
        return fig
    else:
        raise ValueError(f"Unsupported engine: {engine}")
