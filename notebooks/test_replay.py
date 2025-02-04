import marimo

__generated_with = "0.10.17"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    from dynawo_replay.simulation import Case

    # case = Simulation("data/tmp/IEEE14/IEEE14.jobs")
    case = Case("data/tmp/IEEE57_Fault/IEEE57.jobs")
    mo.md(f"Using case at {case.base_folder}.")
    return Case, case


@app.cell(hide_code=True)
def _(case, mo):
    from dynawo_replay.utils import list_available_vars

    curves_options = []
    generators = case.get_terminal_nodes()
    for _gen in generators:
        dyd_bbm = next(bbm for bbm in case.dyd.black_box_model if bbm.id == _gen)
        for var in list_available_vars(dyd_bbm.lib, dynawo=case.dynawo_home):
            curves_options.append(f"{_gen}::{var.name}")

    curves_selection = mo.ui.multiselect(
        options=curves_options, full_width=True, value=curves_options[:1]
    )
    return curves_options, curves_selection, dyd_bbm, generators, var


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
    with case.replica() as _dup:
        _dup.generate_replayable_base(save=True)
        _curves = selected_curves
        _dup.crv.curve = _curves
        _dup.save()
        _dup.run()
        original_df = _dup.read_output_curves()
        replayed_df = _dup.replay(_curves, keep_tmp=True)
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

    s1 = original_df[curve_to_plot_dropdown.value]
    s2 = replayed_df[curve_to_plot_dropdown.value]
    compare_curves(s1, s2)
    return compare_curves, s1, s2


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
