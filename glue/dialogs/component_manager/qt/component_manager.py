from __future__ import absolute_import, division, print_function

import os
from collections import defaultdict

from qtpy import QtWidgets
from qtpy.QtCore import Qt

from glue.core.parse import ParsedComponentLink
from glue.utils.qt import load_ui

from glue.dialogs.component_manager.qt.equation_editor import EquationEditorDialog

__all__ = ['ComponentManagerWidget']


def data_collection_to_state(data_collection):

    state = defaultdict(dict)

    for data in data_collection:

        state[data]['main'] = []
        for cid in data.primary_components:
            comp_state = {}
            comp_state['cid'] = cid
            comp_state['label'] = cid.label
            state[data]['main'].append(comp_state)

        state[data]['derived'] = []
        for cid in data.derived_components:
            comp = data.get_component(cid)
            if isinstance(comp.link, ParsedComponentLink):
                comp_state = {}
                comp_state['cid'] = cid
                comp_state['label'] = cid.label
                comp_state['equation'] = comp.link._parsed._cmd
                state[data]['derived'].append(comp_state)

    return state


class ComponentManagerWidget(QtWidgets.QDialog):

    def __init__(self, data_collection=None, parent=None):

        super(ComponentManagerWidget, self).__init__(parent=parent)

        self.ui = load_ui('component_manager.ui', self,
                          directory=os.path.dirname(__file__))

        self.data_collection = data_collection

        # Populate data combo
        for data in self.data_collection:
            self.ui.combosel_data.addItem(data.label, userData=data)

        # Convert relevant data collection information to a dict
        self._state = data_collection_to_state(data_collection)

        self.ui.combosel_data.setCurrentIndex(0)
        self.ui.combosel_data.currentIndexChanged.connect(self._update_component_lists)

        self._update_component_lists()

        self.ui.button_add_derived.clicked.connect(self._add_derived_component)
        self.ui.button_edit_derived.clicked.connect(self._edit_derived_component)

        # self.ui.list_derived.itemSelectionChanged.connect(self._update_expression_panel)
        #
        # self.ui.button_add_component.clicked.connect(self._add_component)
        # self.ui.button_save.clicked.connect(self._save_current_expression)
        # # self.ui.button_remove_component.clicked.connect(self._remove_component)
        #
        # self.ui.list_derived.itemChanged.connect(self._component_renamed)

    @property
    def data(self):
        return self.ui.combosel_data.currentData()

    @property
    def selected_component(self):
        items = self.ui.list_derived.selectedItems()
        if len(items) == 1:
            return items[0].data(Qt.UserRole)
        else:
            return None

    def _update_component_lists(self, *args):

        # This gets called when the data is changed and we need to update the
        # components shown in the lists.

        self.ui.list_main_components.clear()
        self.ui.list_derived_components.clear()

        root = self.ui.list_main_components.invisibleRootItem()

        for comp_state in self._state[self.data]['main']:
            item = QtWidgets.QTreeWidgetItem(root, [comp_state['label']])
            item.setData(0, Qt.UserRole, comp_state['cid'])
            item.setFlags(item.flags() | Qt.ItemIsEditable)

        root = self.ui.list_derived_components.invisibleRootItem()

        for comp_state in self._state[self.data]['derived']:
            item = QtWidgets.QTreeWidgetItem(root, [comp_state['label']])
            item.setData(0, Qt.UserRole, comp_state['cid'])
            item.setFlags(item.flags() | Qt.ItemIsEditable)
    #
    # def _update_expression_panel(self, *args):
    #
    #     cid = self.selected_component
    #
    #     print(cid)
    #
    #     if cid is None:
    #         self.ui.text_expression.setText('')
    #         self.ui.button_save.setEnabled(False)
    #         return
    #     else:
    #         self.ui.button_save.setEnabled(True)
    #
    #     comp = self.data.get_component(cid)
    #
    #     self.ui.text_expression.setText(comp.link._parsed._cmd)
    #
    # def _save_current_expression(self, *args):
    #
    #     cid = self.selected_component
    #     comp = self.data.get_component(cid)
    #     comp.link._parsed._cmd = self.ui.text_expression.toPlainText()
    #

    def _add_derived_component(self, *args):

        comp_state = {}
        comp_state['cid'] = None
        comp_state['label'] = 'New component'
        comp_state['equation'] = ''

        self._state[self.data]['derived'].append(comp_state)

        self._update_component_lists()

    def _edit_derived_component(self, *args):

        dialog = EquationEditorDialog(self.data, '', parent=self)
        dialog.setWindowFlags(self.windowFlags() | Qt.Window)
        dialog.setFocus()
        dialog.raise_()
        dialog.exec_()

        if dialog.parsed_command is None:
            return


    # def _component_renamed(self, *args):
    #     # This gets called if the text or data of the item change. It may be
    #     # called in more situations than we need, but no harm - we are just
    #     # making sure the data object is in sync with the visible text.
    #     for idx in range(self.ui.list_derived.count()):
    #         item = self.ui.list_derived.item(idx)
    #         label = item.text()
    #         cid = item.data(Qt.UserRole)
    #         if label != cid.label:
    #             cid.label = label


def main():

    import numpy as np

    from glue.core.data import Data
    from glue.core.data_collection import DataCollection

    x = np.random.random((5, 5))
    y = x * 3
    dc = DataCollection()
    dc.append(Data(label='test1', x=x, y=y))
    dc.append(Data(label='test2', a=x, b=y))

    widget = ComponentManagerWidget(dc)
    widget.exec_()


if __name__ == "__main__":
    from glue.utils.qt import get_qapp
    app = get_qapp()
    main()
