from __future__ import absolute_import, division, print_function

import os
from functools import partial

from glue.external.qt.QtCore import Qt
from glue.external.qt import QtGui
from glue.core import message as msg
from glue.viewers.histogram.client import HistogramClient
from glue.viewers.common.qt.toolbar import GlueToolbar
from glue.viewers.common.qt.mouse_mode import HRangeMode
from glue.utils.qt import load_ui
from glue.utils.qt.widget_properties import (connect_int_spin, ButtonProperty,
                                             FloatLineProperty, connect_float_edit,
                                             ValueProperty, connect_bool_button,
                                             CurrentComboProperty, connect_current_combo)
from glue.viewers.common.qt.data_viewer import DataViewer
from glue.viewers.common.qt.mpl_widget import MplWidget, defer_draw
from glue.viewers.histogram.qt.layer_style_widget import HistogramLayerStyleWidget
from glue.utils.array import pretty_number
from glue.core.qt.data_combo_helper import ComponentIDComboHelper

__all__ = ['HistogramWidget']


WARN_SLOW = 10000000


def _hash(x):
    return str(id(x))


class HistogramWidget(DataViewer):
    LABEL = "Histogram"
    _property_set = DataViewer._property_set + \
        'component xlog ylog normed cumulative autoscale xmin xmax nbins'.split(
        )

    component = CurrentComboProperty('ui.attributeCombo', 'Component')
    xmin = FloatLineProperty('ui.xmin', 'Minimum value')
    xmax = FloatLineProperty('ui.xmax', 'Maximum value')
    normed = ButtonProperty('ui.normalized_box', 'Normalized?')
    autoscale = ButtonProperty('ui.autoscale_box',
                               'Autoscale view to histogram?')
    cumulative = ButtonProperty('ui.cumulative_box', 'Cumulative?')
    nbins = ValueProperty('ui.binSpinBox', 'Number of bins')
    xlog = ButtonProperty('ui.xlog_box', 'Log-scale the x axis?')
    ylog = ButtonProperty('ui.ylog_box', 'Log-scale the y axis?')

    _layer_style_widget_cls = HistogramLayerStyleWidget

    def __init__(self, session, parent=None):
        super(HistogramWidget, self).__init__(session, parent)

        self.central_widget = MplWidget()
        self.setCentralWidget(self.central_widget)
        self.option_widget = QtGui.QWidget()

        self.ui = load_ui('options_widget.ui', self.option_widget,
                          directory=os.path.dirname(__file__))

        # Set up helper for attribute box
        self._attribute_helper = ComponentIDComboHelper(self.ui.attributeCombo, self._data)

        self._tweak_geometry()
        self.client = HistogramClient(self._data,
                                      self.central_widget.canvas.fig,
                                      layer_artist_container=self._layer_artist_container)
        self._init_limits()
        self.make_toolbar()
        self._connect()
        # maps _hash(componentID) -> componentID
        self._component_hashes = {}

    @staticmethod
    def _get_default_tools():
        return []

    def _init_limits(self):
        validator = QtGui.QDoubleValidator(None)
        validator.setDecimals(7)
        self.ui.xmin.setValidator(validator)
        self.ui.xmax.setValidator(validator)
        lo, hi = self.client.xlimits
        self.ui.xmin.setText(str(lo))
        self.ui.xmax.setText(str(hi))

    def _tweak_geometry(self):
        self.central_widget.resize(600, 400)
        self.resize(self.central_widget.size())

    def _connect(self):

        ui = self.ui
        cl = self.client

        ui.attributeCombo.currentIndexChanged.connect(self._update_buttons)

        connect_current_combo(cl, 'component', ui.attributeCombo)

        ui.normalized_box.toggled.connect(partial(setattr, cl, 'normed'))
        ui.autoscale_box.toggled.connect(partial(setattr, cl, 'autoscale'))
        ui.cumulative_box.toggled.connect(partial(setattr, cl, 'cumulative'))

        connect_int_spin(cl, 'nbins', ui.binSpinBox)
        connect_float_edit(cl, 'xmin', ui.xmin)
        connect_float_edit(cl, 'xmax', ui.xmax)
        connect_bool_button(cl, 'xlog', ui.xlog_box)
        connect_bool_button(cl, 'ylog', ui.ylog_box)

    def make_toolbar(self):
        result = GlueToolbar(self.central_widget.canvas, self,
                             name='Histogram')
        for mode in self._mouse_modes():
            result.add_mode(mode)
        self.addToolBar(result)
        return result

    def _mouse_modes(self):
        axes = self.client.axes

        def apply_mode(mode):
            return self.apply_roi(mode.roi())

        rect = HRangeMode(axes, roi_callback=apply_mode)
        return [rect]

    @defer_draw
    def _update_buttons(self, *args):
        if self.component is not None:
            for d in self._data:
                try:
                    component = d.get_component(self.component)
                except:
                    continue
                else:
                    break
            if component.categorical:
                self.ui.xlog_box.setEnabled(False)
                self.xlog = False
            else:
                self.ui.xlog_box.setEnabled(True)
        self.update_window_title()

    @defer_draw
    def add_data(self, data):
        """ Add data item to combo box.
        If first addition, also update attributes """

        if self.data_present(data):
            return True

        if data.size > WARN_SLOW and not self._confirm_large_data(data):
            return False

        self.client.add_layer(data)
        self._attribute_helper.append(data)

        return True

    def add_subset(self, subset):
        pass

    def data_present(self, data):
        return data in self._layer_artist_container

    def register_to_hub(self, hub):
        super(HistogramWidget, self).register_to_hub(hub)
        self.client.register_to_hub(hub)

    def unregister(self, hub):
        super(HistogramWidget, self).unregister(hub)
        self.client.unregister(hub)
        self._attribute_helper.unregister(hub)

    @property
    def window_title(self):
        c = self.client.component
        if c is not None:
            label = str(c.label)
        else:
            label = 'Histogram'
        return label

    def _update_labels(self):
        self.update_window_title()

    def __str__(self):
        return "Histogram Widget"

    def options_widget(self):
        return self.option_widget
