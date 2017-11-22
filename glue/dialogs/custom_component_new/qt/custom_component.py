from __future__ import absolute_import, division, print_function

import os
from collections import defaultdict

from qtpy import QtWidgets
from qtpy.QtCore import Qt

from glue.core import ComponentID
from glue.core.parse import ParsedCommand, ParsedComponentLink
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
            self.ui.combosel_data.addItem(data.label, userData=data)

        self.ui.combosel_data.setCurrentIndex(0)
        self.ui.combosel_data.currentIndexChanged.connect(self._update_derived_component_list)
        self._update_derived_component_list()

        self.ui.list_derived.itemSelectionChanged.connect(self._update_expression_panel)

        self.ui.button_add_component.clicked.connect(self._add_component)
        self.ui.button_save.clicked.connect(self._save_current_expression)
        # self.ui.button_remove_component.clicked.connect(self._remove_component)

        self.ui.list_derived.itemChanged.connect(self._component_renamed)

    @property
    def data(self):
        return self.ui.combosel_data.currentData()

    @property
    def derived_components(self):
        for cid in self.data.derived_components:
            comp = self.data.get_component(cid)
            if isinstance(comp.link, ParsedComponentLink):
                yield cid, comp

    @property
    def selected_component(self):
        items = self.ui.list_derived.selectedItems()
        if len(items) == 1:
            return items[0].data(Qt.UserRole)
        else:
            return None

    def _update_derived_component_list(self, *args):

        # This gets called when the data is changed and we need to update the
        # components shown in the left.

        self.ui.list_derived.clear()

        for cid, comp in self.derived_components:
            item = QtWidgets.QListWidgetItem(cid.label)
            item.setData(Qt.UserRole, cid)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.ui.list_derived.addItem(item)

        self._update_expression_panel()

    def _update_expression_panel(self, *args):

        cid = self.selected_component

        print(cid)

        if cid is None:
            self.ui.text_expression.setText('')
            self.ui.button_save.setEnabled(False)
            return
        else:
            self.ui.button_save.setEnabled(True)

        comp = self.data.get_component(cid)

        self.ui.text_expression.setText(comp.link._parsed._cmd)

    def _save_current_expression(self, *args):

        cid = self.selected_component
        comp = self.data.get_component(cid)
        comp.link._parsed._cmd = self.ui.text_expression.toPlainText()

    def _add_component(self, *args):

        self.data.add_component

        command = ParsedCommand('{test1:x}', {'test1:x': self.data.id['x']})
        link = ParsedComponentLink(ComponentID('new'), command)
        self.data.add_component_link(link)

        self._update_derived_component_list()

    def _component_renamed(self, *args):
        # This gets called if the text or data of the item change. It may be
        # called in more situations than we need, but no harm - we are just
        # making sure the data object is in sync with the visible text.
        for idx in range(self.ui.list_derived.count()):
            item = self.ui.list_derived.item(idx)
            label = item.text()
            cid = item.data(Qt.UserRole)
            if label != cid.label:
                cid.label = label


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
