from __future__ import absolute_import, division, print_function

import os

from qtpy import QtWidgets

from glue.core import Data, Subset
from glue.utils.qt import load_ui, autoconnect_qt
from glue.core.qt.data_combo_helper import ComponentIDComboHelper
from glue.viewers.common.qt.attribute_limits_helper import AttributeLimitsHelper

__all__ = ['ScatterOptionsWidget']


class ScatterOptionsWidget(QtWidgets.QWidget):

    def __init__(self, viewer_state, session, parent=None):

        super(ScatterOptionsWidget, self).__init__(parent=parent)

        self.ui = load_ui('options_widget.ui', self,
                          directory=os.path.dirname(__file__))

        autoconnect_qt(viewer_state, self.ui)

        viewer_state.connect('layers', self._update_combo_data)

        self.ui.button_reset.clicked.connect(self.reset_limits)

        self.xatt_helper = ComponentIDComboHelper(self.ui.combo_xatt,
                                                  session.data_collection,
                                                  default_index=0)
        self.yatt_helper = ComponentIDComboHelper(self.ui.combo_yatt,
                                                  session.data_collection,
                                                  default_index=1)
        # Share the cache for the limits as a function of attribute
        self.limits_cache = {}

        self.xatt_limits_helper = AttributeLimitsHelper(self.ui.combo_xatt,
                                                        self.ui.value_x_min,
                                                        self.ui.value_x_max,
                                                        flip_button=self.ui.button_flip_x,
                                                        log_button=self.ui.bool_log_x,
                                                        limits_cache=self.limits_cache)

        self.yatt_limits_helper = AttributeLimitsHelper(self.ui.combo_yatt,
                                                        self.ui.value_y_min,
                                                        self.ui.value_y_max,
                                                        flip_button=self.ui.button_flip_y,
                                                        log_button=self.ui.bool_log_y,
                                                        limits_cache=self.limits_cache)

        self.viewer_state = viewer_state

    def reset_limits(self):
        self.limits_cache.clear()
        self.xatt_limits_helper._update_limits()
        self.yatt_limits_helper._update_limits()

    def _update_combo_data(self, *args):

        layers = []

        for layer_state in self.viewer_state.layers:
            if isinstance(layer_state.layer, Data):
                if layer_state.layer not in layers:
                    layers.append(layer_state.layer)

        for layer_state in self.viewer_state.layers:
            if isinstance(layer_state.layer, Subset) and layer_state.layer.data not in layers:
                if layer_state.layer not in layers:
                    layers.append(layer_state.layer)

        self.xatt_helper.set_multiple_data(layers)
        self.yatt_helper.set_multiple_data(layers)