import marimo

__generated_with = "0.10.17"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    from dynawo_replay import ReplayableCase

    # case = ReplayableCase("data/tmp/IEEE14/IEEE14.jobs")
    # case = ReplayableCase("data/tmp/IEEE57_Fault/IEEE57.jobs")
    case = ReplayableCase("data/tmp/TestCase2/TestCase2.jobs")
    mo.md(f"Using case at {case.base_folder}.")
    return ReplayableCase, case


@app.cell(hide_code=True)
def _(case, mo):
    curves_options = [
        f"{el.id}::{v.name}" for el in case.replayable_elements.values() for v in el.replayable_variables
    ]
    curves_selection = mo.ui.multiselect(
        options=curves_options, full_width=True, value=curves_options[:1]
    )
    return curves_options, curves_selection


@app.cell(hide_code=True)
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
    with case.replica() as _replica:
        _replica.generate_replayable_base(save=True)
        original_df = _replica.calculate_reference_curves(selected_curves)
        replayed_df = _replica.replay(selected_curves)
    return original_df, replayed_df


@app.cell(hide_code=True)
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
def _(curve_to_plot_dropdown, original_df, replayed_df):
    from dynawo_replay.metrics import compare_curves

    compare_curves(
        original_df[curve_to_plot_dropdown.value],
        replayed_df[curve_to_plot_dropdown.value],
    )
    return (compare_curves,)


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
