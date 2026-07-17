import subprocess
import sys
import tempfile

import polars as pl
import pytest

from tests.helpers import assert_snapshot
from tytable import tt
from tytable._directives import ImageDirective, PlotDirective
from tytable._images import _callback_kwargs
from tytable._resolve import build


def test_non_image_render_does_not_import_matplotlib():
    code = """
import sys
import polars as pl
from tytable import tt

tt(pl.DataFrame({"A": [1]})).theme_empty().render("html")
assert "matplotlib" not in sys.modules
"""
    subprocess.run([sys.executable, "-c", code], check=True)


def test_plot_and_image_calls_record_distinct_directive_types():
    table = (
        tt(pl.DataFrame({"Value": [[1, 2, 3]]}))
        .theme_empty()
        .images(j="Value", paths=["image.png"])
        .plot(j="Value", fun=_sparkline)
    )

    assert len(table._plot_directives) == 1
    assert isinstance(table._plot_directives[0], PlotDirective)
    assert not hasattr(table._plot_directives[0], "images")
    assert len(table._image_directives) == 1
    assert isinstance(table._image_directives[0], ImageDirective)
    assert not hasattr(table._image_directives[0], "fun")
    assert table._media_directives == [table._image_directives[0], table._plot_directives[0]]


def test_existing_images_do_not_require_plotting_dependencies(monkeypatch):
    def _unexpected_require():
        raise AssertionError("static images must not load plotting dependencies")

    monkeypatch.setattr("tytable._images._require_plotting", _unexpected_require)
    df = pl.DataFrame({"Logo": ["placeholder"]})

    result = tt(df).theme_empty().images(j="Logo", paths=["img/a.png"]).render("typst")

    assert '#image("img/a.png", height: 1em)' in result


def _sparkline(values, *, color="black", xlim=None, **kw):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 2), dpi=100)
    ax.plot(range(len(values)), values, color=color, lw=2)
    ax.set_axis_off()
    return fig


class TestPlotCallbackKeywords:
    def test_forwards_color_without_xlim(self):
        def color_only(value, *, color):
            return value, color

        assert _callback_kwargs(color_only, color="red", xlim=[0, 1]) == {"color": "red"}

    def test_forwards_xlim_without_color(self):
        def xlim_only(value, *, xlim):
            return value, xlim

        assert _callback_kwargs(xlim_only, color="red", xlim=[0, 1]) == {"xlim": [0, 1]}

    def test_forwards_both_to_var_kwargs(self):
        def variadic(value, **kwargs):
            return value, kwargs

        assert _callback_kwargs(variadic, color="red", xlim=[0, 1]) == {
            "color": "red",
            "xlim": [0, 1],
        }

    def test_forwards_neither_to_plain_callback(self):
        assert _callback_kwargs(lambda value: value, color="red", xlim=[0, 1]) == {}

    def test_does_not_forward_positional_only_parameter(self):
        def positional_only(value, color, /):
            return value, color

        assert _callback_kwargs(positional_only, color="red", xlim=[0, 1]) == {}


@pytest.mark.images
class TestPlotSparkline:
    def test_matplotlib_uses_requested_pixel_dimensions(self, tmp_path):
        df = pl.DataFrame({"Trend": [[1, 2, 3]]})
        tt(df).theme_empty().plot(j="Trend", fun=_sparkline, width_px=320, height_px=96).save(
            str(tmp_path / "out.typ")
        )

        import matplotlib.image as mpimg

        image = mpimg.imread(tmp_path / "tytable_assets" / "plot_0000_testid0001.png")
        assert image.shape[:2] == (96, 320)

    def test_sparkline_list_column(self, tmp_path):
        df = pl.DataFrame({"Trend": [[1, 2, 3], [4, 1, 2]]})
        tt(df).theme_empty().plot(j="Trend", fun=_sparkline).save(str(tmp_path / "out.typ"))
        result = (tmp_path / "out.typ").read_text()
        assert '#image("tytable_assets/plot_0000_testid0001.png", height: 1em)' in result
        assert (tmp_path / "tytable_assets" / "plot_0000_testid0001.png").exists()

    def test_sparkline_explicit_data(self, tmp_path):
        df = pl.DataFrame({"X": [1, 2]})
        tt(df).theme_empty().plot(j="X", fun=_sparkline, data=[[1, 2, 3], [4, 1, 2]]).save(
            str(tmp_path / "out.typ")
        )
        result = (tmp_path / "out.typ").read_text()
        assert '#image("tytable_assets/plot_0000_testid0001.png", height: 1em)' in result

    def test_sparkline_snapshot(self, tmp_path):
        df = pl.DataFrame({"Trend": [[1, 2, 3], [4, 1, 2]]})
        tt(df).theme_empty().plot(j="Trend", fun=_sparkline).save(str(tmp_path / "out.typ"))
        result = (tmp_path / "out.typ").read_text()
        assert_snapshot("images_sparkline", result)

    def test_sparkline_height_str(self, tmp_path):
        df = pl.DataFrame({"Trend": [[1, 2, 3], [4, 1, 2]]})
        tt(df).theme_empty().plot(j="Trend", fun=_sparkline, height="1.5em").save(
            str(tmp_path / "out.typ")
        )
        result = (tmp_path / "out.typ").read_text()
        assert "height: 1.5em" in result

    def test_sparkline_custom_assets(self, tmp_path):
        df = pl.DataFrame({"Trend": [[1, 2, 3]]})
        tt(df).theme_empty().plot(j="Trend", fun=_sparkline).save(
            str(tmp_path / "sub/out.typ"), assets="../assets/myplots"
        )
        result = (tmp_path / "sub" / "out.typ").read_text()
        assert '#image("../assets/myplots/plot_0000_testid0001.png", height: 1em)' in result
        assert (tmp_path / "assets" / "myplots" / "plot_0000_testid0001.png").exists()

    def test_sparkline_render_default_assets(self):
        df = pl.DataFrame({"Trend": [[1, 2, 3]]})
        result = tt(df).theme_empty().plot(j="Trend", fun=_sparkline).render("typst")
        assert '#image("tytable_assets/plot_0000_testid0001.png", height: 1em)' in result


