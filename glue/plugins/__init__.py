def load_all_plugins():
    """
    Load built-in plugins
    """

    from .ginga_viewer import load_ginga_viewer_plugin
    load_ginga_viewer_plugin()

    from .coordinate_helpers import load_coordinate_helpers_plugin
    load_coordinate_helpers_plugin()

    from . import export_d3po

    from . import export_plotly
