import os
from PIL import Image


class TileSet:
    def __init__(self, im_paths):
        # Assumes '{x}_{y}' naming convention for files
        self._tiles = {}
        for fp in im_paths:
            name, _ = os.path.splitext(os.path.basename(fp))
            x, y = map(int, name.split('_'))
            if y not in self._tiles:
                self._tiles[y] = {}
            self._tiles[y][x] = fp

    def tile_dims(self):
        # Assume all tiles are the same dimensions
        # so just open the first tile and get its dimensions
        im = Image.open(self._tiles[0][0])
        return im.width, im.height

    def dims(self):
        # Assume all rows have the same number of tiles
        n_tiles_y = max(self._tiles.keys()) + 1
        n_tiles_x = len(self._tiles[0])
        return n_tiles_x, n_tiles_y

    def __getitem__(self, pos):
        x, y = pos
        return self._tiles[y][x]

    def tiles(self):
        n_tiles_y, _ = self.tile_dims()
        for y in range(n_tiles_y):
            for x in sorted(self._tiles[y].keys()):
                yield (x, y), self._tiles[y][x]
