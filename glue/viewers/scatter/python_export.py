from distutils.version import LooseVersion
from matplotlib import __version__

from glue.viewers.common.python_export import code, serialize_options

MATPLOTLIB_LT_20 = LooseVersion(__version__) < LooseVersion('2.0')


def python_export_scatter_layer(layer, *args):

    if len(layer.mpl_artists) == 0 or not layer.enabled or not layer.visible:
        return [], None

    script = ""
    imports = []

    script += "# Get main data values\n"
    script += "x = layer_data['{0}']\n".format(layer._viewer_state.x_att.label)
    script += "y = layer_data['{0}']\n\n".format(layer._viewer_state.y_att.label)

    if layer.state.cmap_mode == 'Linear':

        script += "# Set up colors\n"
        script += "colors = layer_data['{0}']\n".format(layer.state.cmap_att.label)
        script += "cmap_vmin = {0}\n".format(layer.state.cmap_vmin)
        script += "cmap_vmax = {0}\n".format(layer.state.cmap_vmax)
        script += "colors = plt.cm.{0}((colors - cmap_vmin) / (cmap_vmax - cmap_vmin))\n\n".format(layer.state.cmap.name)

    if layer.state.size_mode == 'Linear':

        script += "# Set up size values\n"
        script += "sizes = layer_data['{0}']\n".format(layer.state.size_att.label)
        script += "size_vmin = {0}\n".format(layer.state.size_vmin)
        script += "size_vmax = {0}\n".format(layer.state.size_vmax)
        script += "sizes = 30 * (sizes - size_vmin) / (size_vmax - size_vmin) * {0}\n\n".format(layer.state.size_scaling)

    if MATPLOTLIB_LT_20:
        imports = ['import numpy as np']
        script += "# Due to a bug in Matplotlib 1.5 we need to filter out NaN values\n"
        script += "keep = ~np.isnan(x) & ~np.isnan(y)\n"

    if layer.state.markers_visible:
        if layer.state.density_map:
            # TODO
            pass
        else:
            if layer.state.cmap_mode == 'Fixed' and layer.state.size_mode == 'Fixed':
                options = dict(color=layer.state.color,
                               markersize=layer.state.size * layer.state.size_scaling,
                               mec='none',
                               alpha=layer.state.alpha,
                               zorder=layer.state.zorder)
                script += "ax.plot(x, y, 'o', {0})\n\n".format(serialize_options(options))
            else:
                options = dict(edgecolor='none',
                               alpha=layer.state.alpha,
                               zorder=layer.state.zorder)

                if layer.state.cmap_mode == 'Fixed':
                    options['facecolor'] = layer.state.color
                else:
                    if MATPLOTLIB_LT_20:
                        options['c'] = code('colors[keep]')
                    else:
                        options['c'] = code('colors')

                if layer.state.size_mode == 'Fixed':
                    options['s'] = code('{0} ** 2'.format(layer.state.size * layer.state.size_scaling))
                else:
                    if MATPLOTLIB_LT_20:
                        options['s'] = code('sizes[keep] ** 2')
                    else:
                        options['s'] = code('sizes ** 2')

                if MATPLOTLIB_LT_20:
                    script += "ax.scatter(x[keep], y[keep], {0})\n\n".format(serialize_options(options))
                else:
                    script += "ax.scatter(x, y, {0})\n\n".format(serialize_options(options))

    if layer.state.vector_visible:

        if layer.state.vx_att is not None and layer.state.vy_att is not None:

            script += "# Get vector data\n"
            if layer.state.vector_mode == 'Polar':
                script += "angle = layer_data['{0}']\n".format(layer.state.vx_att.label)
                script += "length = layer_data['{0}']\n".format(layer.state.vy_att.label)
                script += "vx = length * np.cos(np.radians(angle))\n"
                script += "vy = length * np.sin(np.radians(angle))\n"
            else:
                script += "vx = layer_data['{0}']\n".format(layer.state.vx_att.label)
                script += "vy = layer_data['{0}']\n".format(layer.state.vy_att.label)

        if layer.state.vector_arrowhead:
            hw = 3
            hl = 5
        else:
            hw = 1
            hl = 0

        script += 'vmax = np.nanmax(np.hypot(vx, vy))\n\n'

        scale = code('{0} * vmax'.format(10 / layer.state.vector_scaling))

        options = dict(units='width',
                       pivot=layer.state.vector_origin,
                       headwidth=hw, headlength=hl,
                       scale_units='width',
                       scale=scale,
                       alpha=layer.state.alpha,
                       zorder=layer.state.zorder)

        if layer.state.cmap_mode == 'Fixed':
            options['color'] = layer.state.color
        else:
            options['color'] = code('colors')

        script += "ax.quiver(x, y, vx, vy, {0})\n\n".format(serialize_options(options))

    if layer.state.xerr_visible or layer.state.yerr_visible:

        if layer.state.xerr_visible and layer.state.xerr_att is not None:
            xerr = code("layer_data['{0}']\n".format(layer.state.xerr_att.label))
        else:
            xerr = code("None")

        if layer.state.yerr_visible and layer.state.yerr_att is not None:
            yerr = code("layer_data['{0}']\n".format(layer.state.yerr_att.label))
        else:
            yerr = code("None")

        options = dict(fmt='none', xerr=xerr, yerr=yerr,
                       alpha=layer.state.alpha, zorder=layer.state.zorder)

        if layer.state.cmap_mode == 'Fixed':
            options['ecolor'] = layer.state.color
        else:
            options['ecolor'] = code('colors')

        script += "ax.errorbar(x, y, {0})\n\n".format(serialize_options(options))

    if layer.state.line_visible:

        options = dict(color=layer.state.color,
                       linewidth=layer.state.linewidth,
                       linestyle=layer.state.linestyle,
                       alpha=layer.state.alpha,
                       zorder=layer.state.zorder)
        if layer.state.cmap_mode == 'Fixed':
            script += "ax.plot(x, y, '-', {0})\n\n".format(serialize_options(options))
        else:
            options['c'] = code('colors')
            imports.append("from glue.viewers.scatter.layer_artist import plot_colored_line")
            script += "plot_colored_line(ax, x, y, {0})\n\n".format(serialize_options(options))

    return imports, script.strip()