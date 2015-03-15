# This is a WIP
#
# TODO:
# - auto-choose min/max and default levels to show
# - add parameters in left window to control above settings including alpha
# - add parameter to select component
# - add ability to show subset
# - fix window size
# - do something with messages

import sys
import vtk
import numpy as np
from astropy.io import fits
from PyQt4 import QtGui
from vtk.qt4.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from palettable.colorbrewer import get_map

from ...core.client import Client
from ... import core
from ...qt.widgets.data_viewer import DataViewer


class QtVTKWidget(DataViewer):

    LABEL = "3D Iso-surfaces"

    def __init__(self, session):

        super(QtVTKWidget, self).__init__(session)

        self._data = session.data_collection
        self.client = Client(self._data)

        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(0, 0, 0)

        self.renWin = vtk.vtkRenderWindow()
        self.renWin.AddRenderer(self.ren)

        self.ren.ResetCameraClippingRange()

        self.vtkw = QVTKRenderWindowInteractor(self, rw=self.renWin)
        self.vtkw.resize(800, 800)

    def add_data(self, data):

        data = data["PRIMARY"]
        
        vmin = 0.
        vmax = 5.
        
        nz, ny, nx = data.shape
        data = np.clip((data - vmin) / (vmax - vmin) * 255., 0., 255.)
        data = data.astype(np.uint8)
        data_string = data.tostring()

        # Prepare levels
        levels = np.array([1., 2., 4.])
        levels = np.clip((levels - vmin) / (vmax - vmin) * 255., 0., 255.)

        self.readerVolume = vtk.vtkImageImport()
        self.readerVolume.CopyImportVoidPointer(data_string, len(data_string))
        self.readerVolume.SetDataScalarTypeToUnsignedChar()
        self.readerVolume.SetNumberOfScalarComponents(1)
        self.readerVolume.SetDataExtent(0, nx - 1, 0, ny - 1, 0, nz - 1)
        self.readerVolume.SetWholeExtent(0, nx - 1, 0, ny - 1, 0, nz - 1)
        self.readerVolume.SetDataSpacing(1, 1, 1)

        palette = get_map('RdYlBu', 'diverging', len(levels))

        for ilevel, level in enumerate(levels):
            self.add_contour(level, color=palette.mpl_colors[ilevel], alpha=0.4)

        self.renWin.Render()
        self.renWin.PolygonSmoothingOn()
        self.vtkw.Initialize()
        self.vtkw.Start()
        
        return True

    def add_subset(self, subset):
        print("SUBSET")
        return True


    def add_contour(self, level, color=(1., 1., 1.), alpha=1.):

        print("ADDING CONTOUR", level)

        contour = vtk.vtkMarchingCubes()
        contour.SetInput(self.readerVolume.GetOutput())
        contour.SetValue(0, level)
        contour.ComputeNormalsOn()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInput(contour.GetOutput())
        mapper.ScalarVisibilityOff()

        actor = vtk.vtkLODActor()
        actor.SetMapper(mapper)
        actor.SetNumberOfCloudPoints(100000)
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetOpacity(alpha)

        self.ren.AddActor(actor)

    def register_to_hub(self, hub):
        print("REGISTER WITH HUB")

        self.client.register_to_hub(hub)
        hub.subscribe(self, core.message.DataUpdateMessage,
                      self._sync_labels)
        hub.subscribe(self, core.message.ComponentsChangedMessage,
                      self._update_combos)
        hub.subscribe(self, core.message.ComponentReplacedMessage,
                      self._on_component_replace)

    def _sync_labels(self, msg):
        print("SYNC LABELS")

    def _update_combos(self, msg):
        print("SYNC LABELS")

    def _on_component_replace(self, msg):
        print("SYNC LABELS")


from ...config import qt_client
qt_client.add(QtVTKWidget)
