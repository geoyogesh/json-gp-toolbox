""" topojson.py
functions from (https://github.com/sgillies)
Author: Yogesh
"""

from itertools import chain
from arcpy import AsShape, CreateFeatureclass_management, SpatialReference, CreateFileGDB_management, Delete_management, \
    CopyFeatures_management, da
from os import path
import json


def rel2abs(arc, scale=None, translate=None):
    """Yields absolute coordinate tuples from a delta-encoded arc.

    If either the scale or translate parameter evaluate to False, yield the
    arc coordinates with no transformation."""
    if scale and translate:
        a, b = 0, 0
        for ax, bx in arc:
            a += ax
            b += bx
            yield scale[0] * a + translate[0], scale[1] * b + translate[1]
    else:
        for x, y in arc:
            yield x, y


def get_field_names(data):
    geom = set()
    for feature in data['objects']:
        geom.add(feature['type'])
    return geom


def coordinates(arcs, topology_arcs, scale=None, translate=None):
    """Return GeoJSON coordinates for the sequence(s) of arcs.

    The arcs parameter may be a sequence of ints, each the index of a
    coordinate sequence within topology_arcs
    within the entire topology -- describing a line string, a sequence of
    such sequences -- describing a polygon, or a sequence of polygon arcs.

    The topology_arcs parameter is a list of the shared, absolute or
    delta-encoded arcs in the dataset.

    The scale and translate parameters are used to convert from delta-encoded
    to absolute coordinates. They are 2-tuples and are usually provided by
    a TopoJSON dataset.
    """
    if isinstance(arcs[0], int):
        coords = [
            list(
                rel2abs(
                    topology_arcs[arc if arc >= 0 else ~arc],
                    scale,
                    translate)
            )[::arc >= 0 or -1][i > 0:] \
            for i, arc in enumerate(arcs)]
        return list(chain.from_iterable(coords))
    elif isinstance(arcs[0], (list, tuple)):
        return list(
            coordinates(arc, topology_arcs, scale, translate) for arc in arcs)
    else:
        raise ValueError("Invalid input %s", arcs)


def create_fc(geom, sr):
    fcs = dict()
    # http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#//000v00000153000000
    #http://geojson.org/geojson-spec.html#positions
    for g in geom:
        geometry = None
        if g == 'Point':
            geometry = 'POINT'
        elif g == 'MultiPoint':
            geometry = 'MULTIPOINT'
        elif g == 'LineString' or g == 'MultiLineString':
            geometry = 'POLYLINE'
        elif g == 'Polygon' or g == 'MultiPolygon':
            geometry = 'POLYGON'
        fcs[geometry] = CreateFeatureclass_management('in_memory', geometry, geometry, '', 'DISABLED', 'DISABLED', sr,
                                                      '', '0', '0', '0')

    return fcs


def geometry(obj, topology_arcs, scale=None, translate=None):
    """Converts a topology object to a geometry object.

    The topology object is a dict with 'type' and 'arcs' items, such as
    {'type': "LineString", 'arcs': [0, 1, 2]}.

    See the coordinates() function for a description of the other three
    parameters.
    """
    return {
        "type": obj['type'],
        "coordinates": coordinates(
            obj['arcs'], topology_arcs, scale, translate)}


def export_gdb(fcs, gdb_path):
    (head, tail) = path.split(gdb_path)

    try:
        CreateFileGDB_management(head, tail)
    except:
        for key, value in fcs.iteritems():
            try:
                Delete_management(path.join(gdb_path, key))
            except:
                pass
        pass

    for key, value in fcs.iteritems():
        CopyFeatures_management(value, path.join(gdb_path, key))


def insert_feature(fcs, feature):
    g = feature['type']
    geom_obj = AsShape(geometry(feature, t_arcs))
    fc = None
    if g == 'Point':
        fc = fcs['POINT']
    elif g == 'MultiPoint':
        fc = fcs['MULTIPOINT']
    elif g == 'LineString' or g == 'MultiLineString':
        fc = fcs['POLYLINE']
    elif g == 'Polygon' or g == 'MultiPolygon':
        fc = fcs['POLYGON']
    with da.InsertCursor(fc, tuple(['SHAPE@'])) as icur:
        icur.insertRow(tuple([geom_obj]))


def populate_data(fcs, data):
    for feature in data['objects']:
        insert_feature(fcs, feature)

    return fcs


if __name__ == "__main__":
    '''
    data = """{
    "arcs": [
      [[0, 0], [1, 0]],
      [[1.0, 0.0], [0.0, 1.0]],
      [[0.0, 1.0], [0.0, 0.0]],
      [[1.0, 0.0], [1.0, 1.0]],
      [[1.0, 1.0], [0.0, 1.0]]
      ],
    "transform": {
      "scale": [0.035896033450880604, 0.005251163636665131],
      "translate": [-179.14350338367416, 18.906117143691233]
    },
    "objects": [
      {"type": "Polygon", "arcs": [[0, 1, 2]]},
      {"type": "Polygon", "arcs": [[3, 4, 1]]}
      ]
    }"""

    topology = json.loads(data)
    t_scale = topology['transform']['scale']
    t_translate = topology['transform']['translate']
    t_arcs = topology['arcs']

    for i in topology['objects']:
        p = geometry(i, t_arcs)
        print AsShape(p)
    '''

    with open(path.join('4.topojson'), 'r') as json_data:
        data = json.load(json_data)

        t_scale = data['transform']['scale']
        t_translate = data['transform']['translate']
        t_arcs = data['arcs']

        geom = get_field_names(data)
        # http://resources.arcgis.com/en/help/main/10.1/index.html#//018z0000000v000000S
        #Defualt is wgs 1984S
        sr = SpatialReference(4326)
        fcs = create_fc(geom, sr)
        populate_data(fcs, data)
        export_gdb(fcs, r'C:\Users\Yogesh\Desktop\temp\temp\output.gdb')
        print 'completed successfully'

    '''
    p = geometry({'type': "LineString", 'arcs': [0]}, topology['arcs'])
    pprint.pprint(p)

    q = geometry({'type': "LineString", 'arcs': [0, 1]}, topology['arcs'])
    pprint.pprint(q)

    r = geometry(topology['objects'][0], topology['arcs'])
    pprint.pprint(r)

    s = geometry(topology['objects'][1], topology['arcs'], scale, translate)
    pprint.pprint(s)
    '''

