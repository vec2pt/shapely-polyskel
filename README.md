# shapely-polyskel

![PyPI - Status](https://img.shields.io/pypi/status/shapely-polyskel)
![PyPI - Version](https://img.shields.io/pypi/v/shapely-polyskel)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/shapely-polyskel)


<p align="center">
<img src="https://raw.githubusercontent.com/vec2pt/shapely-polyskel/master/doc/example.png" alt="A straight skeleton"/>
</p>

> [!NOTE]
> This package is a fork of an implementation written by Ármin Scipiades (Botffy). The original code can be found under the [link](https://github.com/Botffy/polyskel).

This is a Python 3 implementation of the straight skeleton algorithm as described by Felkel and Obdržálek in their 1998 conference paper [Straight skeleton implementation](doc/StraightSkeletonImplementation.pdf).

The algorithm itself is fairly dated, and shown to be incorrect for certain input polygons.
This implementation is a bit crap, and does not really attempt to fix the algorithm.
It works kinda okay for most real-life input (for example country contours or floor plans).

For a modern and excellent overview of the topic please refer to Stefan Huber's excellent [Computing Straight Skeleton and Motorcycle Graphs: Theory and Practice](https://www.sthu.org/research/publications/files/phdthesis.pdf).

## Installation

shapely-polyskel is available on PyPI:

```bash
pip install shapely-polyskel
```

## Usage

### Basic example (`skeletonize`)

```python
from shapely_polyskel import skeletonize

rectangle = [(40, 40), (40, 310), (520, 310), (520, 40)]
skeleton = skeletonize(polygon=rectangle)
```

### Polygon with holes (`skeletonize`)

```python
from shapely_polyskel import skeletonize

rectangle = [(40, 40), (40, 310), (520, 310), (520, 40)]
holes = [[(100, 100), (200, 100), (200, 150), (100, 150)]]
skeleton = skeletonize(polygon=rectangle, holes=holes)
```

### Basic example (`StraightSkeleton`)

```python
from shapely import Polygon
from shapely_polyskel import StraightSkeleton

# In the case of using 'StraightSkeleton', the direction of the polygon/hole
# points is not important.

polygon = Polygon(
    [(520, 40), (520, 310), (40, 310), (40, 40)],
    [[(100, 150), (200, 150), (200, 100), (100, 100)]],
)

straight_skeleton = StraightSkeleton(polygon=polygon)

# Returns the same list as 'skeletonize'
skeleton = straight_skeleton.straight_skeleton

source_points = straight_skeleton.source_points(points3d=False)
ridges = straight_skeleton.ridges()
sinks = straight_skeleton.sinks()
```

More examples can be found in the [notebooks](./notebooks/) folder.

## Forks & ports

- [Yongha Hwang's fork](https://github.com/yonghah/polyskel). Check out it to see polyskel in [sweet real-life action](https://github.com/yonghah/polyskel/blob/master/Create%20layout%20network%20using%20straight%20skeletons%20.ipynb) :heart: :heart: :heart:.
- [Polyskel-Swift](https://github.com/andygeers/Polyskel-Swift) a Swift port.
- [bpolyskel](https://github.com/prochitecture/bpypolyskel) is a port for Blender, making [some sweet roofs](https://user-images.githubusercontent.com/613295/94917497-4fd8c800-04b9-11eb-89ba-2f4f47f5b416.png) :heart:.
