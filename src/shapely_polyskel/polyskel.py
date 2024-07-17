"""
Implementation of the straight skeleton algorithm as described by Felkel and
Obdržálek in their 1998 conference paper Straight skeleton implementation.
"""

import heapq
from dataclasses import dataclass
from itertools import chain, cycle, islice, tee

from euclid3 import Line2, LineSegment2, Point2, Ray2, Vector2, operator

EPSILON = 0.00001


def _window(lst: list[Point2]):
    prevs, items, nexts = tee(lst, 3)
    prevs = islice(cycle(prevs), len(lst) - 1, None)
    nexts = islice(cycle(nexts), 1, None)
    return zip(prevs, items, nexts)


def _cross(a: Vector2, b: Vector2) -> float:
    return a.x * b.y - b.x * a.y


def _approximately_equals(a: Point2, b: Point2) -> bool:
    return a == b or (abs(a - b) <= max(abs(a), abs(b)) * 0.001)


# TODO Function not used
# def _approximately_same(point_a: Point2, point_b: Point2) -> bool:
#     return _approximately_equals(
#         point_a.x, point_b.x
#     ) and _approximately_equals(point_a.y, point_b.y)


def _normalize_contour(contour: list) -> list[Point2]:
    contour = [Point2(x, y) for (x, y) in contour]
    normalized_contour = [
        point
        for prev, point, next in _window(contour)
        if not (
            point == next
            or (point - prev).normalized() == (next - point).normalized()
        )
    ]
    return normalized_contour


@dataclass
class _OriginalEdge:
    edge: LineSegment2
    bisector_left: Ray2
    bisector_right: Ray2


@dataclass
class Subtree:
    source: Point2
    height: float
    sinks: list[Point2]


