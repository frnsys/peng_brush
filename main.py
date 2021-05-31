# <https://pyrosm.readthedocs.io/en/latest/basics.html>
#
# See what data is available:
#   from pyrosm.data import sources
#   print(sources.cities.available)
# Alternatively, use <http://download.geofabrik.de>,
# but those regions may be too large

# CRS is WGS84/EPSG4326
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

TILE_SIZE_M = 2000 # in meters
METERS_PER_PX = 10

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
DEFAULT_FEAT_COLOR = '#ffffff'

proj = partial(pyproj.transform,
        pyproj.CRS('epsg:4326'),
        pyproj.CRS('epsg:3857'), always_xy=True)

inv_proj = partial(pyproj.transform,
        pyproj.CRS('epsg:3857'),
        pyproj.CRS('epsg:4326'), always_xy=True)

def bbox_to_dim_meters(bounds):
    bbox = box(*bounds)

    # Project to meters
    bbox_m = transform(proj, bbox)
    bounds_m = bbox_m.bounds
    width_m = bounds_m[2] - bounds_m[0]
    height_m = bounds_m[3] - bounds_m[1]
    return bounds_m, (width_m, height_m)

# Adjust the given bounding box so that
# it produces a round (integer) number of tiles
def fit_bbox_to_tiles(bounds, tile_size_m):
    bounds_m, (width_m, height_m) = bbox_to_dim_meters(bounds)

    n_x_tiles = math.ceil(width_m/tile_size_m)
    n_y_tiles = math.ceil(height_m/tile_size_m)
    adj_width_m = n_x_tiles * tile_size_m
    adj_height_m = n_y_tiles * tile_size_m
    width_adj = adj_width_m - width_m
    height_adj = adj_height_m - height_m
    adj_bounds_m = (
        bounds_m[0] - width_adj/2,
        bounds_m[1] - height_adj/2,
        bounds_m[2] + width_adj/2,
        bounds_m[3] + height_adj/2
    )
    adj_bbox_m = box(*adj_bounds_m)
    return transform(inv_proj, adj_bbox_m)

def bbox_to_pixels(bounds, meters_per_px):
    bounds_m, (width_m, height_m) = bbox_to_dim_meters(bounds)
    width_px = math.ceil(width_m/meters_per_px)
    height_px = math.ceil(height_m/meters_per_px)
    return width_px, height_px

def tileize(bounds, tile_size_m):
    adj_bbox = fit_bbox_to_tiles(bounds, tile_size_m)
    bounds_m, (width_m, height_m) = bbox_to_dim_meters(adj_bbox.bounds)

    for i in range(round(height_m/tile_size_m)):
        y = bounds_m[1] + (i * tile_size_m)
        for j in range(round(width_m/tile_size_m)):
            x = bounds_m[0] + (j * tile_size_m)
            bounds_ = (x, y, x + tile_size_m, y + tile_size_m)
            yield (j, i), transform(inv_proj, box(*bounds_)).bounds


def generate_tiles(name, datapath, bounds):
    adj_bbox = fit_bbox_to_tiles(bounds, TILE_SIZE_M)
    width_px, height_px = bbox_to_pixels(adj_bbox.bounds, METERS_PER_PX)

    fig_size = (width_px/100, width_px/100) # default DPI is 100
    print('Image dimensions:', (width_px, height_px))
    # import ipdb; ipdb.set_trace()

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
        print('Getting landuse...')
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
        print('Getting natural features...')
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
    output_dir = 'data/vec/{}'.format(name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Split into tiles
    tile_size_px = TILE_SIZE_M/METERS_PER_PX

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


def maskS2clouds(image):
  # Bits 10 and 11 are clouds and cirrus, respectively.
  cloudBitMask = (1 << 10)
  cirrusBitMask = (1 << 11)

  qa = image.select('QA60')

  # Both flags should be set to zero, indicating clear conditions.
  mask = qa.bitwiseAnd(cloudBitMask).eq(0)\
          .And(qa.bitwiseAnd(cirrusBitMask).eq(0))

  return image.updateMask(mask).divide(10000)


if __name__ == '__main__':
    import ee
    from peng.satellite import Satellite

    # fp = 'data/new-york-latest.osm.pbf'
    # fp = 'data/north-america-latest.osm.pbf'
    fp = 'data/us-northeast-latest.osm.pbf'
    # fp = pyrosm.get_data('NewYorkCity')

    bbox = [-74.023819,40.695666,-73.927689,40.814578]
    bbox = [-74.005108,40.740937,-73.972578,40.754599]

    # source = {
    #     'name': 'COPERNICUS/S2_SR',
    #     'bands': {
    #         'B4': 'red', 'B3': 'green', 'B2': 'blue',
    #         'QA60': 'QA60',
    #     },
    #     'range': (0.0, 0.3),
    #     'process': lambda col: col.filterDate('2018-01-01', '2020-01-30').filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)).map(maskS2clouds)
    # }
    # sat = Satellite(img_source=source)
    # for (x, y), tile_bbox in tileize(bbox, TILE_SIZE_M):
    #     # <https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR>
    #     adj_tile_bbox = [tile_bbox[1], tile_bbox[0], tile_bbox[3], tile_bbox[2]]
    #     image, params = sat.get_area_image(adj_tile_bbox, scale=10)
    #     params['crs'] = 'epsg:4326'
    #     sat.download_image(image, params, 'data/sat/manhattan/{}_{}.jpg'.format(x, y))

    generate_tiles('manhattan', fp, bbox)
