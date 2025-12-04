"""
Comprehensive (but fast) Matplotlib smoke-test suite.

- Uses the non-interactive 'Agg' backend so it runs headless.
- Exercises a wide cross-section of pyplot / Axes APIs:
  figures, subplots, subplot_mosaic, 2D/3D/polar plots, images,
  colormaps & normalizations, colorbars, ticks/locators/formatters,
  dates & categorical data, annotations/text/mathtext, legends,
  scales (log/linear), twin/secondary axes, transforms, patches,
  collections, masked arrays, errorbar/fill_between, rc/Style context,
  saving/drawing, constrained layout fallback, etc.

This suite mostly asserts that calls succeed and generate valid artists /
buffers, and checks a few key properties (shapes, counts, basic types).
"""

import io
import math
import unittest
import warnings

import numpy as np

# Use a headless backend BEFORE importing pyplot.
import matplotlib
matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
from matplotlib import colors, cm, dates, ticker
from matplotlib.colors import LogNorm, Normalize
from matplotlib.patches import Rectangle, Circle
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (ensures 3d projection registered)

try:
    from matplotlib import MatplotlibDeprecationWarning
except Exception:  # pragma: no cover
    class MatplotlibDeprecationWarning(Warning):  # fallback for very old versions
        pass


# ----------------------------
# Helpers & base test class
# ----------------------------
def _subplots_constrained(*args, **kwargs):
    """Try to create subplots with layout='constrained', fall back cleanly."""
    try:
        if "layout" not in kwargs:
            kwargs["layout"] = "constrained"
        return plt.subplots(*args, **kwargs)
    except TypeError:
        # Older Matplotlib versions may not support layout kwarg
        kwargs.pop("layout", None)
        fig, ax = plt.subplots(*args, **kwargs)
        try:
            fig.tight_layout()
        except Exception:
            pass
        return fig, ax


class MPLTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        np.random.seed(19680801)

    def draw_and_close(self, fig):
        """Render figure to a PNG buffer to ensure it fully draws, then close."""
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        self.assertGreater(buf.tell(), 0, "Rendered PNG buffer is empty")
        plt.close(fig)

    def assertIsType(self, obj, typ):
        self.assertIsInstance(obj, typ, f"Expected {typ}, got {type(obj)}")


# ----------------------------
# Tests
# ----------------------------
class TestFigureAndAxesCreation(MPLTestCase):
    def test_basic_figure_and_axes(self):
        fig, ax = plt.subplots()
        self.assertEqual(len(fig.axes), 1)
        # Simple, version-agnostic type check
        self.assertIsType(ax, plt.Axes)
        ax.plot([1, 2, 3], [1, 4, 9])
        self.draw_and_close(fig)

    def test_multiple_axes_and_mosaic(self):
        fig, axs = plt.subplots(2, 2)
        self.assertEqual(len(fig.axes), 4)
        self.draw_and_close(fig)

        fig2, axd = plt.subplot_mosaic([['left', 'right_top'],
                                        ['left', 'right_bottom']])
        self.assertIn('left', axd)
        self.assertEqual(len(fig2.axes), 3)
        axd['left'].plot([0, 1], [0, 1])
        self.draw_and_close(fig2)

    def test_constrained_layout_fallback(self):
        fig, ax = _subplots_constrained()
        ax.plot([0, 1], [0, 1])
        self.draw_and_close(fig)


class TestLinesMarkersStyles(MPLTestCase):
    def test_lines_markers_linestyles(self):
        fig, ax = plt.subplots()
        x = np.linspace(0, 2, 50)
        (l1,) = ax.plot(x, x, label="linear", color='C0', linewidth=2, linestyle='--', marker='o', markersize=4)
        (l2,) = ax.plot(x, x**2, label="quadratic", color='C1')
        l2.set_linestyle(':')
        self.assertEqual(l1.get_linestyle(), '--')
        self.assertEqual(l2.get_linestyle(), ':')
        ax.legend()
        self.draw_and_close(fig)

    def test_fill_between_and_errorbar(self):
        fig, ax = plt.subplots()
        x = np.linspace(0, 1, 100)
        y = np.sin(2*np.pi*x)
        ax.fill_between(x, y-0.1, y+0.1, alpha=0.3)
        ax.errorbar(x[::10], y[::10], yerr=0.2, fmt='o', capsize=3, label='err')
        ax.legend()
        self.draw_and_close(fig)