class _LAVertex:
    def __init__(
        self,
        point: Point2,
        edge_left: LineSegment2,
        edge_right: LineSegment2,
        direction_vectors: tuple[Vector2, Vector2] | None = None,
    ) -> None:
        self.point = point
        self.edge_left = edge_left
        self.edge_right = edge_right
        self.prev = None
        self.next = None
        self.lav = None
        # TODO this might be handled better. Maybe membership in lav implies validity?
        self._valid = True

        creator_vectors = (
            edge_left.v.normalized() * -1,
            edge_right.v.normalized(),
        )
        if direction_vectors is None:
            direction_vectors = creator_vectors

        self._is_reflex = (_cross(*direction_vectors)) < 0
        self._bisector = Ray2(
            self.point,
            operator.add(*creator_vectors) * (-1 if self.is_reflex else 1),
        )

    @property
    def bisector(self) -> Ray2:
        return self._bisector

    @property
    def is_reflex(self) -> bool:
        return self._is_reflex

    @property
    def original_edges(self):
        return self.lav._slav._original_edges

    def next_event(self):
        events = []
        if self.is_reflex:
            # a reflex vertex may generate a split event
            # split events happen when a vertex hits an opposite edge, splitting the polygon in two.
            for edge in self.original_edges:
                if edge.edge == self.edge_left or edge.edge == self.edge_right:
                    continue

                # a potential b is at the intersection of between our own bisector and the bisector of the
                # angle between the tested edge and any one of our own edges.

                # we choose the "less parallel" edge (in order to exclude a potentially parallel edge)
                leftdot = abs(
                    self.edge_left.v.normalized().dot(edge.edge.v.normalized())
                )
                rightdot = abs(
                    self.edge_right.v.normalized().dot(edge.edge.v.normalized())
                )
                selfedge = (
                    self.edge_left if leftdot < rightdot else self.edge_right
                )
                otheredge = (
                    self.edge_left if leftdot > rightdot else self.edge_right
                )

                i = Line2(selfedge).intersect(Line2(edge.edge))
                if i is not None and not _approximately_equals(i, self.point):
                    # locate candidate b
                    linvec = (self.point - i).normalized()
                    edvec = edge.edge.v.normalized()
                    if linvec.dot(edvec) < 0:
                        edvec = -edvec

                    bisecvec = edvec + linvec
                    if abs(bisecvec) == 0:
                        continue
                    bisector = Line2(i, bisecvec)
                    b = bisector.intersect(self.bisector)

                    if b is None:
                        continue

                    # check eligibility of b
                    # a valid b should lie within the area limited by the edge and the bisectors of its two vertices:
                    xleft = (
                        _cross(
                            edge.bisector_left.v.normalized(),
                            (b - edge.bisector_left.p).normalized(),
                        )
                        > -EPSILON
                    )
                    xright = (
                        _cross(
                            edge.bisector_right.v.normalized(),
                            (b - edge.bisector_right.p).normalized(),
                        )
                        < EPSILON
                    )
                    xedge = (
                        _cross(
                            edge.edge.v.normalized(),
                            (b - edge.edge.p).normalized(),
                        )
                        < EPSILON
                    )

                    if not (xleft and xright and xedge):
                        continue

                    events.append(
                        _SplitEvent(
                            Line2(edge.edge).distance(b), b, self, edge.edge
                        )
                    )

        i_prev = self.bisector.intersect(self.prev.bisector)
        i_next = self.bisector.intersect(self.next.bisector)

        if i_prev is not None:
            events.append(
                _EdgeEvent(
                    Line2(self.edge_left).distance(i_prev),
                    i_prev,
                    self.prev,
                    self,
                )
            )
        if i_next is not None:
            events.append(
                _EdgeEvent(
                    Line2(self.edge_right).distance(i_next),
                    i_next,
                    self,
                    self.next,
                )
            )

        if not events:
            return None

        ev = min(
            events,
            key=lambda event: self.point.distance(event.intersection_point),
        )

        return ev

    def invalidate(self):
        if self.lav is not None:
            self.lav.invalidate(self)
        else:
            self._valid = False

    @property
    def is_valid(self) -> bool:
        return self._valid

    def __str__(self) -> str:
        return f"Vertex ({self.point.x:.2f};{self.point.y:.2f})"

    def __repr__(self) -> str:
        return "Vertex ({}) ({:.2f};{:.2f}), bisector {}, edges {} {}".format(
            "reflex" if self.is_reflex else "convex",
            self.point.x,
            self.point.y,
            self.bisector,
            self.edge_left,
            self.edge_right,
        )


@dataclass
class _SplitEvent:
    distance: float
    intersection_point: Point2
    vertex: _LAVertex
    opposite_edge: LineSegment2

    def __lt__(self, other: "_SplitEvent") -> bool:
        return self.distance < other.distance

    def __str__(self) -> str:
        return f"{self.distance} Split event @ {self.intersection_point} from \
{self.vertex} to {self.opposite_edge}"


@dataclass
class _EdgeEvent:
    distance: float
    intersection_point: Point2
    vertex_a: _LAVertex
    vertex_b: _LAVertex

    def __lt__(self, other: "_EdgeEvent") -> bool:
        return self.distance < other.distance

    def __str__(self) -> str:
        return f"{self.distance} Edge event @ {self.intersection_point} between\
 {self.vertex_a} and {self.vertex_b}"


