# Setup

```
git submodule init
git submodule update
```

# Usage

1. First set the `PENG_BRUSH_MAPBOX_TOKEN` env var to [your Mapbox key](https://account.mapbox.com/access-tokens/). It needs to have the `styles:tiles` scope (which should be included by default).
2. Run `main.py <name> <bounding box>`, for example: `python main.py manhattan -74.025879,40.693010,-73.888550,40.839218`
    - This saves satellite tiles to `data/{name}/sat` and "vector" (label) tiles to `data/{name}/vec`
    - Training images are saved to `data/{name}/train`

# Palette

Colors used for the vector/label tiles:

- Roads: `#1A1A1A`
- Greenspace: `#00DB96`
- Land: `#FCFCFC`
- Water: `#4D4DEA`
- Buildings: `#FF0000`

These other labels/colors are used but don't really show up:

- Sand: `#FDE0AA`
- Glacier: `#A3E0F0`
- Agriculture: `#FA8900`
- Rock: `#949494`
- Wood: `#407d12`

TODO consider making an even simpler tile style one without greenspace/buildings