from __future__ import absolute_import, division, print_function

from glue.external.qt.QtCore import Qt
# from glue.viewers.scatter.client import ScatterClient
from glue.viewers.common.qt.toolbar import GlueToolbar
from glue.viewers.common.qt.mouse_mode import (RectangleMode, CircleMode,
                                PolyMode, HRangeMode, VRangeMode)
from glue.viewers.common.qt.data_viewer import DataViewer
from glue.viewers.common.qt.mpl_widget import MplWidget, defer_draw
from glue.viewers.scatter.qt.options_widget import ScatterOptionsWidget
from glue.viewers.scatter.qt.layer_style_widget import ScatterLayerStyleWidget
from glue.utils import nonpartial, cache_axes
from glue.utils.qt.widget_properties import (ButtonProperty, FloatLineProperty,
                                             CurrentComboProperty,
                                             connect_bool_button, connect_float_edit)
from glue.viewers.common.viz_client import init_mpl
from ..layer_artist import ScatterLayerArtist

__all__ = ['ScatterWidget']

WARN_SLOW = 1000000  # max number of points which render quickly

# TODO: split out things to do with options widget and caching into
# options_widget.py, similarly to what we did in 3D

# TODO: finish up attribute limits helper since it can be used here. Need to add
# a log option.

# TODO: use similar layout as for 3D scatter plot viewer and add log option to
# 3D scatter plot viewer.

# TODO: make sure the two attribute combos don't default to the same attribute,
# in the options widget.

# TODO: add back window title
# TODO: add back button for autoscaling
# TODO: get log scaling to work
# TODO: add back cache_axis
# TODO: add back ability to restore viewer
# TODO: make warning about large data a feature of DataViewer
# TODO: make it so the MPL canvas is easily replaceable


# Matplotlib widget should be in charge of creating axes and have callback
# properties for xmin/xmax/xlog etc.


class ScatterWidget(DataViewer):

    """
    An interactive scatter plot.
    """

    LABEL = "Scatter Plot"

    _layer_style_widget_cls = ScatterLayerStyleWidget

    def __init__(self, session, parent=None):

        super(ScatterWidget, self).__init__(session, parent)

        self.central_widget = MplWidget()
        self.setCentralWidget(self.central_widget)

        figure, axes = init_mpl(figure=self.central_widget.canvas.fig)

        self.figure = figure
        self._axes = axes

        self._options_widget = ScatterOptionsWidget(data_collection=self._data)

        self._tweak_geometry()
        
        self.client = self

        self._connect()
        self.unique_fields = set()
        tb = self.make_toolbar()

        # cache_axes(self.client.axes, tb)
        self.statusBar().setSizeGripEnabled(False)
        self.setFocusPolicy(Qt.StrongFocus)

    def add_layer(self, data):
        """
        Adds a new visual layer to a client, to display either a dataset or a
        subset.

        Returns the created layer artist

        :param layer: the layer to add
        :type layer: :class:`~glue.core.data.Data` or :class:`~glue.core.subset.Subset`
        """

        if data.data not in self._data:
            raise TypeError("Layer not in data collection")

        if data in self._layer_artist_container:
            return self._layer_artist_container[data][0]

        layer_artist = ScatterLayerArtist(data, self._axes)
        self._layer_artist_container.append(layer_artist)
        layer_artist.update()

        return layer_artist

    def _update_attributes(self):
        options = self._options_widget.ui
        for artist in self._layer_artist_container:
            if options.x_att is not None:
                artist.xatt = options.x_att[0]
            if options.y_att is not None:
                artist.yatt = options.y_att[0]
        self._update_all_artists()

    def _update_all_artists(self):
        for artist in self._layer_artist_container:
            artist.update()
        if len(self._layer_artist_container) > 0:
            self._layer_artist_container[0].redraw()

    @staticmethod
    def _get_default_tools():
        return []

    def _tweak_geometry(self):
        self.central_widget.resize(600, 400)
        self.resize(self.central_widget.size())

    def _connect(self):

        options = self._options_widget.ui

        options.button_x_log.toggled.connect(nonpartial(self._update_limits))
        options.button_y_log.toggled.connect(nonpartial(self._update_limits))
        options.value_x_min.editingFinished.connect(nonpartial(self._update_limits))
        options.value_x_max.editingFinished.connect(nonpartial(self._update_limits))
        options.value_y_min.editingFinished.connect(nonpartial(self._update_limits))
        options.value_y_max.editingFinished.connect(nonpartial(self._update_limits))

        options.combo_x_attribute.currentIndexChanged.connect(nonpartial(self._update_attributes))
        options.combo_y_attribute.currentIndexChanged.connect(nonpartial(self._update_attributes))

    @defer_draw
    def _update_limits(self):
        options = self._options_widget.ui
        self._axes.set_xlim(options.x_min, options.x_max)
        self._axes.set_ylim(options.y_min, options.y_max)
        self._axes.set_xscale('log' if options.x_log else 'linear')
        self._axes.set_yscale('log' if options.y_log else 'linear')
        self._update_all_artists()

    def make_toolbar(self):
        result = GlueToolbar(self.central_widget.canvas, self,
                             name='Scatter Plot')
        for mode in self._mouse_modes():
            result.add_mode(mode)
        self.addToolBar(result)
        return result


    def apply_mode(self, mode):
        roi = mode.roi()
        return self.apply_roi(roi)

    def _mouse_modes(self):
        axes = self._axes

        rect = RectangleMode(axes, roi_callback=self.apply_mode)
        xra = HRangeMode(axes, roi_callback=self.apply_mode)
        yra = VRangeMode(axes, roi_callback=self.apply_mode)
        circ = CircleMode(axes, roi_callback=self.apply_mode)
        poly = PolyMode(axes, roi_callback=self.apply_mode)
        return [rect, xra, yra, circ, poly]

    def apply_roi(self, roi):

        # every editable subset is updated
        # using specified ROI

        for x_comp, y_comp in zip(self._get_data_components('x'),
                                  self._get_data_components('y')):
                                  
            subset_state = x_comp.subset_from_roi(self.xatt, roi,
                                                  other_comp=y_comp,
                                                  other_att=self.yatt,
                                                  coord='x')
            mode = EditSubsetMode()
            visible = [d for d in self._data if self.is_visible(d)]
            focus = visible[0] if len(visible) > 0 else None
            mode.update(self._data, subset_state, focus_data=focus)
            
    @defer_draw
    def add_data(self, data):
        """Add a new data set to the widget

        :returns: True if the addition was expected, False otherwise
        """
        # if self.client.is_layer_present(data):
        #     return

        if data.size > WARN_SLOW and not self._confirm_large_data(data):
            return False

        self._options_widget.append(data)

        self.add_layer(data)

        self.update_window_title()
        return True

    @defer_draw
    def add_subset(self, subset):
        """Add a subset to the widget

        :returns: True if the addition was accepted, False otherwise
        """
        # if self.client.is_layer_present(subset):
        #     return

        data = subset.data
        if data.size > WARN_SLOW and not self._confirm_large_data(data):
            return False

        self._options_widget.append(subset)

        self.add_layer(subset)

        return True

    def options_widget(self):
        return self._options_widget