class TestScatterBarHistPie(MPLTestCase):
    def test_scatter_and_bar(self):
        fig, ax = plt.subplots()
        data1, data2 = np.random.randn(2, 100)
        s = np.random.rand(100) * 50 + 10
        c = np.random.rand(100)
        sc = ax.scatter(data1, data2, s=s, c=c, cmap='viridis', edgecolor='k')
        # Robust Colormap type check across versions
        self.assertIsType(sc.get_cmap(), colors.Colormap)
        categories = ['turnips', 'rutabaga', 'cucumber', 'pumpkins']
        ax.bar(categories, np.random.rand(len(categories)))
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        self.draw_and_close(fig)

    def test_hist_and_pie(self):
        fig, (ax1, ax2) = plt.subplots(1, 2)
        x = np.random.randn(1000)
        n, bins, patches = ax1.hist(x, bins=30, density=True, alpha=0.75)
        self.assertEqual(len(patches), 30)
        ax2.pie([10, 20, 30], labels=['A', 'B', 'C'], autopct='%1.1f%%', startangle=90)
        ax1.set_title('Hist')
        ax2.set_title('Pie')
        self.draw_and_close(fig)


class TestImagesColormapsColorbars(MPLTestCase):
    def test_imshow_pcolormesh_contour_colorbars(self):
        X, Y = np.meshgrid(np.linspace(-3, 3, 64), np.linspace(-3, 3, 64))
        Z = (1 - X/2 + X**5 + Y**3) * np.exp(-X**2 - Y**2)

        fig, axs = plt.subplots(2, 2)
        pc1 = axs[0, 0].pcolormesh(X, Y, Z, vmin=-1, vmax=1, cmap='RdBu_r')
        fig.colorbar(pc1, ax=axs[0, 0])

        co = axs[0, 1].contourf(X, Y, Z, levels=np.linspace(-1.25, 1.25, 11))
        fig.colorbar(co,   ax=axs[0, 1])

        im = axs[1, 0].imshow(Z**2 + 0.01, cmap='plasma', norm=LogNorm(vmin=0.01, vmax=10))
        cbar = fig.colorbar(im, ax=axs[1, 0], extend='both')
        self.assertIsType(cbar.norm, colors.Normalize)

        sc = axs[1, 1].scatter(np.random.randn(200), np.random.randn(200), c=np.random.randn(200), cmap='coolwarm')
        fig.colorbar(sc, ax=axs[1, 1])

        for ax in axs.ravel():
            ax.set_title(ax.get_title() or "ok")

        self.draw_and_close(fig)

    def test_custom_colormap_and_normalize(self):
        fig, ax = plt.subplots()
        data = np.linspace(0, 1, 100).reshape(10, 10)
        # Prefer modern API if available; fall back to cm.get_cmap for older versions
        try:
            cmap = matplotlib.colormaps.get_cmap('viridis')
        except AttributeError:
            cmap = cm.get_cmap('viridis')
        norm = Normalize(vmin=0.2, vmax=0.8, clip=True)
        im = ax.imshow(data, cmap=cmap, norm=norm)
        self.assertIs(im.norm, norm)
        self.draw_and_close(fig)


