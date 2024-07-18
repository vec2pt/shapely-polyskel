from shapely import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    Point,
    Polygon,
    normalize,
    simplify,
)

from .polyskel import skeletonize


class StraightSkeleton:
    """StraightSkeleton"""

    def __init__(self, polygon: Polygon) -> None:
        """Straight skeleton

        Args:
            polygon (Polygon): Input polygon.

        Raises:
            ValueError: Empty polygon.
        """
        if polygon.is_empty:
            raise ValueError(
                "The polygon is empty. The skeleton can't be compute."
            )
        if not polygon.is_valid:
            raise ValueError(
                "The polygon is invalid. The skeleton can't be compute."
            )
        self._polygon = normalize(simplify(polygon, 0))
        self._straight_skeleton = self._skeletonize()

    def _skeletonize(self) -> list:
        polygon_pts = self._polygon.exterior.coords[:-1]
        holes_pts = [i.coords[:-1] for i in self._polygon.interiors]
        return skeletonize(polygon_pts, holes_pts)

    @property
    def polygon(self) -> Polygon:
        """Returns input polygon."""
        return self._polygon

    @property
    def straight_skeleton(self) -> list:
        """Returns straight skeleton (polyskel)."""
        return self._straight_skeleton

    def _source_points_coords(self, points3d: bool = False) -> list:
        coords = [
            (st.source.x, st.source.y, st.height)
            if points3d
            else (st.source.x, st.source.y)
            for st in self._straight_skeleton
        ]
        return coords

    def source_points(self, points3d: bool = False) -> MultiPoint | Point:
        """Source points

        Args:
            points3d (bool, optional): If True returns 3D points. Defaults to False.

        Returns:
            MultiPoint | Point: Source points.
        """
        source_points_coords = self._source_points_coords(points3d)
        if len(source_points_coords) == 1:
            return Point(source_points_coords[0])
        return MultiPoint(source_points_coords)

    def ridges(
        self,
    ) -> MultiLineString | LineString | Point:
        """Straight skeleton ridges

        Returns:
            MultiLineString | LineString | Point: Straight skeleton ridges
        """
        # TODO Add points3d option
        source_points_coords = self._source_points_coords()
        source_points_count = len(source_points_coords)
        if source_points_count == 1:
            return Point(source_points_coords[0])
        elif source_points_count == 2:
            return LineString(source_points_coords)
        else:
            ridges_lines = [
                [subtree.source, (sink_pt.x, sink_pt.y)]
                for subtree in self._straight_skeleton
                for sink_pt in subtree.sinks
                if (sink_pt.x, sink_pt.y) in source_points_coords
                and subtree.source != (sink_pt.x, sink_pt.y)
            ]
            return MultiLineString(ridges_lines)

    def sinks(self) -> MultiLineString:
        """Straight skeleton sinks

        Returns:
            MultiLineString: Straight skeleton sinks
        """
        # TODO Add points3d option
        source_points_coords = self._source_points_coords()
        sinks_lines = [
            [subtree.source, (sink_pt.x, sink_pt.y)]
            for subtree in self._straight_skeleton
            for sink_pt in subtree.sinks
            if (sink_pt.x, sink_pt.y) not in source_points_coords
        ]
        return MultiLineString(sinks_lines)

    def __str__(self) -> str:
        return f"StraightSkeleton ({self._polygon})"

    def __repr__(self) -> str:
        return f"StraightSkeleton ({self._polygon})"

    def svg(self, scale_factor: float = 1.0, color: str | None = None) -> str:
        """Returns a group of SVG elements for the straight skeleton.

        Args:
            scale_factor (float, optional): Multiplication factor for the SVG
                stroke-width. Defaults to 1.0.
            color (str | None, optional): Hex string for stroke or fill color.
                Default is to use "#66cc99" if geometry is valid, and "#ff3333"
                if invalid. Defaults to None.

        Returns:
            str: SVG string.
        """
        geometry = GeometryCollection(
            [self._polygon, self.ridges(), self.sinks()]
        )
        return geometry.svg(scale_factor, color)

    def _repr_svg_(self) -> str:
        """SVG representation for iPython notebook"""
        # TODO Add different colors
        geometry = GeometryCollection(
            [self._polygon, self.ridges(), self.sinks()]
        )
        return geometry._repr_svg_()
