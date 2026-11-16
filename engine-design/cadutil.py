"""Small CadQuery helpers. Engine frame: x forward, y left (crank axis), z up (cylinder axis)."""
import math
import cadquery as cq

V = cq.Vector


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl_y(r, y0, y1, x=0.0, z=0.0):
    return cq.Solid.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))


def cyl_z(r, z0, z1, x=0.0, y=0.0):
    return cq.Solid.makeCylinder(r, z1 - z0, V(x, y, z0), V(0, 0, 1))


def cyl_x(r, x0, x1, y=0.0, z=0.0):
    return cq.Solid.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))


def cyl_dir(r, p0, d, length):
    """Cylinder from point p0 along unit direction d."""
    return cq.Solid.makeCylinder(r, length, V(*p0), V(*d))


def tube_y(ro, ri, y0, y1, x=0.0, z=0.0):
    return cut(cyl_y(ro, y0, y1, x, z), cyl_y(ri, y0 - 1, y1 + 1, x, z))


def tube_z(ro, ri, z0, z1, x=0.0, y=0.0):
    return cut(cyl_z(ro, z0, z1, x, y), cyl_z(ri, z0 - 1, z1 + 1, x, y))


def fuse(*shapes):
    items = [s for s in shapes if s is not None]
    out = items[0]
    for s in items[1:]:
        out = out.fuse(s)
    return out.clean()


def cut(a, *bs):
    out = a
    for b in bs:
        if b is not None:
            out = out.cut(b)
    return out.clean()


def common(a, b):
    return a.intersect(b)


def prism_xz(points, y0, y1):
    """Polygon given as (x, z) points, extruded along y from y0 to y1."""
    wp = cq.Workplane(cq.Plane(origin=(0, y1, 0), xDir=(1, 0, 0), normal=(0, -1, 0)))
    return wp.polyline(points).close().extrude(y1 - y0).val()


def prism_xy(points, z0, z1):
    wp = cq.Workplane(cq.Plane(origin=(0, 0, z0), xDir=(1, 0, 0), normal=(0, 0, 1)))
    return wp.polyline(points).close().extrude(z1 - z0).val()


def prism_yz(points, x0, x1):
    """Polygon given as (y, z) points, extruded along x from x0 to x1."""
    wp = cq.Workplane(cq.Plane(origin=(x0, 0, 0), xDir=(0, 1, 0), normal=(1, 0, 0)))
    return wp.polyline(points).close().extrude(x1 - x0).val()


def revolve_z(profile, x=0.0, y=0.0, z=0.0):
    """Revolve an (r, h) polygon about a vertical axis through (x, y, z); h measured upward from z."""
    wp = cq.Workplane("XZ").polyline(profile).close().revolve(360, (0, 0, 0), (0, 1, 0))
    s = wp.val()
    return s.translate(V(x, y, z))


def sector_pts(cx, cz, r_of_a, a0, a1, n=48):
    """Points of a polar region centred (cx, cz): angles a measured from +z toward +x, degrees."""
    pts = [(cx, cz)]
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        r = r_of_a(a)
        pts.append((cx + r * math.sin(math.radians(a)), cz + r * math.cos(math.radians(a))))
    return pts


def rot(shape, axis, deg, center=(0, 0, 0)):
    return shape.rotate(V(*center), V(center[0] + axis[0], center[1] + axis[1], center[2] + axis[2]), deg)


def move(shape, x=0.0, y=0.0, z=0.0):
    return shape.translate(V(x, y, z))


def place_z_to(shape, origin, direction):
    """Shape modelled with its axis on +z at the origin; rotate +z onto 'direction' and move to 'origin'."""
    d = V(*direction).normalized()
    z = V(0, 0, 1)
    axis = z.cross(d)
    ang = math.degrees(math.acos(max(-1.0, min(1.0, z.dot(d)))))
    out = shape
    if axis.Length > 1e-9 and ang > 1e-9:
        out = out.rotate(V(0, 0, 0), axis, ang)
    elif ang > 90:
        out = out.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    return out.translate(V(*origin))


def vol(s):
    return s.Volume()


def bbox(s):
    b = s.BoundingBox()
    return (round(b.xmin, 2), round(b.xmax, 2), round(b.ymin, 2), round(b.ymax, 2), round(b.zmin, 2), round(b.zmax, 2))


def n_solids(s):
    return len(s.Solids())


def circle_pts(cx, cz, r, n=48):
    return [(cx + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
