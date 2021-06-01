import os
import math
from PIL import Image
from tiles import TileSet


# Generate side-by-side images of two tilesets
# for training pix2pix
def combine_images(im_paths_a, im_paths_b, outdir):
    ts_a = TileSet(im_paths_a)
    ts_b = TileSet(im_paths_b)

    # Assert same number of tiles in each axis
    assert ts_a.dims() == ts_b.dims()

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Scale tiles as needed
    tile_dims_a = ts_a.tile_dims()
    tile_dims_b = ts_b.tile_dims()
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

    dims_a = (int(tile_dims_a[0] * scale_a), int(tile_dims_a[1] * scale_a))
    dims_b = (int(tile_dims_b[0] * scale_b), int(tile_dims_b[1] * scale_b))

    im_dims = (dims_a[0] * 2, dims_b[1])
    for (x, y), tile_path in ts_a.tiles():
        im_a = Image.open(tile_path)
        im_b = Image.open(ts_b[x, y])
        if scale_a != 1.:
            im_a = im_a.resize(dims_a, Image.LANCZOS)
        if scale_b != 1.:
            im_b = im_b.resize(dims_b, Image.LANCZOS)

        im = Image.new('RGB', im_dims)
        im.paste(im_a)
        im.paste(im_b, box=(dims_a[0], 0))

        outpath = os.path.join(outdir, '{}_{}.jpg'.format(x, y))
        im.save(outpath, quality=95, subsampling=0)


# Merge tiles into a single image,
# for debugging
def stitch(im_paths, outpath):
    ts = TileSet(im_paths)
    n_tiles_x, n_tiles_y = ts.dims()
    tile_w, tile_h = ts.tile_dims()

    im_dims = (n_tiles_x * tile_w, n_tiles_y * tile_h)
    im = Image.new('RGB', im_dims)
    for (j, i), tile_path in ts.tiles():
        y = i * tile_h
        x = j * tile_w
        tile_im = Image.open(tile_path)
        im.paste(tile_im, (x, y))

    im.save(outpath, quality=95, subsampling=0)


if __name__ == '__main__':
    from glob import glob

    im_paths = glob('data/manhattan/vec/*.jpg')
    stitch(im_paths, '/tmp/vec.jpg')

    im_paths = glob('data/manhattan/sat/*.jpg')
    stitch(im_paths, '/tmp/sat.jpg')
