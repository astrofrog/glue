from . import export_d3po
from . import export_plotly


def load_all_plugins():
    """
    Load built-in plugins
    """

    from .ginga_viewer import load_ginga_viewer_plugin
    load_ginga_viewer_plugin()

from . import coordinate_helpers
