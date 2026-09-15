import numpy as np

from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection

from glue.config import layer_artist_maker
from glue.core import BaseData, Subset
from glue.core.exceptions import IncompatibleAttribute
from glue.core.units import UnitConverter
from glue.utils import defer_draw, ensure_numerical, datetime64_to_mpl
from glue.viewers.matplotlib.state import (MatplotlibLayerState,
                                           DeferredDrawCallbackProperty as DDCProperty)
from glue.viewers.matplotlib.layer_artist import MatplotlibLayerArtist

__all__ = ['VerticalLineLayerState', 'VerticalLineLayerArtist', 'add_vertical_lines']


class VerticalLineLayerState(MatplotlibLayerState):
    """
    A state class for layers shown as full-height vertical lines.
    """

    linewidth = DDCProperty(1, docstring='The width of the vertical lines')
    linestyle = DDCProperty('solid', docstring='The style of the vertical lines')


def values_to_segments(values):
    """
    Construct segments for a `~matplotlib.collections.LineCollection` with one
    full-height vertical line per value, where the direction along the lines
    is in axes fraction coordinates (0 to 1).
    """
    segments = np.zeros((len(values), 2, 2))
    segments[:, 0, 0] = values
    segments[:, 1, 0] = values
    segments[:, 1, 1] = 1
    return segments


class VerticalLineLayerArtist(MatplotlibLayerArtist):
    """
    A layer artist that renders the values of the viewer x attribute for the
    layer as full-height vertical lines.

    This can be used in any Matplotlib-based viewer whose viewer state has an
    ``x_att`` attribute, e.g. the scatter, profile, histogram, and image
    viewers, and is aimed at datasets such as spectral line lists for which
    only positions along the x axis are meaningful.
    """

    _layer_state_cls = VerticalLineLayerState

    def __init__(self, axes, viewer_state, layer_state=None, layer=None):

        super(VerticalLineLayerArtist, self).__init__(axes, viewer_state,
                                                      layer_state=layer_state,
                                                      layer=layer)

        self._viewer_state.add_global_callback(self._update_vertical_lines)
        self.state.add_global_callback(self._update_vertical_lines)

        # The line collection uses a blended transform so that the lines
        # always span the full height of the axes regardless of the y limits.
        self.vline_collection = LineCollection(np.zeros((0, 2, 2)),
                                               transform=self.axes.get_xaxis_transform())
        self.axes.add_collection(self.vline_collection)

        self.mpl_artists = [self.vline_collection]

    @defer_draw
    def _update_data(self):

        x_att = self._viewer_state.x_att

        try:
            values = ensure_numerical(self.layer[x_att].ravel())
            if values.dtype.kind == 'M':
                values = datetime64_to_mpl(values)
        except (IncompatibleAttribute, IndexError):
            self.vline_collection.set_segments(np.zeros((0, 2, 2)))
            self.redraw()
            if isinstance(self.state.layer, BaseData):
                self.disable_invalid_attributes(x_att)
            else:
                self.disable_incompatible_subset()
            return

        # Viewers such as the profile viewer support displaying the x axis in
        # different units, in which case the positions need to be converted.
        x_display_unit = getattr(self._viewer_state, 'x_display_unit', None)
        reference_data = getattr(self._viewer_state, 'reference_data', None)
        if x_display_unit is not None and reference_data is not None:
            converter = UnitConverter()
            values = converter.to_unit(reference_data, x_att, values, x_display_unit)

        self.enable()
        positions = np.unique(values[~np.isnan(values)])
        self.vline_collection.set_segments(values_to_segments(positions))
        self.redraw()

    @defer_draw
    def _update_visual_attributes(self):

        if not self.enabled:
            return

        self.vline_collection.set_visible(self.state.visible)
        self.vline_collection.set_zorder(self.state.zorder)
        self.vline_collection.set_color(self.state.color)
        self.vline_collection.set_alpha(self.state.alpha)
        self.vline_collection.set_linewidth(self.state.linewidth)
        self.vline_collection.set_linestyle(self.state.linestyle)

        self.redraw()

    def _update_vertical_lines(self, force=False, **kwargs):

        if (getattr(self._viewer_state, 'x_att', None) is None or
                self.state.layer is None):
            return

        # NOTE: we need to evaluate this even if force=True so that the cache
        # of updated properties is up to date after this method has been called.
        changed = self.pop_changed_properties()

        if force or any(prop in changed for prop in ('layer', 'x_att', 'x_att_pixel',
                                                     'x_display_unit', 'reference_data')):
            self._update_data()
            force = True

        if force or any(prop in changed for prop in ('alpha', 'color', 'zorder', 'visible',
                                                     'linewidth', 'linestyle')):
            self._update_visual_attributes()

    @defer_draw
    def update(self):
        self._update_vertical_lines(force=True)
        self.redraw()

    def get_handle_legend(self):
        if self.enabled and self.state.visible:
            handle = Line2D([0], [0], alpha=self.state.alpha,
                            linestyle=self.state.linestyle,
                            linewidth=self.state.linewidth,
                            color=self.get_layer_color())
            return handle, self.layer.label, None
        else:
            return None, None, None


def add_vertical_lines(viewer, layer):
    """
    Add a dataset or subset to a Matplotlib-based viewer as full-height
    vertical lines at the values of the viewer x attribute.

    Any existing subsets of a dataset are added along with it, and any subsets
    created afterwards will also be shown as vertical lines.

    Parameters
    ----------
    viewer : viewer based on `~glue.viewers.matplotlib.viewer.MatplotlibViewerMixin`
        The viewer to add the layer to.
    layer : `~glue.core.data.BaseData` or `~glue.core.subset.Subset`
        The dataset or subset to show as vertical lines.

    Returns
    -------
    artist : `VerticalLineLayerArtist`
        The layer artist that was added to the viewer.
    """
    artist = viewer.get_layer_artist(VerticalLineLayerArtist, layer=layer)
    viewer._layer_artist_container.append(artist)
    artist.update()
    viewer.draw_legend()
    if isinstance(layer, BaseData):
        for subset in layer.subsets:
            add_vertical_lines(viewer, subset)
    return artist


@layer_artist_maker('vertical-line-subsets')
def vertical_line_subset_maker(viewer, layer):
    # New subsets follow the parent dataset: if the parent data is shown as
    # vertical lines in this viewer, subsets of it should be too.
    if isinstance(layer, Subset):
        for artist in viewer._layer_artist_container:
            if isinstance(artist, VerticalLineLayerArtist) and artist.layer is layer.data:
                return viewer.get_layer_artist(VerticalLineLayerArtist, layer=layer)