@pytest.mark.images
class TestImages:
    def test_images_existing_files(self, tmp_path):
        df = pl.DataFrame({"Logo": ["a.png", "b.png"]})
        tt(df).theme_empty().images(j="Logo", paths=["img/a.png", "img/b.png"]).save(
            str(tmp_path / "out.typ")
        )
        result = (tmp_path / "out.typ").read_text()
        assert '#image("img/a.png", height: 1em)' in result
        assert '#image("img/b.png", height: 1em)' in result

    def test_image_paths_are_escaped_for_markup(self):
        df = pl.DataFrame({"Logo": ["placeholder"]})

        html = tt(df).theme_empty().images(j="Logo", paths=['x" onerror="alert(1)']).render("html")
        assert '<img src="x&amp;quot; onerror=&amp;quot;alert(1)"' not in html
        assert '<img src="x&quot; onerror=&quot;alert(1)"' in html

        typst = (
            tt(df)
            .theme_empty()
            .images(j="Logo", paths=['x"), pagebreak(), image("'])
            .render("typst")
        )
        assert '#image("x\\"), pagebreak(), image(\\"", height: 1em)' in typst


@pytest.mark.images
class TestPlotnine:
    def test_plotnine_ggplot_duck(self, tmp_path):
        pytest.importorskip("plotnine")

        import plotnine as p9

        df = pl.DataFrame({"Trend": [[1, 2, 3], [4, 1, 2]]})

        def p9_sparkline(values, *, color="black", xlim=None):
            import pandas as pd

            data = pd.DataFrame({"x": range(len(values)), "y": values})
            return p9.ggplot(data, p9.aes("x", "y")) + p9.geom_line(color=color)

        tt(df).theme_empty().plot(j="Trend", fun=p9_sparkline, height_px=96, width_px=320).save(
            str(tmp_path / "out.typ")
        )
        result = (tmp_path / "out.typ").read_text()
        assert '#image("tytable_assets/plot_0000_testid0001.png", height: 1em)' in result

        import matplotlib.image as mpimg

        image = mpimg.imread(tmp_path / "tytable_assets" / "plot_0000_testid0001.png")
        assert image.shape[:2] == (96, 320)


@pytest.mark.images
class TestPortable:
    def test_portable_mode_inline_svg(self):
        df = pl.DataFrame({"Trend": [[1, 2, 3]]})
        result = tt(df).theme_empty().plot(j="Trend", fun=_sparkline).render("typst")
        assert '#image("tytable_assets/plot_0000_testid0001.png"' in result

    def test_portable_theme_typst_inline_svg(self):
        from tytable._themes import theme_typst

        df = pl.DataFrame({"Trend": [[1, 2, 3]]})
        result = (
            tt(df)
            .theme_empty()
            .plot(j="Trend", fun=_sparkline)
            .theme(lambda t: theme_typst(t, portable=True))
            .render("typst")
        )
        assert "#image(bytes(" in result
        assert 'format: "svg"' in result

    def test_portable_wrapper_uses_requested_pixel_dimensions(self):
        from tytable._themes import theme_typst

        df = pl.DataFrame({"Trend": [[1, 2, 3]]})
        result = (
            tt(df)
            .theme_empty()
            .plot(j="Trend", fun=_sparkline, width_px=320, height_px=96)
            .theme(lambda t: theme_typst(t, portable=True))
            .render("typst")
        )

        assert "width='320' height='96'" in result
        assert "viewBox='0 0 320 96'" in result

    def test_temp_dir_cleaned_up_when_plot_fails(self, tmp_path, monkeypatch):
        from tytable._themes import theme_typst

        monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))

        def fail(_value):
            raise RuntimeError("plot failed")

        table = (
            tt(pl.DataFrame({"Trend": [[1, 2, 3]]}))
            .theme_empty()
            .plot(j="Trend", fun=fail)
            .theme(lambda t: theme_typst(t, portable=True))
        )

        with pytest.raises(RuntimeError, match="plot failed"):
            table.render("typst")

        assert list(tmp_path.iterdir()) == []