class TestAxesScalesTicksFormatters(MPLTestCase):
    def test_log_scale_and_ticks(self):
        fig, (ax1, ax2) = plt.subplots(1, 2)
        x = np.arange(1, 10)
        y = 10 ** np.linspace(0, 2, len(x))
        ax1.plot(x, y)
        ax2.set_yscale('log')
        ax2.plot(x, y)
        ax2.yaxis.set_major_locator(ticker.LogLocator(base=10))
        ax1.set_xticks([1, 5, 9], ['one', 'five', 'nine'])
        ax1.set_yticks([0, 50, 100])
        self.draw_and_close(fig)

    def test_secondary_and_twin_axes(self):
        t = np.linspace(0, 2*np.pi, 200)
        s = np.cos(2*np.pi*t)
        fig, (ax1, ax3) = plt.subplots(1, 2, figsize=(7, 3))
        l1, = ax1.plot(t, s, label="sine (left)")
        ax2 = ax1.twinx()
        l2, = ax2.plot(t, np.linspace(0, len(t)-1, len(t)), 'C1', label="index (right)")
        ax2.legend([l1, l2], ['Sine (left)', 'Straight (right)'])

        ax3.plot(t, s)
        ax3.set_xlabel('Angle [rad]')

        if hasattr(ax3, 'secondary_xaxis'):
            # Older Matplotlib requires keyword 'functions=...'
            try:
                ax4 = ax3.secondary_xaxis('top', functions=(np.rad2deg, np.deg2rad))
            except TypeError:
                # Very old signature fallback: create without transform functions if necessary
                ax4 = ax3.secondary_xaxis('top')
            ax4.set_xlabel('Angle [°]')
            self.assertIsNotNone(ax4)
        else:
            self.skipTest("secondary_xaxis is not available in this Matplotlib version")

        self.draw_and_close(fig)


class TestDatesAndCategorical(MPLTestCase):
    def test_dates_formatter(self):
        fig, ax = plt.subplots()
        dts = np.arange(np.datetime64('2021-11-15'), np.datetime64('2021-11-18'),
                        np.timedelta64(1, 'h'))
        vals = np.cumsum(np.random.randn(len(dts)))
        ax.plot(dts, vals)
        ax.xaxis.set_major_formatter(dates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
        self.assertIsType(ax.xaxis.get_major_formatter(), dates.ConciseDateFormatter)
        self.draw_and_close(fig)

    def test_categorical(self):
        fig, ax = plt.subplots()
        cats = ['a', 'b', 'c']
        ax.bar(cats, [1, 2, 3])
        self.assertEqual(len(ax.patches), 3)
        self.draw_and_close(fig)


class TestTextAnnotationsLegends(MPLTestCase):
    def test_text_and_math_and_annotation(self):
        fig, ax = plt.subplots()
        x = 115 + 15*np.random.randn(1000)
        ax.hist(x, 30, density=True, alpha=0.5)
        ax.set_xlabel('Length [cm]')
        ax.set_ylabel('Probability')
        ax.set_title(r'Aardvark lengths: $\mu=115,\ \sigma=15$')
        ax.text(80, 0.02, r'$\sigma_i=15$')
        ax.annotate('local note', xy=(np.mean(x), 0.01), xytext=(np.mean(x)+10, 0.02),
                    arrowprops=dict(facecolor='black', shrink=0.05))
        self.draw_and_close(fig)

    def test_legend_properties(self):
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], label='line1')
        ax.plot([0, 1], [1, 0], label='line2')
        leg = ax.legend(title="Legend")
        self.assertIsType(leg, matplotlib.legend.Legend)
        self.draw_and_close(fig)


