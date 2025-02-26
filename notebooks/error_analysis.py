import marimo

__generated_with = "0.11.7"
app = marimo.App(width="medium", app_title="Error Analysis")


@app.cell(hide_code=True)
def _():
    import altair as alt
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    import seaborn as sns
    from plotly.subplots import make_subplots

    from dynawo_replay import ReplayableCase
    from dynawo_replay.schemas.curves_input import CurveInput
    from dynawo_replay.metrics import compare_curves
    return (
        CurveInput,
        ReplayableCase,
        alt,
        compare_curves,
        go,
        make_subplots,
        mo,
        np,
        pd,
        plt,
        px,
        sns,
    )


@app.cell
def _(ReplayableCase, mo):
    # case = ReplayableCase("data/tmp/IEEE57_GeneratorDisconnection/IEEE57.jobs")
    # case = ReplayableCase("data/tmp/WSCC9_Fault/WSCC9.jobs")
    case = ReplayableCase("data/tmp/IEEE57_Fault/IEEE57.jobs")
    mo.md(f"Using case at {case.base_folder}.")
    return (case,)


@app.cell
def _(CurveInput, case, mo):
    selected_curves = [
        CurveInput(model=el.id, variable=v.name)
        for el in case.replayable_elements.values()
        for v in el.replayable_variables
    ]
    mo.md(f"Total number of curves to evaluate {len(selected_curves)}.")
    return (selected_curves,)


@app.cell
def _(mo):
    mo.md("""# Full metrics table""")
    return


@app.cell
def _(case, compare_curves, mo, pd, selected_curves):
    with mo.persistent_cache(name="error_analysis"):
        with case.replica() as _replica:
            _replica.generate_replayable_base(save=True)
            reference_df = _replica.calculate_reference_curves(selected_curves)
            replayed_df = _replica.replay(selected_curves)
        _metrics = []
        for _curve in selected_curves:
            curve_name = f"{_curve.model}_{_curve.variable}"
            _metrics.append(
                {
                    "name": curve_name,
                    "model": _curve.model,
                    "var": _curve.variable,
                    **compare_curves(
                        reference_df[curve_name], replayed_df[curve_name]
                    ).__dict__,
                }
            )
        metrics_df = pd.DataFrame(_metrics)

    metrics_df
    return curve_name, metrics_df, reference_df, replayed_df


@app.cell(hide_code=True)
def _(mo, selected_curves):
    curves_column_names = [f"{c.model}_{c.variable}" for c in selected_curves]
    curve_to_plot_dropdown = mo.ui.dropdown(
        options=curves_column_names,
        label="Select the curve you want to plot",
        value=curves_column_names[0],
        searchable=True,
    )
    curve_to_plot_dropdown
    return curve_to_plot_dropdown, curves_column_names


@app.cell
def _(curve_to_plot_dropdown, plot_curves_comparison):
    plot_curves_comparison(curve_to_plot_dropdown.value)
    return


@app.cell
def _(mo):
    mo.md(r"""# Max errors""")
    return


@app.cell
def _(metrics_df, plot_curves_comparison):
    _column = "ptp_diff_rel"
    _max_ptp_curve = metrics_df.loc[metrics_df[_column].idxmax(), "name"]
    _fig = plot_curves_comparison(_max_ptp_curve)
    _fig.update_layout(title_text=f"Maximum {_column}")
    _fig
    return


@app.cell
def _(metrics_df, plot_curves_comparison):
    _column = "ss_value_diff_rel"
    _max_ptp_curve = metrics_df.loc[metrics_df[_column].idxmax(), "name"]
    _fig = plot_curves_comparison(_max_ptp_curve)
    _fig.update_layout(title_text=f"Maximum {_column}")
    _fig
    return


@app.cell
def _(metrics_df, plot_curves_comparison):
    _column = "ss_time_diff"
    _max_ptp_curve = metrics_df.loc[metrics_df[_column].idxmax(), "name"]
    _fig = plot_curves_comparison(_max_ptp_curve)
    _fig.update_layout(title_text=f"Maximum {_column}")
    _fig
    return


@app.cell
def _(mo):
    mo.md(r"""# Other things""")
    return


@app.cell
def _(metrics_df):
    _feats = [
        "ptp_diff",
        "ss_value_diff",
        "ss_time_diff",
        "ptp_diff_rel",
        "ss_value_diff_rel",
        # 'r2', 'rmse', 'nrmse', 'mae',
    ]
    _df = metrics_df.groupby("model")[_feats].mean()
    _df
    return


@app.cell(hide_code=True)
def _(compare_curves, go, make_subplots, reference_df, replayed_df):
    def plot_curves_comparison(
        curve_name: str,
        show_metrics: list[str] = [
            "ptp_diff",
            "ss_value_diff",
            "ss_time_diff",
            "ptp_diff_rel",
            "ss_value_diff_rel",
        ],
    ) -> go.Figure:
        """
        Plot comparison of curves with a table displaying metrics below the graph.

        Parameters
        ----------
        curve_name : str
            The name of the curve to plot and analyze.

        Returns
        -------
        go.Figure
            The plotly figure object with line plots and a metrics table.
        """
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
                line=dict(dash="dash"),
                name="Replayed",
            ),
            row=1,
            col=1,
        )
        fig.update_layout(xaxis_title="Time")
        metrics = compare_curves(
            reference_df[curve_name],
            replayed_df[curve_name],
        )
        fig.add_trace(
            go.Table(
                header=dict(values=show_metrics),
                cells=dict(values=[f"{getattr(metrics, m):.2f}" for m in show_metrics]),
            ),
            row=2,
            col=1,
        )
        return fig
    return (plot_curves_comparison,)


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
