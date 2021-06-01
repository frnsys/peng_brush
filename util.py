import math
import pyproj
from functools import partial
from shapely.geometry import box
from shapely.ops import transform

proj = partial(pyproj.transform,
        pyproj.CRS('epsg:4326'),
        pyproj.CRS('epsg:3857'), always_xy=True)

inv_proj = partial(pyproj.transform,
        pyproj.CRS('epsg:3857'),
        pyproj.CRS('epsg:4326'), always_xy=True)


# Convert a EPSG:4326 bounding box
# into EPSG:3857 (i.e. meters)
def bbox_to_dim_meters(bounds):
    bbox = box(*bounds)
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


# Calculate the pixel size of a given
# EPSG:4326 bounding box for a given meter resolution
def bbox_to_pixels(bounds, meters_per_px):
    bounds_m, (width_m, height_m) = bbox_to_dim_meters(bounds)
    width_px = math.ceil(width_m/meters_per_px)
    height_px = math.ceil(height_m/meters_per_px)
    return width_px, height_px

def tile_dims(bounds, tile_size_m):
    adj_bbox = fit_bbox_to_tiles(bounds, tile_size_m)
    bounds_m, (width_m, height_m) = bbox_to_dim_meters(adj_bbox.bounds)
    return round(width_m/tile_size_m), round(height_m/tile_size_m)

# Break a given EPSG:4326 bounding box into
# tiles of a given meter size
def tileize(bounds, tile_size_m):
    adj_bbox = fit_bbox_to_tiles(bounds, tile_size_m)
    bounds_m, (width_m, height_m) = bbox_to_dim_meters(adj_bbox.bounds)
    for i in range(round(height_m/tile_size_m)):
        y = bounds_m[1] + (i * tile_size_m)
        for j in range(round(width_m/tile_size_m)):
            x = bounds_m[0] + (j * tile_size_m)
            bounds_ = (x, y, x + tile_size_m, y + tile_size_m)
            yield (j, i), transform(inv_proj, box(*bounds_)).bounds