class _SLAV:
    def __init__(self, polygon: list, holes: list) -> None:
        contours = [_normalize_contour(polygon)]
        contours.extend([_normalize_contour(hole) for hole in holes])

        self._lavs = [_LAV.from_polygon(contour, self) for contour in contours]

        # store original polygon edges for calculating split events
        self._original_edges = [
            _OriginalEdge(
                LineSegment2(vertex.prev.point, vertex.point),
                vertex.prev.bisector,
                vertex.bisector,
            )
            for vertex in chain.from_iterable(self._lavs)
        ]

    def __iter__(self):
        yield from self._lavs

    def __len__(self) -> int:
        return len(self._lavs)

    def empty(self) -> bool:
        return len(self._lavs) == 0

    def handle_edge_event(self, event):
        sinks = []
        events = []

        lav = event.vertex_a.lav
        if event.vertex_a.prev == event.vertex_b.next:
            self._lavs.remove(lav)
            for vertex in list(lav):
                sinks.append(vertex.point)
                vertex.invalidate()
        else:
            new_vertex = lav.unify(
                event.vertex_a, event.vertex_b, event.intersection_point
            )
            if lav.head in (event.vertex_a, event.vertex_b):
                lav.head = new_vertex
            sinks.extend((event.vertex_a.point, event.vertex_b.point))
            next_event = new_vertex.next_event()
            if next_event is not None:
                events.append(next_event)

        return (
            Subtree(event.intersection_point, event.distance, sinks),
            events,
        )

    def handle_split_event(self, event):
        lav = event.vertex.lav

        sinks = [event.vertex.point]
        vertices = []
        x = None  # right vertex
        y = None  # left vertex
        norm = event.opposite_edge.v.normalized()
        for v in chain.from_iterable(self._lavs):
            if (
                norm == v.edge_left.v.normalized()
                and event.opposite_edge.p == v.edge_left.p
            ):
                x = v
                y = x.prev
            elif (
                norm == v.edge_right.v.normalized()
                and event.opposite_edge.p == v.edge_right.p
            ):
                y = v
                x = y.next

            if x:
                xleft = (
                    _cross(
                        y.bisector.v.normalized(),
                        (event.intersection_point - y.point).normalized(),
                    )
                    >= -EPSILON
                )
                xright = (
                    _cross(
                        x.bisector.v.normalized(),
                        (event.intersection_point - x.point).normalized(),
                    )
                    <= EPSILON
                )

                if xleft and xright:
                    break
                else:
                    x = None
                    y = None

        if x is None:
            return (None, [])

        v1 = _LAVertex(
            event.intersection_point,
            event.vertex.edge_left,
            event.opposite_edge,
        )
        v2 = _LAVertex(
            event.intersection_point,
            event.opposite_edge,
            event.vertex.edge_right,
        )

        v1.prev = event.vertex.prev
        v1.next = x
        event.vertex.prev.next = v1
        x.prev = v1

        v2.prev = y
        v2.next = event.vertex.next
        event.vertex.next.prev = v2
        y.next = v2

        new_lavs = None
        self._lavs.remove(lav)
        if lav != x.lav:
            # the split event actually merges two lavs
            self._lavs.remove(x.lav)
            new_lavs = [_LAV.from_chain(v1, self)]
        else:
            new_lavs = [_LAV.from_chain(v1, self), _LAV.from_chain(v2, self)]

        for l in new_lavs:
            if len(l) > 2:
                self._lavs.append(l)
                vertices.append(l.head)
            else:
                sinks.append(l.head.next.point)
                for v in list(l):
                    v.invalidate()

        events = []
        for vertex in vertices:
            next_event = vertex.next_event()
            if next_event is not None:
                events.append(next_event)

        event.vertex.invalidate()
        return (
            Subtree(event.intersection_point, event.distance, sinks),
            events,
        )


