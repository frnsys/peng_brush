# Use this to find a bbox: <http://bboxfinder.com>

import pyrosm
from glob import glob
from vec import generate_vec_tiles
from sat import generate_sat_tiles
from img import combine_images

TILE_SIZE_M = 2000 # in meters
METERS_PER_PX = 10


if __name__ == '__main__':
    name = 'manhattan'
    # osm_fp = 'data/us-northeast-latest.osm.pbf'
    # osm_fp = 'data/new-york-latest.osm.pbf'
    # osm_fp = 'data/north-america-latest.osm.pbf'
    osm_fp = pyrosm.get_data('NewYorkCity')

    # bbox = [-74.005108,40.740937,-73.972578,40.754599]
    bbox = [-74.025879,40.693010,-73.888550,40.839218]

    print('Generating vector tiles...')
    # generate_vec_tiles(name, osm_fp, bbox, TILE_SIZE_M, METERS_PER_PX)

    print('Generating satellite tiles...')
    # generate_sat_tiles(name, bbox, TILE_SIZE_M)

    print('Combining tiles...')
    combine_images(
            glob('data/{}/vec/*.jpg'.format(name)),
            glob('data/{}/sat/*.jpg'.format(name)),
            'data/{}/train'.format(name))
