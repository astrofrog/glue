from __future__ import absolute_import, division, print_function

import uuid
import numpy as np

from glue.utils import defer_draw

from glue.external.modest_image import imshow
from glue.viewers.image_new.state import ImageLayerState
from glue.viewers.matplotlib.layer_artist import MatplotlibLayerArtist
from glue.core.exceptions import IncompatibleAttribute
from glue.viewers.image_new.composite_array import CompositeArray
from glue.utils import color2rgb


class ImageLayerArtist(MatplotlibLayerArtist):

    _layer_state_cls = ImageLayerState

    def __init__(self, axes, viewer_state, layer_state=None, layer=None):

        super(ImageLayerArtist, self).__init__(axes, viewer_state,
                                               layer_state=layer_state, layer=layer)

        # Watch for changes in the viewer state which would require the
        # layers to be redrawn
        self._viewer_state.add_global_callback(self._update_image)
        self.state.add_global_callback(self._update_image)

        # TODO: following is temporary
        self.state.data_collection = self._viewer_state.data_collection
        self.data_collection = self._viewer_state.data_collection

        # We use a custom object to deal with the compositing of images, and we
        # store it as a private attribute of the axes to make sure it is
        # accessible for all layer artists.
        self.uuid = str(uuid.uuid4())
        if hasattr(self.axes, '_composite'):
            self.composite = self.axes._composite
            do_imshow = False
        else:
            self.composite = CompositeArray(self.axes)
            self.axes._composite = self.composite
            do_imshow = True
        self.composite.allocate(self.uuid)
        self.composite.set(self.uuid, array=np.zeros(self.layer.shape[:2]))

        if do_imshow:
            self.composite_image = imshow(self.axes, self.composite, origin='lower', interpolation='nearest')
            self.axes._composite_image = self.composite_image
            self.axes.set_xlim(-0.5, self.composite.shape[1] - 0.5)
            self.axes.set_ylim(-0.5, self.composite.shape[0] - 0.5)
        else:
            self.composite_image = self.axes._composite_image

        self.reset_cache()

    def reset_cache(self):
        self._last_viewer_state = {}
        self._last_layer_state = {}

    def _update_image_data(self):

        try:
            image = self.layer[self.state.attribute]
        except (IncompatibleAttribute, IndexError):
            # The following includes a call to self.clear()
            self.disable_invalid_attributes(self.state.attribute)
            return
        else:
            self._enabled = True

        if image.ndim > 2:
            image = image[self._viewer_state.numpy_slice]

        self.composite.set(self.uuid, array=image)

        self.composite_image.invalidate_cache()

        self.redraw()

    @defer_draw
    def _update_visual_attributes(self):

        self.composite.set(self.uuid,
                           clim=(self.state.v_min, self.state.v_max),
                           visible=self.state.visible,
                           zorder=self.state.zorder,
                           color=self.state.color,
                           contrast=self.state.contrast,
                           bias=self.state.bias,
                           alpha=self.state.alpha)

        self.composite_image.invalidate_cache()

        self.redraw()

    def _update_image(self, force=False, **kwargs):

        if (self.state.attribute is None or
            self.state.layer is None):
            return

        # Figure out which attributes are different from before. Ideally we shouldn't
        # need this but currently this method is called multiple times if an
        # attribute is changed due to x_att changing then hist_x_min, hist_x_max, etc.
        # If we can solve this so that _update_histogram is really only called once
        # then we could consider simplifying this. Until then, we manually keep track
        # of which properties have changed.

        changed = set()

        if not force:

            for key, value in self._viewer_state.as_dict().items():
                if value != self._last_viewer_state.get(key, None):
                    changed.add(key)

            for key, value in self.state.as_dict().items():
                if value != self._last_layer_state.get(key, None):
                    changed.add(key)

        self._last_viewer_state.update(self._viewer_state.as_dict())
        self._last_layer_state.update(self.state.as_dict())

        print('CHANGED', changed)

        if force or any(prop in changed for prop in ('layer', 'attribute', 'slices')):
            self._update_image_data()
            force = True  # make sure scaling and visual attributes are updated

        if force or any(prop in changed for prop in ('v_min', 'v_max', 'contrast', 'bias', 'alpha', 'color', 'zorder', 'visible')):
            self._update_visual_attributes()

    @defer_draw
    def update(self):

        self._update_image(force=True)

        # Reset the axes stack so that pressing the home button doesn't go back
        # to a previous irrelevant view.
        self.axes.figure.canvas.toolbar.update()

        self.redraw()


