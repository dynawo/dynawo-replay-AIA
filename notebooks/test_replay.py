import marimo

__generated_with = "0.11.7"
app = marimo.App(width="medium")


@app.cell
def _():
    from dynawo_replay import ReplayableCase

    # case = ReplayableCase("tmp/Nordic/Nordic.jobs")
    # case = ReplayableCase("tmp/IEEE118_NodeFault/IEEE118.jobs")
    case = ReplayableCase("tmp/IEEE57_GeneratorDisconnection/IEEE57.jobs")
    # case = ReplayableCase("tmp/IEEE57_Fault/IEEE57.jobs")
    # case = ReplayableCase("tmp/TestCase2/TestCase2.jobs")
    # case = ReplayableCase("tmp/t0/fic_JOB.xml")
    return ReplayableCase, case


@app.cell(hide_code=True)
def _(case, curves_selection, element_selection, mo):
    column_names = [f"{element_selection.value.id}_{v}" for v in curves_selection.value]
    _md_list = "".join(f"\n- {c}" for c in column_names)

    mo.md(f"""
    Using case at {case.base_folder}.

    {element_selection}

    {curves_selection}

    Full list of curves to replay is:
    {_md_list}
    """)
    return (column_names,)


@app.cell
def _(case):
    case.generate_replayable_base()
    return


@app.cell
def _(case, curves_selection, element_selection):
    reference_df = case.calculate_reference_curves(element_selection.value.id, curves_selection.value)
    return (reference_df,)


@app.cell
def _(case, curves_selection, element_selection):
    replayed_df = case.replay(element_selection.value.id, curves_selection.value, keep_tmp=True)
    return (replayed_df,)


@app.cell
def _(column_names, mo):
    curve_to_plot_dropdown = mo.ui.dropdown(
        options=column_names, label="Curve to plot", value=column_names[0]
    )
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


@app.cell(hide_code=True)
def _(case, mo):
    replayable_elements = list(case.replayable_elements.values())
    _options = {f"{e.id} ({e.lib})": e for e in replayable_elements}
    _default_option = next(iter(_options))
    element_selection = mo.ui.dropdown(
        options=_options,
        label="Element to replay",
        value=_default_option,
        full_width=True,
        searchable=True,
    )
    return element_selection, replayable_elements


@app.cell(hide_code=True)
def _(element_selection, mo):
    replayable_curves = [v.name for v in element_selection.value.replayable_variables]
    curves_selection = mo.ui.multiselect(
        options=replayable_curves,
        label="Curves to replay",
        value=replayable_curves[:1],
        full_width=True,
    )
    return curves_selection, replayable_curves


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