class _LAV:
    def __init__(self, slav) -> None:
        self.head = None
        self._slav = slav
        self._len = 0

    @classmethod
    def from_polygon(cls, polygon, slav):
        lav = cls(slav)
        for prev, point, next in _window(polygon):
            lav._len += 1
            vertex = _LAVertex(
                point, LineSegment2(prev, point), LineSegment2(point, next)
            )
            vertex.lav = lav
            if lav.head is None:
                lav.head = vertex
                vertex.prev = vertex.next = vertex
            else:
                vertex.next = lav.head
                vertex.prev = lav.head.prev
                vertex.prev.next = vertex
                lav.head.prev = vertex
        return lav

    @classmethod
    def from_chain(cls, head, slav):
        lav = cls(slav)
        lav.head = head
        for vertex in lav:
            lav._len += 1
            vertex.lav = lav
        return lav

    def invalidate(self, vertex):
        assert (
            vertex.lav is self
        ), "Tried to invalidate a vertex that's not mine"
        vertex._valid = False
        if self.head == vertex:
            self.head = self.head.next
        vertex.lav = None

    def unify(self, vertex_a, vertex_b, point):
        replacement = _LAVertex(
            point,
            vertex_a.edge_left,
            vertex_b.edge_right,
            (
                vertex_b.bisector.v.normalized(),
                vertex_a.bisector.v.normalized(),
            ),
        )
        replacement.lav = self

        if self.head in [vertex_a, vertex_b]:
            self.head = replacement

        vertex_a.prev.next = replacement
        vertex_b.next.prev = replacement
        replacement.prev = vertex_a.prev
        replacement.next = vertex_b.next

        vertex_a.invalidate()
        vertex_b.invalidate()

        self._len -= 1
        return replacement

    def __str__(self) -> str:
        return f"LAV {id(self)}"

    def __repr__(self) -> str:
        return f"{self!s} = {[vertex for vertex in self]}"

    def __len__(self) -> int:
        return self._len

    def __iter__(self):
        cur = self.head
        while True:
            yield cur
            cur = cur.next
            if cur == self.head:
                return

    def _show(self) -> None:
        cur = self.head
        while True:
            print(cur.__repr__())
            cur = cur.next
            if cur == self.head:
                break


class _EventQueue:
    def __init__(self) -> None:
        self.__data = []

    def put(self, item):
        if item is not None:
            heapq.heappush(self.__data, item)

    def put_all(self, iterable):
        for item in iterable:
            heapq.heappush(self.__data, item)

    def get(self):
        return heapq.heappop(self.__data)

    def empty(self) -> bool:
        return len(self.__data) == 0

    def peek(self):
        return self.__data[0]

    def show(self) -> None:
        for item in self.__data:
            print(item)


def _merge_sources(skeleton: list[Subtree]) -> None:
    """
    In highly symmetrical shapes with reflex vertices multiple sources may share
    the same location. This function merges those sources.
    """
    sources = {}
    to_remove = []
    for i, p in enumerate(skeleton):
        source = tuple(i for i in p.source)
        if source in sources:
            source_index = sources[source]
            # source exists, merge sinks
            for sink in p.sinks:
                if sink not in skeleton[source_index].sinks:
                    skeleton[source_index].sinks.append(sink)
            to_remove.append(i)
        else:
            sources[source] = i
    for i in reversed(to_remove):
        skeleton.pop(i)


def skeletonize(polygon: list, holes: list | None = None) -> list[Subtree]:
    """
    Compute the straight skeleton of a polygon.

    The polygon should be given as a list of vertices in counter-clockwise
    order.Holes is a list of the contours of the holes, the vertices of which
    should be in clockwise order.

    Please note that the y-axis goes downwards as far as polyskel is concerned,
    so specify your ordering accordingly.

    Returns the straight skeleton as a list of "subtrees", which are in the form
    of (source, height, sinks), where source is the highest points, height is
    its height, and sinks are the point connected to the source.
    """
    slav = _SLAV(polygon, [] if holes is None else holes)
    output = []
    prioque = _EventQueue()

    for lav in slav:
        for vertex in lav:
            prioque.put(vertex.next_event())

    while not (prioque.empty() or slav.empty()):
        i = prioque.get()
        if isinstance(i, _EdgeEvent):
            if not i.vertex_a.is_valid or not i.vertex_b.is_valid:
                continue

            (arc, events) = slav.handle_edge_event(i)
        elif isinstance(i, _SplitEvent):
            if not i.vertex.is_valid:
                continue
            (arc, events) = slav.handle_split_event(i)

        prioque.put_all(events)

        if arc is not None:
            output.append(arc)

    _merge_sources(output)
    return output