class Test3DAndPolar(MPLTestCase):
    def test_3d_lines_and_scatter(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        t = np.linspace(0, 2*np.pi, 100)
        ax.plot3D(np.cos(t), np.sin(t), t, label='helix')
        ax.scatter3D(np.cos(t), np.sin(t), t, c=t, cmap='viridis')
        ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
        self.draw_and_close(fig)

    def test_polar_plot(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='polar')
        theta = np.linspace(0, 2*np.pi, 50)
        r = 0.5 + 0.5*np.sin(5*theta)
        ax.plot(theta, r)
        self.draw_and_close(fig)


class TestPatchesCollectionsTransforms(MPLTestCase):
    def test_patches_and_collections(self):
        fig, ax = plt.subplots()
        rect = Rectangle((0.1, 0.1), 0.5, 0.3, facecolor='C2', edgecolor='k')
        circ = Circle((0.7, 0.7), 0.2, facecolor='C3', alpha=0.6)
        ax.add_patch(rect)
        ax.add_patch(circ)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        self.assertGreaterEqual(len(ax.patches), 2)
        self.draw_and_close(fig)

    def test_transforms_and_figure_text(self):
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        fig.text(0.02, 0.98, "Top-left", transform=fig.transFigure, va='top')
        ax.text(0.5, 0.5, "In-axes", transform=ax.transAxes, ha='center')
        self.draw_and_close(fig)


class TestMaskedArraysAndDataInputs(MPLTestCase):
    def test_masked_array_plot(self):
        fig, ax = plt.subplots()
        y = np.linspace(-1, 1, 50)
        m = np.ma.masked_greater(y, 0.5)
        ax.plot(m, 'o-')
        # ensure masked values exist
        self.assertTrue(np.ma.isMaskedArray(m) and np.any(m.mask))
        self.draw_and_close(fig)

    def test_dict_data_interface(self):
        fig, ax = plt.subplots()
        data = {'a': np.arange(20), 'b': np.random.randn(20), 'c': np.random.rand(20)}
        ax.scatter('a', 'b', c='c', s=50, data=data)
        ax.set_xlabel('entry a'); ax.set_ylabel('entry b')
        self.draw_and_close(fig)


class TestLayoutAndSubfigures(MPLTestCase):
    def test_multiple_figures_and_save(self):
        # Ensure multiple figures can coexist and render
        fig1, ax1 = plt.subplots()
        ax1.plot([1, 2, 3], [1, 4, 9])
        fig2, ax2 = plt.subplots()
        ax2.imshow(np.random.rand(10, 10), cmap='gray')
        self.draw_and_close(fig1)
        self.draw_and_close(fig2)

    def test_subplot_mosaic_layouts(self):
        fig, axd = plt.subplot_mosaic([['upleft', 'right'],
                                       ['lowleft', 'right']])
        for name, ax in axd.items():
            ax.set_title(name)
            ax.plot([0, 1], [0, 1])
        self.assertEqual(len(fig.axes), 3)
        self.draw_and_close(fig)


class TestStylesAndRCParams(MPLTestCase):
    def test_style_context_and_rc(self):
        # baseline linewidth
        base_lw = plt.rcParams['lines.linewidth']
        with plt.style.context('ggplot'):
            fig, ax = plt.subplots()
            (ln,) = ax.plot([0, 1], [0, 1])
            self.draw_and_close(fig)

        with plt.rc_context({'lines.linewidth': 5}):
            fig, ax = plt.subplots()
            (ln2,) = ax.plot([0, 1], [0, 1])
            self.assertEqual(ln2.get_linewidth(), 5)
            self.draw_and_close(fig)
        # rc reset happened, so default restored approximately
        self.assertEqual(plt.rcParams['lines.linewidth'], base_lw)


class TestSavingDrawingIO(MPLTestCase):
    def test_savefig_to_bytes_and_svg(self):
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        # PNG
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        self.assertGreater(buf.tell(), 0)
        # SVG
        buf2 = io.BytesIO()
        fig.savefig(buf2, format='svg')
        self.assertGreater(buf2.tell(), 0)
        plt.close(fig)

    def test_canvas_draw(self):
        fig, ax = plt.subplots()
        ax.plot(np.random.rand(10))
        # Draw twice to catch any re-entrant issues
        fig.canvas.draw()
        fig.canvas.draw()
        self.draw_and_close(fig)


class TestAxesHelpersAPIs(MPLTestCase):
    def test_helpers_like_stairs_and_stem(self):
        fig, axs = plt.subplots(1, 2)
        x_edges = np.arange(11)  # len(edges) must be len(values)+1
        y_vals = np.random.rand(10)
        if hasattr(axs[0], "stairs"):
            # Provide correct edges length, robust to older signatures
            try:
                axs[0].stairs(y_vals, x_edges)  # positional edges
            except TypeError:
                axs[0].stairs(y_vals, edges=x_edges)  # keyword for very old signature
        else:
            self.skipTest("stairs is not available in this Matplotlib version")

        markerline, stemlines, baseline = axs[1].stem(np.arange(5), np.random.rand(5))
        # stemlines may be a list or LineCollection; convert to length safely
        try:
            n_stems = len(stemlines)
        except TypeError:
            n_stems = 1
        self.assertGreater(n_stems, 0)
        self.draw_and_close(fig)

    def test_boxplot_violinplot(self):
        fig, axs = plt.subplots(1, 2)
        data = [np.random.randn(100) + i for i in range(3)]
        axs[0].boxplot(data)
        axs[1].violinplot(data, showmeans=True)
        self.draw_and_close(fig)


if __name__ == "__main__":
    # Silence common non-critical warnings that vary across Matplotlib versions.
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=MatplotlibDeprecationWarning)
    unittest.main()