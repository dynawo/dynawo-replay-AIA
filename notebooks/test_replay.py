import marimo

__generated_with = "0.11.7"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    from dynawo_replay import ReplayableCase

    # case = ReplayableCase("data/tmp/Nordic/Nordic.jobs")
    # case = ReplayableCase("data/tmp/IEEE118_NodeFault/IEEE118.jobs")
    case = ReplayableCase("data/tmp/IEEE57_GeneratorDisconnection/IEEE57.jobs")
    # case = ReplayableCase("data/tmp/TestCase2/TestCase2.jobs")
    mo.md(f"Using case at {case.base_folder}.")
    return ReplayableCase, case


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
def _(case, selected_curves):
    case.generate_replayable_base()
    original_df = case.calculate_reference_curves(selected_curves)
    replayed_df = case.replay(selected_curves, keep_tmp=True)
    return original_df, replayed_df


@app.cell
def _(curves_column_names, mo):
    curve_to_plot_dropdown = mo.ui.dropdown(
        options=curves_column_names, label="Curve to plot", value=curves_column_names[0]
    )
    curve_to_plot_dropdown
    return (curve_to_plot_dropdown,)


@app.cell
def _(curve_to_plot_dropdown, original_df, replayed_df):
    from matplotlib import pyplot as plt

    if curve_to_plot_dropdown.value:
        plot = original_df[curve_to_plot_dropdown.value].plot(label="original")
        plot = replayed_df[curve_to_plot_dropdown.value].plot(
            label="replayed", linestyle="--"
        )
        plt.legend()
    else:
        plot = "Choose a curve to plot in the dropdown above"

    plot
    return plot, plt


@app.cell
def _(curve_to_plot_dropdown, mo, original_df, replayed_df):
    from dynawo_replay.metrics import compare_curves

    metrics = compare_curves(
        original_df[curve_to_plot_dropdown.value],
        replayed_df[curve_to_plot_dropdown.value],
    )
    mo.ui.table(data=[metrics.__dict__])
    return compare_curves, metrics


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
