import numpy as np
from numpy.testing import assert_allclose

from glue.core.application_base import Application
from glue.core.data import Data
from glue.core.link_helpers import LinkSame
from glue.viewers.scatter.viewer import SimpleScatterViewer
from glue.viewers.profile.viewer import SimpleProfileViewer
from glue.viewers.histogram.viewer import SimpleHistogramViewer
from glue.viewers.image.viewer import SimpleImageViewer
from glue.viewers.matplotlib.vertical_lines import (VerticalLineLayerArtist,
                                                    add_vertical_lines)


def make_lines_app(main_data, link_cid):
    app = Application()
    lines = Data(position=[1., 3., 2., 3.], label='lines')
    app.data_collection.append(main_data)
    app.data_collection.append(lines)
    app.data_collection.add_link(LinkSame(lines.id['position'], link_cid))
    return app, lines


def assert_positions(artist, expected):
    segments = artist.vline_collection.get_segments()
    assert_allclose([s[0][0] for s in segments], expected)


def test_scatter_viewer():

    data = Data(x=[1., 2., 3., 4.], y=[4., 5., 6., 7.], label='data')
    app, lines = make_lines_app(data, data.id['x'])

    viewer = app.new_data_viewer(SimpleScatterViewer)
    viewer.add_data(data)

    artist = add_vertical_lines(viewer, lines)

    assert isinstance(artist, VerticalLineLayerArtist)
    assert artist.enabled
    # Values are unique-d and sorted
    assert_positions(artist, [1, 2, 3])
    assert artist.vline_collection.get_transform() is viewer.axes.get_xaxis_transform()

    # If the x attribute changes to one that cannot be resolved for the
    # layer, the layer is disabled, and re-enabled when changing back
    viewer.state.x_att = data.id['y']
    assert not artist.enabled
    viewer.state.x_att = data.id['x']
    assert artist.enabled
    assert_positions(artist, [1, 2, 3])


def test_profile_viewer():

    spectrum = Data(flux=np.random.random(10), label='spectrum')
    app, lines = make_lines_app(spectrum, spectrum.pixel_component_ids[0])

    viewer = app.new_data_viewer(SimpleProfileViewer)
    viewer.add_data(spectrum)

    artist = add_vertical_lines(viewer, lines)

    assert artist.enabled
    assert_positions(artist, [1, 2, 3])

    # Subsets created after the fact follow the parent dataset and are also
    # shown as vertical lines. Note that the subset group is global, so the
    # spectrum subset is added too, as a regular profile layer.
    app.data_collection.new_subset_group(label='high', subset_state=lines.id['position'] > 1.5)

    subset_artists = [layer for layer in viewer.layers
                      if isinstance(layer, VerticalLineLayerArtist)
                      and layer.layer is not lines]
    assert len(subset_artists) == 1
    assert subset_artists[0].layer.data is lines
    assert subset_artists[0].enabled
    assert_positions(subset_artists[0], [2, 3])

    # Removing the data removes the vertical line layers
    viewer.remove_data(lines)
    assert not any(isinstance(layer, VerticalLineLayerArtist) for layer in viewer.layers)


def test_histogram_viewer():

    data = Data(values=[1., 1., 2., 3., 5., 8.], label='data')
    app, lines = make_lines_app(data, data.id['values'])

    viewer = app.new_data_viewer(SimpleHistogramViewer)
    viewer.add_data(data)

    artist = add_vertical_lines(viewer, lines)

    assert artist.enabled
    assert_positions(artist, [1, 2, 3])


def test_image_viewer():

    image = Data(intensity=np.random.random((5, 5)), label='image')
    app, lines = make_lines_app(image, image.pixel_component_ids[1])

    viewer = app.new_data_viewer(SimpleImageViewer)
    viewer.add_data(image)

    artist = add_vertical_lines(viewer, lines)

    assert artist.enabled
    assert_positions(artist, [1, 2, 3])


def test_existing_subsets_added():

    spectrum = Data(flux=np.random.random(10), label='spectrum')
    app, lines = make_lines_app(spectrum, spectrum.pixel_component_ids[0])

    app.data_collection.new_subset_group(label='high', subset_state=lines.id['position'] > 1.5)

    viewer = app.new_data_viewer(SimpleProfileViewer)
    viewer.add_data(spectrum)

    add_vertical_lines(viewer, lines)

    vline_artists = [layer for layer in viewer.layers
                     if isinstance(layer, VerticalLineLayerArtist)]
    assert len(vline_artists) == 2
    assert vline_artists[1].layer.data is lines
    assert_positions(vline_artists[1], [2, 3])


def test_styling():

    data = Data(x=[1., 2., 3.], y=[4., 5., 6.], label='data')
    app, lines = make_lines_app(data, data.id['x'])

    lines.style.color = '#ff0000'

    viewer = app.new_data_viewer(SimpleScatterViewer)
    viewer.add_data(data)
    artist = add_vertical_lines(viewer, lines)

    assert artist.state.color == '#ff0000'

    artist.state.linewidth = 3
    assert artist.vline_collection.get_linewidth()[0] == 3

    artist.state.visible = False
    assert not artist.vline_collection.get_visible()
