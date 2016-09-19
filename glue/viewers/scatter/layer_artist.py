from __future__ import absolute_import, division, print_function

from glue.utils import nonpartial

from glue_new_viewers.scatter.state import ScatterLayerState
from glue_new_viewers.common.mpl_layer_artist import MatplotlibLayerArtist


class ScatterLayerArtist(MatplotlibLayerArtist):

    def __init__(self, layer, axes, viewer_state):

        super(ScatterLayerArtist, self).__init__(layer, axes, viewer_state)

        # Set up a state object for the layer artist
        self.layer_state = ScatterLayerState(layer=layer)
        self.viewer_state.layers.append(self.layer_state)

        # Watch for changes in the viewer state which would require the
        # layers to be redrawn
        # TODO: don't connect to ALL signals here
        # self.viewer_state.connect_all(nonpartial(self.update))
        self.viewer_state.connect('xatt', nonpartial(self.update))
        self.viewer_state.connect('yatt', nonpartial(self.update))

        self.layer_state.connect_all(nonpartial(self.update))

        # TODO: following is temporary
        self.layer_state.data_collection = self.viewer_state.data_collection
        self.data_collection = self.viewer_state.data_collection

        # Set up an initially empty artist
        # self.mpl_artist = self.axes.plot([], [], 'o', mec='none')[0]

    def update(self):

        x = self.layer[self.viewer_state.xatt[0]]
        y = self.layer[self.viewer_state.yatt[0]]

        if self.layer_state.color_mode == 'Fixed':
            c = self.layer_state.color
            vmin = vmax = cmap = None
        else:
            c = self.layer[self.layer_state.cmap_attribute[0]]
            vmin = self.layer_state.cmap_vmin
            vmax = self.layer_state.cmap_vmax
            cmap = self.layer_state.cmap

        if self.layer_state.size_mode == 'Fixed':
            s = self.layer_state.size
        else:
            s = self.layer[self.layer_state.size_attribute[0]]
            s = ((s - self.layer_state.size_vmin) /
                 (self.layer_state.size_vmax - self.layer_state.size_vmin)) * 100

        s *= self.layer_state.size_scaling

        # For plot
        # self.mpl_artist.set_data(x, y)
        # self.mpl_artist.set_color(self.color)
        # self.mpl_artist.set_markersize(self.size)

        # TODO: is there a better way to do this?
        self.clear()

        # For scatter
        self.mpl_artists = [self.axes.scatter(x, y, c=c, s=s,
                                              vmin=vmin, vmax=vmax, cmap=cmap,
                                              edgecolor='none',
                                              zorder=self.zorder,
                                              alpha=self.layer_state.alpha)]

        # Reset the axes stack so that pressing the home button doesn't go back
        # to a previous irrelevant view.
        self.axes.figure.canvas.toolbar.update()

        self.redraw()