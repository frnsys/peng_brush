# Use this to find a bbox: <http://bboxfinder.com>

import os
from PIL import Image
from glob import glob
from img import combine_images
from peng.util import download

TILE_SIZE_M = 500 # in meters
METERS_PER_PX = 1

# Set this env var first
# Token needs `styles:tiles` scope
# <https://docs.mapbox.com/api/maps/static-images/>
ACCESS_TOKEN = os.getenv('PENG_BRUSH_MAPBOX_TOKEN')

if ACCESS_TOKEN is None:
    raise Exception('Please set the PENG_BRUSH_MAPBOX_TOKEN env var')

# Edit styles in studio.mapbox.com
# to change colors/what features are included
username = 'jfift'
sat_style_id = 'ckpdfsmn00tj417pdztwm94s6'
vec_style_id = 'ckpde82g7164c17nzcsb7yxhx'
tiles_url = 'https://api.mapbox.com/styles/v1/{username}/{style_id}/static/{bbox}/{width}x{height}'

# bbox should be EPSG:4326
def get_image(bbox, typ, dims, outpath):
    bottom_padding = 25

    if typ == 'sat':
        style_id = sat_style_id
    elif typ == 'vec':
        style_id = vec_style_id

    url = tiles_url.format(
        username=username,
        style_id=style_id,
        bbox=str(list(bbox)).replace(' ', ''),
        width=dims[0],
        height=dims[1]+bottom_padding)
    url = '{}?access_token={}'.format(url, ACCESS_TOKEN)
    download(url, outpath)
    Image.open(outpath)\
            .crop((0, 0, width, height))\
            .convert('RGB')\
            .save(outpath, quality=95, subsampling=0)


if __name__ == '__main__':
    import sys
    import util
    from tqdm import tqdm
    from multiprocessing import Pool

    name = sys.argv[1]
    bbox = list(map(float, sys.argv[2].split(',')))
    width = height = int(TILE_SIZE_M/METERS_PER_PX)

    outdir = 'data/{}'.format(name)
    if os.path.exists(outdir):
        print('Output directory already exists. Skipping tile download.')
        print('Remove output directory to re-download.')
    else:
        print('Downloading tiles...')
        os.makedirs(outdir)
        os.makedirs(os.path.join(outdir, 'sat'))
        os.makedirs(os.path.join(outdir, 'vec'))
        os.makedirs(os.path.join(outdir, 'train'))

        def fn(inp):
            (x, y), bbox = inp
            for typ in ['sat', 'vec']:
                outpath = 'data/{}/{}/{}_{}.jpg'.format(name, typ, x, y)
                get_image(bbox, typ, (width, height), outpath)

        n_x, n_y = util.tile_dims(bbox, TILE_SIZE_M)
        n_tiles = n_x * n_y
        tile_iter = tqdm(util.tileize(bbox, TILE_SIZE_M), total=n_tiles)
        with Pool(4) as p:
            list(p.imap(fn, tile_iter))

    print('Combining tiles...')
    combine_images(
            glob('data/{}/vec/*.jpg'.format(name)),
            glob('data/{}/sat/*.jpg'.format(name)),
            'data/{}/train'.format(name))
    print('examples:', len(glob('data/{}/train'.format(name))))
