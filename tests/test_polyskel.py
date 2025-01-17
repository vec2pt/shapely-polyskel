# This file is a test initiation only.
# TODO Add real tests !!!
# TODO Add speed tests

import pytest
from shapely import Polygon
from shapely_polyskel import StraightSkeleton

init_data = [
    {  # florida
        "polygon": [
            (208, 131),
            (213, 142),
            (168, 141),
            (260, 168),
            (246, 149),
            (277, 142),
            (271, 163),
            (302, 180),
            (268, 173),
            (305, 196),
            (319, 225),
            (367, 214),
            (423, 169),
            (471, 160),
            (540, 208),
            (588, 268),
            (616, 270),
            (644, 308),
            (630, 446),
            (647, 472),
            (641, 459),
            (656, 467),
            (660, 450),
            (646, 423),
            (687, 447),
            (666, 495),
            (651, 495),
            (711, 580),
            (728, 584),
            (714, 557),
            (746, 560),
            (735, 569),
            (744, 617),
            (769, 594),
            (753, 624),
            (771, 628),
            (793, 700),
            (842, 708),
            (871, 759),
            (902, 780),
            (891, 788),
            (871, 773),
            (887, 799),
            (947, 774),
            (964, 782),
            (978, 689),
            (985, 678),
            (990, 695),
            (984, 555),
            (868, 338),
            (854, 294),
            (869, 316),
            (887, 314),
            (892, 366),
            (895, 322),
            (805, 196),
            (747, 61),
            (759, 59),
            (753, 43),
            (691, 33),
            (683, 98),
            (661, 72),
            (355, 83),
            (333, 46),
            (35, 70),
            (70, 144),
            (50, 165),
            (77, 154),
            (87, 125),
            (99, 139),
            (106, 118),
            (122, 139),
            (89, 152),
            (169, 124),
        ],
        "holes": None,
        "expected": True,
    },
    {  # half_iron_cross
        "polygon": [
            (100, 50),
            (150, 150),
            (50, 100),
            (50, 350),
            (350, 350),
            (350, 100),
            (250, 150),
            (300, 50),
        ],
        "holes": None,
        "expected": True,
    },
    {  # hole_symmetric (not supported list)
        "polygon": [(0, 0), (0, 200), (400, 200), (400, 0)],
        "holes": [(50, 50), (350, 50), (350, 150), (50, 150)],
        "expected": False,
    },
    {  # hole_symmetric (list of holes)
        "polygon": [(0, 0), (0, 200), (400, 200), (400, 0)],
        "holes": [[(50, 50), (350, 50), (350, 150), (50, 150)]],
        "expected": True,
    },
    {  # holey
        "polygon": [
            (30, 100),
            (50, 200),
            (220, 240),
            (440, 240),
            (430, 40),
            (230, 30),
            (85, 40),
        ],
        "holes": [
            [
                (175, 85),
                (245, 140),
                (315, 90),
                (385, 160),
                (330, 200),
                (165, 180),
            ]
        ],
        "expected": True,
    },
    {  # holey_2
        "polygon": [(0, 0), (0, 200), (500, 200), (400, 0)],
        "holes": [[(50, 50), (350, 50), (350, 150), (50, 150)]],
        "expected": True,
    },
    {  # misshapen
        "polygon": [
            (100, 50),
            (150, 150),
            (50, 100),
            (50, 250),
            (150, 250),
            (50, 350),
            (350, 350),
            (350, 100),
            (250, 150),
            (300, 50),
        ],
        "holes": None,
        "expected": True,
    },
    {  # rectangle
        "polygon": [(40, 40), (40, 310), (520, 310), (520, 40)],
        "holes": None,
        "expected": True,
    },
    {  # simple
        "polygon": [
            (30, 20),
            (30, 120),
            (90, 70),
            (160, 140),
            (178, 93),
            (160, 20),
        ],
        "holes": None,
        "expected": True,
    },
    {  # south_africa
        "polygon": [
            (162, 387),
            (186, 401),
            (337, 368),
            (434, 267),
            (442, 241),
            (416, 250),
            (402, 237),
            (429, 200),
            (417, 144),
            (377, 139),
            (301, 212),
            (254, 203),
            (225, 236),
            (203, 236),
            (193, 195),
            (193, 269),
            (176, 281),
            (140, 276),
            (134, 262),
            (125, 273),
            (144, 315),
        ],
        "holes": [
            [
                (345, 316),
                (336, 291),
                (358, 275),
                (372, 290),
            ]
        ],
        "expected": True,
    },
    {  # t-shape_extra_edge
        "polygon": [
            (0, 0),
            (0, 100),
            (60, 100),
            (60, 70),
            (100, 70),
            (100, 30),
            (60, 30),
            (60, 0),
        ],
        "holes": None,
        "expected": True,
    },
    {  # t-shape_hole_extra_edge
        "polygon": [
            (0, 0),
            (0, 200),
            (400, 200),
            (400, 0),
        ],
        "holes": [
            [
                (50, 50),
                (300, 50),
                (300, 75),
                (250, 75),
                (250, 125),
                (300, 125),
                (300, 150),
                (50, 150),
            ]
        ],
        "expected": True,
    },
    {  # the_sacred_polygon
        "polygon": [
            (40, 50),
            (40, 520),
            (625, 425),
            (500, 325),
            (635, 250),
            (635, 10),
            (250, 40),
            (200, 200),
            (100, 50),
        ],
        "holes": None,
        "expected": True,
    },
]


@pytest.mark.parametrize(
    "polygon, holes, expected",
    [(test["polygon"], test["holes"], test["expected"]) for test in init_data],
)
def test_validation(polygon, holes, expected):
    try:
        shapely_polygon = Polygon(polygon, holes)
        StraightSkeleton(shapely_polygon)
        assert True == expected
    except TypeError:
        assert False == expected
