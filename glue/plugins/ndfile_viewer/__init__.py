from glue.config import data_factory
from glue.core import Data
from glue.core.callback_property import CallbackProperty, add_callback
from glue.clients import GenericMplClient
from glue.core.coordinates import LUTCoordinates
from glue.qt.custom_viewer import ComponentElement, CustomViewer
from glue import custom_viewer

class HiddenComponentElement(ComponentElement):

    """
    A dropdown selector to choose a component that also recognizes hidden
    components

    The shorthand notation is 'atth'::

        e = FormElement.auto('atth')
    """

    @classmethod
    def recognizes(cls, params):
        return params == 'atth'
    
    def _list_components(self):
        comps = list(set([c for l in self.container.layers
                          for c in l.data.components]))
        comps = sorted(comps, key=lambda x: x.label)
        return comps

class ContourPlot(CustomViewer):
    name = 'Contour Viewer'
    x = 'atth'
    y = 'atth'
    z = 'att'
    nlevels = (5, 100, 31)

    def plot_data(self, axes, x, y, z, nlevels):
        try:
            axes.set_xlabel(x.id.label)
            axes.set_ylabel(y.id.label)

            axes.contourf(x, y, z, nlevels, origin='image')
            axes.contour(x, y, z, nlevels, origin='image')
            axes.relim()
        except AttributeError as e:
            pass

def mock_data():
    '''temporary file loader for testing contour plot and nd file viewer'''
    import numpy as np
    from functools import partial
    from glue.core.data import Data
    from glue.core.coordinates import LUTCoordinates

    SHAPE = (100, 1340)
    tstart, tend = -200, 600e3
    wlstart, wlend = 620, 720
    gaussian = lambda sigma, x: np.exp(-(x/sigma)**2)
    exp_decay = lambda tau, x: np.exp(-x.clip(min=0)/tau)
    sigmoid = lambda tau, x: 1/(1 + np.exp(-x/tau))
    risetime = lambda tau, lim, x: np.piecewise(x, 
            [np.abs(x/tau) < lim, x/tau <= -lim, x/tau >= lim], 
            [partial(sigmoid, tau), lambda x: 0., lambda x: 1])

    idx = np.linspace(1.01, 0.01, SHAPE[0])
    nonlinear_spacing = lambda start, stop, idx: stop*(idx[-1]/idx - 
            idx[-1]/idx[0]) + start

    population_time = nonlinear_spacing(tstart, tend, idx)
    wavelength = wl = np.linspace(wlstart, wlend, SHAPE[1])

    # simulate data
    spectrum = gaussian(10, wl-650) + gaussian(25, wl-680)
    kinetics = risetime(10, 10, population_time)*exp_decay(1e5,
            population_time) 
    image = np.outer(kinetics, spectrum)

    print("Image shape: ", image.shape)
    c = [('population time', population_time), ('wavelength',
        wavelength)][::-1]
    coords = LUTCoordinates(*c)
    data = Data(label='Mock Kinetics', kinetics=image, coords=coords)
    return data

def plugin(session, data_collection):
    print("ran mock_kinetics")
    data = mock_data()
    data_collection.append(data)

def setup():
    print("in mock_kinetics setup")
    try:
        from h5py import File
    except ImportError:
        raise ImportError('h5py is required')
    else:
        from glue.config import menubar_plugin
        from glue.config import qt_client

        menubar_plugin.add('mock kinetics', plugin)
        print("loaded mock kinetics")
