from PIL import Image
from .tiles import TileSet

# Merge tiles into a single image,
# for debugging
def stitch(im_paths, outpath):
    ts = TileSet(im_paths)
    n_tiles_x, n_tiles_y = ts.dims()
    tile_w, tile_h = ts.tile_dims()

    im_dims = (n_tiles_x * tile_w, n_tiles_y * tile_h)
    im = Image.new('RGB', im_dims)
    for (j, i), tile_path in ts.tiles:
        y = i * tile_h
        x = j * tile_w
        tile_im = Image.open(tile_path)
        im.paste(tile_im, (x, y))

    im.save(outpath, quality=95, subsampling=0)


if __name__ == '__main__':
    from glob import glob

    im_paths = glob('data/vec/manhattan/*.jpg')
    stitch(im_paths, 'vec.jpg')

    im_paths = glob('data/sat/manhattan/*.jpg')
    stitch(im_paths, 'sat.jpg')
