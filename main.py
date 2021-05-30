# <https://pyrosm.readthedocs.io/en/latest/basics.html>
#
# See what data is available:
#   from pyrosm.data import sources
#   print(sources.cities.available)
# Alternatively, use <http://download.geofabrik.de>,
# but those regions may be too large

# CRS is WGS84/EPS4326
# Use this to find a bbox: <http://bboxfinder.com>

import os
import math
import pyrosm
import pyproj
from PIL import Image
from functools import partial
from shapely.geometry import box
from shapely.ops import transform
from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt

TILE_SIZE = 500 # in meters
PX_PER_METER = 2

ROAD_COLOR = '#ff0000'
BLDG_COLOR = '#00ff00'
LAND_COLORS = {
    'grass': '#43CC70',
    'forest': '#274230',
    'industrial': '#6e3008',
}
DEFAULT_LAND_COLOR = '#ffffff'
FEAT_COLORS = {
    'water': '#0000ff',
}
DEFAULT_FEAT_COLOR = '#fffff'

proj = partial(pyproj.transform,
        pyproj.CRS('epsg:4326'),
        pyproj.CRS('epsg:3857'), always_xy=True)

inv_proj = partial(pyproj.transform,
        pyproj.CRS('epsg:3857'),
        pyproj.CRS('epsg:4326'), always_xy=True)


def generate_tiles(name, datapath, bbox):
    bbox = box(*bbox)

    # Project to meters
    bbox_m = transform(proj, bbox)

    # Figure out image dimensions
    bounds_m = bbox_m.bounds
    width_m = bounds_m[2] - bounds_m[0]
    height_m = bounds_m[3] - bounds_m[1]
    width_px = round(width_m * PX_PER_METER)
    height_px = round(height_m * PX_PER_METER)
    tile_size_px = TILE_SIZE * PX_PER_METER

    # Adjust bounds so we have an integer number of tiles
    adj_width_px = math.ceil(width_px/tile_size_px) * tile_size_px
    adj_height_px = math.ceil(height_px/tile_size_px) * tile_size_px
    adj_width_m = adj_width_px/PX_PER_METER
    adj_height_m = adj_height_px/PX_PER_METER
    width_adj = adj_width_m - width_m
    height_adj = adj_height_m - height_m
    adj_bounds_m = (
        bounds_m[0] - width_adj/2,
        bounds_m[1] - height_adj/2,
        bounds_m[2] + width_adj/2,
        bounds_m[3] + height_adj/2
    )
    adj_bbox_m = box(*adj_bounds_m)
    adj_bbox = transform(inv_proj, adj_bbox_m)

    fig_size = (adj_width_px/100, adj_height_px/100) # default DPI is 100

    # Load OSM data in the specified bounding box
    osm = pyrosm.OSM(datapath, bounding_box=adj_bbox)

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
        landuse = osm.get_landuse()
    except KeyError:
        landuse = None
    if landuse is not None:
        labels = list(landuse.landuse.unique())
        print('Landuse labels:', labels)
        colors = [LAND_COLORS.get(l, DEFAULT_LAND_COLOR) for l in labels]
        cmap = ListedColormap(colors)
        landuse.plot(column='landuse', ax=ax, figsize=fig_size, cmap=cmap)

    try:
        natural = osm.get_natural()
    except KeyError:
        natural = None
    if natural is not None:
        labels = list(natural.natural.unique())
        print('Natural labels:', labels)
        colors = [FEAT_COLORS.get(l, DEFAULT_FEAT_COLOR) for l in labels]
        cmap = ListedColormap(colors)
        natural.plot(column='natural', ax=ax, figsize=fig_size, cmap=cmap)

    # Road networks
    drive_net = osm.get_network(network_type='driving+service')
    if drive_net is not None:
        drive_net.plot(ax=ax, color=ROAD_COLOR, figsize=fig_size)

    # Buildings
    buildings = osm.get_buildings()
    if buildings is not None:
        buildings.plot(ax=ax, color=BLDG_COLOR, figsize=fig_size)

    # Remove axes, margins, and other whitespace
    ax.margins(0)
    ax.apply_aspect()

    # Draw figure and then break into tiles
    fig.canvas.draw()
    temp_canvas = fig.canvas
    plt.close()
    img = Image.frombytes('RGB',
            temp_canvas.get_width_height(), temp_canvas.tostring_rgb())

    # Check that the image is the expected size
    width = img.width
    height = img.height
    assert(width == adj_width_px)
    assert(height == adj_height_px)

    output_dir = 'data/tiles/{}'.format(name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Split into tiles
    for i in range(int(height/tile_size_px)):
        y = i * tile_size_px
        for j in range(int(width/tile_size_px)):
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



if __name__ == '__main__':
    # fp = 'data/new-york-latest.osm.pbf'
    fp = pyrosm.get_data('NewYorkCity')

    # Smaller, for testing
    # bbox = [-74.005623,40.739417,-73.939362,40.806791]

    # Most of NYC
    bbox = [-74.100037,40.652908,-73.828812,40.867297]

    generate_tiles('nyc', fp, bbox)
