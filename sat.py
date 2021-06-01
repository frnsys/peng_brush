import os
import ee
import util
from PIL import Image
from tqdm import tqdm
from peng.satellite import Satellite


def generate_sat_tiles(name, bounds, tile_size_m):
    output_dir = 'data/{}/sat'.format(name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # <https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR>
    source = {
        'name': 'COPERNICUS/S2_SR',
        'bands': {
            'B4': 'red', 'B3': 'green', 'B2': 'blue',
            'QA60': 'QA60',
        },
        'range': (0.0, 0.3),
        'process': lambda col: col.filterDate('2018-01-01', '2020-01-30').filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)).map(maskS2clouds)
    }
    sat = Satellite(img_source=source)
    n_x, n_y = util.tile_dims(bounds, tile_size_m)
    n_tiles = n_x * n_y
    for (x, y), tile_bbox in tqdm(util.tileize(bounds, tile_size_m), total=n_tiles):
        adj_tile_bbox = [tile_bbox[1], tile_bbox[0], tile_bbox[3], tile_bbox[2]]
        image, params = sat.get_area_image(adj_tile_bbox, scale=10)
        params['crs'] = 'epsg:4326'
        im_path = os.path.join(output_dir, '{}_{}.jpg'.format(x, y))
        sat.download_image(image, params, im_path)

        # According to <https://gis.stackexchange.com/questions/392400/raster-pixel-aspect-ratio-gets-distorted-when-exporting-from-google-earth-engine>
        # there may be some pixel warping, so re-adjust the image size to square
        im = Image.open(im_path)
        if im.width > im.height:
            size = (im.width, im.width)
        else:
            size = (im.height, im.height)
        im.resize(size, Image.LANCZOS).save(im_path, quality=95, subsampling=0)

    return output_dir


def maskS2clouds(image):
  # Bits 10 and 11 are clouds and cirrus, respectively.
  cloudBitMask = (1 << 10)
  cirrusBitMask = (1 << 11)

  qa = image.select('QA60')

  # Both flags should be set to zero, indicating clear conditions.
  mask = qa.bitwiseAnd(cloudBitMask).eq(0)\
          .And(qa.bitwiseAnd(cirrusBitMask).eq(0))

  return image.updateMask(mask).divide(10000)
