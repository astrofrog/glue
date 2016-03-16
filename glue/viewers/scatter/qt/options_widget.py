import os
import math
from functools import partial

import numpy as np
from glue.external.qt import QtGui

from glue.utils.qt.widget_properties import CurrentComboProperty, FloatLineProperty, connect_bool_button, ButtonProperty
from glue.utils.qt import load_ui
from glue.viewers.common.qt.attribute_limits_helper import AttributeLimitsHelper

__all__ = ["ScatterOptionsWidget"]


class ScatterOptionsWidget(QtGui.QWidget):

    x_att = CurrentComboProperty('ui.combo_x_attribute')
    x_log = ButtonProperty('ui.button_x_log')
    x_min = FloatLineProperty('ui.value_x_min')
    x_max = FloatLineProperty('ui.value_x_max')

    y_att = CurrentComboProperty('ui.combo_y_attribute')
    y_log = ButtonProperty('ui.button_y_log')
    y_min = FloatLineProperty('ui.value_y_min')
    y_max = FloatLineProperty('ui.value_y_max')

    hidden = FloatLineProperty('ui.checkbox_hidden')

    def __init__(self, parent=None, data=None):

        super(ScatterOptionsWidget, self).__init__(parent=parent)

        self.ui = load_ui('options_widget.ui', self,
                          directory=os.path.dirname(__file__))

        self.ui.button_flip_axes.clicked.connect(self._flip_axes)

        # Share limits cache between the two sets of limits
        limits_cache = {}

        self.x_limits_helper = AttributeLimitsHelper(self.ui.combo_x_attribute,
                                                     self.ui.value_x_min,
                                                     self.ui.value_x_max,
                                                     flip_button=self.ui.button_flip_x,
                                                     limits_cache=limits_cache)

        self.y_limits_helper = AttributeLimitsHelper(self.ui.combo_y_attribute,
                                                     self.ui.value_y_min,
                                                     self.ui.value_y_max,
                                                     flip_button=self.ui.button_flip_y,
                                                     limits_cache=limits_cache)

        self.x_limits_helper.data = data
        self.y_limits_helper.data = data

    def _flip_axes(self):
        self.x_att, self.y_att = self.y_att, self.x_att
        self.x_log, self.y_log = self.y_log, self.x_log

# TODO: include log button in attribute limits helper

if __name__ == "__main__":

    from glue.external.qt import get_qapp
    from glue.core import Data

    data = Data(x=[1,2,3], y=[4,5,6], z=[7,8,9])

    app = get_qapp()

    widget = ScatterOptionsWidget(data=data)
    widget.show()
    widget.raise_()

    app.exec_()
