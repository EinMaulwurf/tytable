import polars as pl
import pytest

from tests.helpers import assert_snapshot
from tinytables import tt
from tinytables._resolve import build


def _sparkline(values, *, color="black", xlim=None, **kw):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 2), dpi=100)
    ax.plot(range(len(values)), values, color=color, lw=2)
    ax.set_axis_off()
    return fig


@pytest.mark.images
class TestPlotSparkline:
    def test_sparkline_list_column(self, tmp_path):
        df = pl.DataFrame({"Trend": [[1, 2, 3], [4, 1, 2]]})
        tt(df, theme=None).plot(j="Trend", fun=_sparkline).save(str(tmp_path / "out.typ"))
        result = (tmp_path / "out.typ").read_text()
        assert '#image("tinytable_assets/plot_0000_testid0001.png", height: 1em)' in result
        assert (tmp_path / "tinytable_assets" / "plot_0000_testid0001.png").exists()

    def test_sparkline_explicit_data(self, tmp_path):
        df = pl.DataFrame({"X": [1, 2]})
        tt(df, theme=None).plot(j="X", fun=_sparkline, data=[[1, 2, 3], [4, 1, 2]]).save(
            str(tmp_path / "out.typ")
        )
        result = (tmp_path / "out.typ").read_text()
        assert '#image("tinytable_assets/plot_0000_testid0001.png", height: 1em)' in result

    def test_sparkline_snapshot(self, tmp_path):
        df = pl.DataFrame({"Trend": [[1, 2, 3], [4, 1, 2]]})
        tt(df, theme=None).plot(j="Trend", fun=_sparkline).save(str(tmp_path / "out.typ"))
        result = (tmp_path / "out.typ").read_text()
        assert_snapshot("images_sparkline", result)

    def test_sparkline_height_str(self, tmp_path):
        df = pl.DataFrame({"Trend": [[1, 2, 3], [4, 1, 2]]})
        tt(df, theme=None).plot(j="Trend", fun=_sparkline, height="1.5em").save(
            str(tmp_path / "out.typ")
        )
        result = (tmp_path / "out.typ").read_text()
        assert "height: 1.5em" in result

    def test_sparkline_custom_assets(self, tmp_path):
        df = pl.DataFrame({"Trend": [[1, 2, 3]]})
        tt(df, theme=None).plot(j="Trend", fun=_sparkline).save(
            str(tmp_path / "sub/out.typ"), assets="../assets/myplots"
        )
        result = (tmp_path / "sub" / "out.typ").read_text()
        assert '#image("../assets/myplots/plot_0000_testid0001.png", height: 1em)' in result
        assert (tmp_path / "assets" / "myplots" / "plot_0000_testid0001.png").exists()

    def test_sparkline_render_default_assets(self):
        df = pl.DataFrame({"Trend": [[1, 2, 3]]})
        result = tt(df, theme=None).plot(j="Trend", fun=_sparkline).render("typst")
        assert '#image("tinytable_assets/plot_0000_testid0001.png", height: 1em)' in result


@pytest.mark.images
class TestImages:
    def test_images_existing_files(self, tmp_path):
        df = pl.DataFrame({"Logo": ["a.png", "b.png"]})
        tt(df, theme=None).images(j="Logo", paths=["img/a.png", "img/b.png"]).save(
            str(tmp_path / "out.typ")
        )
        result = (tmp_path / "out.typ").read_text()
        assert '#image("img/a.png", height: 1em)' in result
        assert '#image("img/b.png", height: 1em)' in result


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

        tt(df, theme=None).plot(j="Trend", fun=p9_sparkline, height_px=400, width_px=1200).save(
            str(tmp_path / "out.typ")
        )
        result = (tmp_path / "out.typ").read_text()
        assert '#image("tinytable_assets/plot_0000_testid0001.png", height: 1em)' in result
        assert (tmp_path / "tinytable_assets" / "plot_0000_testid0001.png").exists()


@pytest.mark.images
class TestPortable:
    def test_portable_mode_inline_svg(self):
        df = pl.DataFrame({"Trend": [[1, 2, 3]]})
        result = tt(df, theme=None).plot(j="Trend", fun=_sparkline).render("typst")
        assert '#image("tinytable_assets/plot_0000_testid0001.png"' in result

    def test_portable_theme_typst_inline_svg(self):
        from tinytables._themes import theme_typst

        df = pl.DataFrame({"Trend": [[1, 2, 3]]})
        result = (
            tt(df, theme=None)
            .plot(j="Trend", fun=_sparkline)
            .theme(lambda t: theme_typst(t, portable=True))
            .render("typst")
        )
        assert "#image(bytes(" in result
        assert 'format: "svg"' in result


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

    def test_missing_images_paths(self):
        df = pl.DataFrame({"X": [1]})
        with pytest.raises(ValueError, match="requires paths"):
            tt(df).images(j="X")

    def test_missing_extra_hint(self, monkeypatch):
        def _fake_require():
            raise ImportError(
                ".plot()/.images() require the 'images' extra:\n    pip install tinytables[images]"
            )

        monkeypatch.setattr("tinytables._images._require_images", _fake_require)
        df = pl.DataFrame({"Trend": [[1, 2, 3]]})
        with pytest.raises(ImportError, match="images.*extra"):
            build(tt(df, theme=None).plot(j="Trend", fun=_sparkline), "typst")
