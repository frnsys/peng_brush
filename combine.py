import os
import math
from PIL import Image
from .tiles import TileSet

# Generate side-by-side images of two tilesets
# for training pix2pix
def combine_images(im_paths_a, im_paths_b, outdir):
    ts_a = TileSet(im_paths_a)
    ts_b = TileSet(im_paths_b)

    # Assert same number of tiles in each axis
    assert ts_a.dims() == ts_b.dims()

    # Assert that aspect ratio is the same for each tile
    tile_dims_a = ts_a.tile_dims()
    tile_dims_b = ts_b.tile_dims()
    assert tile_dims_a[0]/tile_dims_a[1] == tile_dims_b[0]/tile_dims_b[1]

    if tile_dims_a != tile_dims_b:
        # Need to scale images.
        # Scale the larger one down
        tile_size_a = tile_dims_a[0] * tile_dims_a[1]
        tile_size_b = tile_dims_b[0] * tile_dims_b[1]
        if tile_size_a > tile_size_b:
            scale_b = 1.
            scale_a = math.sqrt(tile_size_b/tile_size_a)
        else:
            scale_a = 1.
            scale_b = math.sqrt(tile_size_a/tile_size_b)
    else:
        scale_a = scale_b = 1.

    dims_a = (tile_dims_a[0] * scale_a, tile_dims_a[1] * scale_a)
    dims_b = (tile_dims_b[0] * scale_b, tile_dims_b[1] * scale_b)

    im_dims = (dims_a[0] * 2, dims_b[1])
    for (x, y), tile_path in ts_a.tiles:
        im_a = Image.open(tile_path)
        im_b = Image.open(ts_b[x,y])
        if scale_a != 1.:
            im_a = im_a.resize(dims_a, Image.LANCZOS)
        if scale_b != 1.:
            im_b = im_b.resize(dims_b, Image.LANCZOS)

        im = Image.new('RGB', im_dims)
        im.paste(im_a)
        im.paste(im_b, box=(dims_a[0], 0))

        outpath = os.path.join(outdir, '{}_{}.jpg'.format(x, y))
        im.save(outpath, quality=95, subsampling=0)