class ImageSubsetLayerArtist(MatplotlibLayerArtist):

    _layer_state_cls = ImageLayerState

    def __init__(self, axes, viewer_state, layer_state=None, layer=None):

        super(ImageLayerArtist, self).__init__(axes, viewer_state,
                                               layer_state=layer_state, layer=layer)

        # Watch for changes in the viewer state which would require the
        # layers to be redrawn
        self._viewer_state.add_global_callback(self._update_image)
        self.state.add_global_callback(self._update_image)

        # TODO: following is temporary
        self.state.data_collection = self._viewer_state.data_collection
        self.data_collection = self._viewer_state.data_collection

        self.mpl_image = self.axes.imshow(np.zeros(self.layer.shape + (4,)),
                                          origin='lower', interpolation='nearest', vmin=0, vmax=1)
        self.axes.set_xlim(-0.5, self.layer.shape[1] - 0.5)
        self.axes.set_ylim(-0.5, self.layer.shape[0] - 0.5)

        self.reset_cache()

    def reset_cache(self):
        self._last_viewer_state = {}
        self._last_layer_state = {}

    def _update_image_data(self):

        try:
            mask = self.layer.to_mask()
        except (IncompatibleAttribute, IndexError):
            # The following includes a call to self.clear()
            self.disable_invalid_attributes(self.state.attribute)
            return
        else:
            self._enabled = True

        r, g, b = color2rgb(self.state.color)
        mask = np.dstack((r * mask, g * mask, b * mask, mask * .5))
        mask = (255 * mask).astype(np.uint8)

        self.mpl_image.set_data(mask)

        self.composite_image.invalidate_cache()

        self.redraw()

    @defer_draw
    def _update_visual_attributes(self):

        self.mpl_image.set_visible(self.state.visible)
        self.mpl_image.set_zorder(self.state.zorder)

        self.composite_image.invalidate_cache()

        self.redraw()

    def _update_image(self, force=False, **kwargs):

        if (self.state.attribute is None or
            self.state.layer is None):
            return

        # Figure out which attributes are different from before. Ideally we shouldn't
        # need this but currently this method is called multiple times if an
        # attribute is changed due to x_att changing then hist_x_min, hist_x_max, etc.
        # If we can solve this so that _update_histogram is really only called once
        # then we could consider simplifying this. Until then, we manually keep track
        # of which properties have changed.

        changed = set()

        if not force:

            for key, value in self._viewer_state.as_dict().items():
                if value != self._last_viewer_state.get(key, None):
                    changed.add(key)

            for key, value in self.state.as_dict().items():
                if value != self._last_layer_state.get(key, None):
                    changed.add(key)

        self._last_viewer_state.update(self._viewer_state.as_dict())
        self._last_layer_state.update(self.state.as_dict())

        if force or any(prop in changed for prop in ('layer', 'attribute')):
            self._update_image_data()
            force = True  # make sure scaling and visual attributes are updated

        if force or any(prop in changed for prop in ('zorder', 'visible')):
            self._update_visual_attributes()

    @defer_draw
    def update(self):

        self._update_image(force=True)

        # Reset the axes stack so that pressing the home button doesn't go back
        # to a previous irrelevant view.
        self.axes.figure.canvas.toolbar.update()

        self.redraw()