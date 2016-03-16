import os
import math
from functools import partial

import numpy as np
from glue.external.qt import QtGui

from glue.utils.qt.widget_properties import CurrentComboProperty, FloatLineProperty, connect_bool_button, ButtonProperty
from glue.utils.qt import load_ui

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

    def __init__(self, parent=None):

        super(ScatterOptionsWidget, self).__init__(parent=parent)

        self.ui = load_ui('options_widget.ui', self,
                          directory=os.path.dirname(__file__))

        self.ui.button_flip_axes.clicked.connect(self._flip_axes)

    def _flip_axes(self):
        self.x_att, self.y_att = self.y_att, self.x_att




# Have a way for cache to be shared between different axis limit helpers


if __name__ == "__main__":
    
    from glue.external.qt import get_qapp
    
    app = get_qapp()
    
    widget = ScatterOptionsWidget()
    widget.show()
    widget.raise_()
    
    app.exec_()