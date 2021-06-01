# <https://pyrosm.readthedocs.io/en/latest/basics.html>
#
# See what data is available:
#   from pyrosm.data import sources
#   print(sources.cities.available)
# Alternatively, use <http://download.geofabrik.de>,
# but those regions may be too large

# CRS for OSM data is WGS84/EPSG4326

import os
import util
import pyrosm
from PIL import Image
from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt


ROAD_COLOR = '#000000'
BLDG_COLOR = '#ff0000'
LAND_COLORS = {
    # 'grass': '#43CC70',
    # 'forest': '#274230',
    # 'industrial': '#6e3008',
}
# DEFAULT_LAND_COLOR = '#ffffff'
DEFAULT_LAND_COLOR = '#666666'
FEAT_COLORS = {
    # 'water': '#0000ff',
}
# DEFAULT_FEAT_COLOR = '#ffffff'
DEFAULT_FEAT_COLOR = '#222222'


def generate_vec_tiles(name, datapath, bounds, tile_size_m, meters_per_px):
    adj_bbox = util.fit_bbox_to_tiles(bounds, tile_size_m)
    width_px, height_px = util.bbox_to_pixels(adj_bbox.bounds, meters_per_px)

    fig_size = (width_px/100, height_px/100) # default DPI is 100
    print('Image dimensions:', (width_px, height_px))
    # import ipdb; ipdb.set_trace()

    # Load OSM data in the specified bounding box
    osm = pyrosm.OSM(datapath, bounding_box=adj_bbox)

    print(osm.conf.tags.available)

    # Prepare figure
    fig = plt.figure()
    fig.set_size_inches(*fig_size)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')

    # Get landuse and natural feature data
    # View labels to see if you want to add a specific
    # color for any of them.

    # If no data or no tags associated,
    # this will be None
    try:
        print('Getting landuse...')
        landuse = osm.get_landuse()
        import ipdb; ipdb.set_trace()
    except KeyError:
        landuse = None
    if landuse is not None:
        labels = list(landuse.landuse.unique())
        print('Landuse labels:', labels)
        colors = [LAND_COLORS.get(l, DEFAULT_LAND_COLOR) for l in labels]
        cmap = ListedColormap(colors)
        landuse.plot(column='landuse', ax=ax, figsize=fig_size, cmap=cmap)

    try:
        print('Getting natural features...')
        natural = osm.get_natural()
        import ipdb; ipdb.set_trace()
    except KeyError:
        natural = None
    if natural is not None:
        labels = list(natural.natural.unique())
        print('Natural labels:', labels)
        colors = [FEAT_COLORS.get(l, DEFAULT_FEAT_COLOR) for l in labels]
        cmap = ListedColormap(colors)
        natural.plot(column='natural', ax=ax, figsize=fig_size, cmap=cmap)

    # Road networks
    print('Getting road network...')
    drive_net = osm.get_network(network_type='driving+service')
    if drive_net is not None:
        drive_net.plot(ax=ax, color=ROAD_COLOR, figsize=fig_size)

    # Buildings
    print('Getting buildings...')
    buildings = osm.get_buildings()
    if buildings is not None:
        buildings.plot(ax=ax, color=BLDG_COLOR, figsize=fig_size)

    # Remove axes, margins, and other whitespace
    ax.margins(0)
    ax.apply_aspect()

    # Draw figure and then break into tiles
    print('Generating plot...')
    fig.canvas.draw()
    temp_canvas = fig.canvas
    plt.close()

    print('Generating tiles...')
    img = Image.frombytes('RGB',
            temp_canvas.get_width_height(), temp_canvas.tostring_rgb())
    width = img.width
    height = img.height

    print('Creating tiles...')
    output_dir = 'data/{}/vec'.format(name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Split into tiles
    tile_size_px = tile_size_m/meters_per_px

    for i in range(round(height/tile_size_px)):
        y = i * tile_size_px
        for j in range(round(width/tile_size_px)):
            x = j * tile_size_px
            tile = img.crop((x, y, x + tile_size_px, y + tile_size_px))
            tile.save(
                    os.path.join(output_dir, '{}_{}.jpg'.format(j, i)),
                    quality=95, subsampling=0)

    # Palette, for reference
    print('Palette')
    print(' road:', ROAD_COLOR)
    print(' building:', BLDG_COLOR)
    for key, color in LAND_COLORS.items():
        print(' {}:'.format(key), color)
    for key, color in FEAT_COLORS.items():
        print(' {}:'.format(key), color)

    return output_dir
