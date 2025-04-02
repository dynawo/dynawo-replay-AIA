import marimo

__generated_with = "0.11.7"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    from pathlib import Path
    from dynawo_replay import ReplayableCase

    # case = ReplayableCase("tmp/Nordic/Nordic.jobs")
    # case = ReplayableCase("tmp/IEEE118_NodeFault/IEEE118.jobs")
    # case = ReplayableCase("tmp/IEEE57_GeneratorDisconnection/IEEE57.jobs")
    case = ReplayableCase("tmp/IEEE57_Fault/IEEE57.jobs")
    # case = ReplayableCase("tmp/TestCase2/TestCase2.jobs")
    # case = ReplayableCase("tmp/t0/fic_JOB.xml")
    mo.md(f"Using case at {case.base_folder}.")
    return Path, ReplayableCase, case


@app.cell
def _(case, mo):
    curves_options = [
        f"{el.id}::{v.name}"
        for el in case.replayable_elements.values()
        for v in el.replayable_variables
    ]
    curves_selection = mo.ui.multiselect(
        options=curves_options, full_width=True, value=curves_options[:1]
    )
    return curves_options, curves_selection


@app.cell
def _(curves_selection, mo):
    from dynawo_replay.schemas.curves_input import CurveInput

    _curves_md = ""
    curves_column_names = []
    selected_curves = []
    for _curve in curves_selection.value:
        model, variable = _curve.split("::")
        selected_curves.append(CurveInput(model=model, variable=variable))
        curves_column_names.append(_curve.replace("::", "_"))
        _curves_md += f"\n\n- {_curve}"

    mo.md(f"""
    Select the curves to test the replay:
    {curves_selection}

    Selection: {_curves_md}
    """)
    return CurveInput, curves_column_names, model, selected_curves, variable


@app.cell
def _(case):
    case.generate_replayable_base()
    return


@app.cell
def _(case, selected_curves):
    reference_df = case.calculate_reference_curves(selected_curves)
    return (reference_df,)


@app.cell
def _(case, selected_curves):
    replayed_df = case.replay(selected_curves, keep_tmp=True)
    return (replayed_df,)


@app.cell(hide_code=True)
def _(curves_column_names, mo):
    curve_to_plot_dropdown = mo.ui.dropdown(
        options=curves_column_names, label="Curve to plot", value=curves_column_names[0]
    )
    curve_to_plot_dropdown
    return (curve_to_plot_dropdown,)


@app.cell
def _(curve_to_plot_dropdown, plot_curves_comparison):
    plot_curves_comparison(curve_to_plot_dropdown.value)
    return


@app.cell(hide_code=True)
def _(reference_df, replayed_df):
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from dynawo_replay.metrics import compare_curves


    def plot_curves_comparison(
        curve_name: str,
        show_metrics: list[str] = [
            "ptp_ref",
            "ptp_rep",
            "ptp_diff",
            "ss_value_ref",
            "ss_value_rep",
            "ss_value_diff",
            "ss_time_ref",
            "ss_time_rep",
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
                line=dict(dash="dot"),
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
    return compare_curves, go, make_subplots, plot_curves_comparison, px


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
