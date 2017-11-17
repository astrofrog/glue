from __future__ import absolute_import, division, print_function

import os
from collections import defaultdict

from qtpy import QtWidgets

from glue.core.parse import ParsedComponentLink
from glue.utils.qt import load_ui

__all__ = ['CustomComponentWidget']


class CustomComponentWidget(QtWidgets.QDialog):

    def __init__(self, data_collection=None, parent=None):

        super(CustomComponentWidget, self).__init__(parent=parent)

        self.ui = load_ui('custom_component.ui', self,
                          directory=os.path.dirname(__file__))

        self.data_collection = data_collection

        # Populate data combo
        for data in self.data_collection:
            self.ui.combosel_data.addItem(data.label, userData=data.label)

        # Figure out what the derived components are for each dataset. We then
        # store these inside a dictionary - we only update the actual data
        # objects at the end once the user clicks 'ok'.
        self.derived = defaultdict(list)
        for data in self.data_collection:
            for cid in data.derived_components:
                comp = data.get_component(cid)
                if isinstance(comp.link, ParsedComponentLink):
                    self.derived[data].append({'label': cid.label,
                                               'type': 'custom',
                                               'expression': comp._parsed._cmd})

        self.ui.combosel_data.setCurrentIndex(0)
        self.ui.combosel_data.currentIndexChanged.connect(self._update_derived_component_list)
        self._update_derived_component_list()

        self.ui.list_derived.itemSelectionChanged.connect(self._update_expression_panel)

        self.ui.button_add_component.clicked.connect(self._add_component)
        # self.ui.button_remove_component.clicked.connect(self._remove_component)

    @property
    def data(self):
        return self.ui.combosel_data.currentData()

    @property
    def selected_component(self):
        for index in range(self.ui.list_derived.count()):
            if self.ui.list_derived.item(index).isSelected():
                return self.derived[self.data][index]
        else:
            return None

    def _update_derived_component_list(self, *args):

        # This gets called when the data is changed and we need to update the
        # components shown in the left.

        self.ui.list_derived.clear()

        for component in self.derived[self.data]:
            item = QtWidgets.QListWidgetItem(component['label'])
            self.ui.list_derived.addItem(item)

    def _update_expression_panel(self, *args):

        component = self.selected_component

        print(component)

        if component is None:
            self.ui.text_expression.setText('')

        self.ui.text_expression.setText(component['expression'])

    def _add_component(self, *args):

        print("ADD COMPONENT")

        self.derived[self.data].append({'label': 'Component name',
                                        'type': 'custom',
                                        'expression': ''})

        self._update_derived_component_list()
        self._update_expression_panel()


def main():

    import numpy as np

    from glue.core.data import Data
    from glue.core.data_collection import DataCollection

    x = np.random.random((5, 5))
    y = x * 3
    dc = DataCollection()
    dc.append(Data(label='test1', x=x, y=y))
    dc.append(Data(label='test2', a=x, b=y))

    widget = CustomComponentWidget(dc)
    widget.exec_()


if __name__ == "__main__":
    from glue.utils.qt import get_qapp
    app = get_qapp()
    main()
