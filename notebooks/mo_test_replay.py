import marimo

__generated_with = "0.11.7"
app = marimo.App(width="medium")


@app.cell
def _():
    from dynawo_replay import ReplayableCase
    from dynawo_replay.plotting import plot_curves_comparison

    case = ReplayableCase("tmp/IEEE118_NodeFault/IEEE118.jobs")
    return ReplayableCase, case, plot_curves_comparison


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
    reference_df = case.calculate_reference_curves(
        element_selection.value.id, curves_selection.value
    )
    return (reference_df,)


@app.cell
def _(case, curves_selection, element_selection):
    replayed_df = case.replay(element_selection.value.id, curves_selection.value)
    return (replayed_df,)


@app.cell(hide_code=True)
def _(column_names, mo):
    curve_to_plot_dropdown = mo.ui.dropdown(
        options=column_names, label="Curve to plot", value=column_names[0]
    )
    curve_to_plot_dropdown
    return (curve_to_plot_dropdown,)


@app.cell
def _(
    curve_to_plot_dropdown,
    plot_curves_comparison,
    reference_df,
    replayed_df,
):
    plot_curves_comparison(
        reference_df, replayed_df, curve_to_plot_dropdown.value, engine="plotly"
    )
    return


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
        # value=replayable_curves[:1],
        value=[
            "generator_IRotorPu_value",
            "generator_IStatorPu_value",
            "generator_PGen",
            "generator_PGenPu",
            "generator_PePu",
            "generator_PmPu_value",
            "generator_QGen",
            "generator_QGenPu",
        ],
        full_width=True,
    )
    return curves_selection, replayable_curves


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