@pytest.mark.images
class TestValidation:
    def test_missing_j(self):
        df = pl.DataFrame({"X": [1]})
        with pytest.raises(ValueError, match="requires j"):
            tt(df).plot(fun=lambda x: x)

    def test_missing_fun(self):
        df = pl.DataFrame({"X": [1]})
        with pytest.raises(ValueError, match="requires fun"):
            tt(df).plot(j="X")

    @pytest.mark.parametrize("name", ["width_px", "height_px"])
    @pytest.mark.parametrize("value", [0, -1])
    def test_plot_pixel_dimensions_must_be_positive(self, name, value):
        df = pl.DataFrame({"X": [[1, 2, 3]]})
        with pytest.raises(ValueError, match=rf"{name} must be positive"):
            tt(df).plot(j="X", fun=_sparkline, **{name: value})

    @pytest.mark.parametrize("name", ["width_px", "height_px"])
    @pytest.mark.parametrize("value", [True, 1.5, "100"])
    def test_plot_pixel_dimensions_must_be_integers(self, name, value):
        df = pl.DataFrame({"X": [[1, 2, 3]]})
        with pytest.raises(TypeError, match=rf"{name} must be an integer"):
            tt(df).plot(j="X", fun=_sparkline, **{name: value})

    def test_missing_images_paths(self):
        df = pl.DataFrame({"X": [1]})
        with pytest.raises(ValueError, match="requires paths"):
            tt(df).images(j="X")

    def test_missing_extra_hint(self, monkeypatch):
        def _fake_require():
            raise ImportError(
                ".plot() requires the 'images' extra:\n    pip install tytable[images]"
            )

        monkeypatch.setattr("tytable._images._require_plotting", _fake_require)
        df = pl.DataFrame({"Trend": [[1, 2, 3]]})
        with pytest.raises(ImportError, match="images.*extra"):
            build(tt(df).theme_empty().plot(j="Trend", fun=_sparkline), "typst")

    def test_invalid_callback_return_includes_directive_and_cell(self, tmp_path):
        table = tt(pl.DataFrame({"Trend": [[1, 2, 3]]})).plot(
            j="Trend", fun=lambda _value: "not a plot"
        )

        with pytest.raises(
            TypeError,
            match=r"directive 1, selected cell \(row=0, column=0\).*got str",
        ):
            table.save(str(tmp_path / "out.typ"))


class TestMediaCardinality:
    DF = pl.DataFrame({"A": [1, 2], "B": [3, 4]})

    def test_images_assign_multiple_rows_and_columns_row_major(self):
        built = build(
            tt(self.DF).theme_empty().images(j=["A", "B"], paths=["a", "b", "c", "d"]),
            "typst",
        )

        assert 'image("a"' in built.data_body[0][0]
        assert 'image("b"' in built.data_body[0][1]
        assert 'image("c"' in built.data_body[1][0]
        assert 'image("d"' in built.data_body[1][1]

    @pytest.mark.parametrize("paths", [["a", "b", "c"], ["a", "b", "c", "d", "e"]])
    def test_images_reject_wrong_cardinality(self, paths):
        with pytest.raises(ValueError, match=rf"paths has {len(paths)} item.*contains 4 cell"):
            build(tt(self.DF).images(j=["A", "B"], paths=paths), "typst")

    def test_images_accept_empty_input_for_empty_selection(self):
        built = build(tt(self.DF).images(i=[], j=["A", "B"], paths=[]), "typst")

        assert built.data_body == [["1", "3"], ["2", "4"]]

    def test_images_reject_input_for_empty_selection(self):
        with pytest.raises(ValueError, match="paths has 1 item.*contains 0 cell"):
            build(tt(self.DF).images(i=[], j="A", paths=["a"]), "typst")

    @pytest.mark.parametrize("data", [[1, 2, 3], [1, 2, 3, 4, 5]])
    def test_plot_rejects_wrong_data_cardinality_before_loading_dependencies(self, data):
        with pytest.raises(ValueError, match=rf"data has {len(data)} item.*contains 4 cell"):
            build(tt(self.DF).plot(j=["A", "B"], fun=lambda value: value, data=data), "typst")
