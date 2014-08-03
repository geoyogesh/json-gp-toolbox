import os

__author__ = 'Yogesh'



import json
import arcpy
from pprint import pprint


def get_field_names(data):
    attr = set()
    geom = set()

    if data['type'] == "Feature":
        geom.add(data['geometry']['type'])
        attr.update(tuple(data['properties'].keys()))
    else:
        for feature in data['features']:
            geom.add(feature['geometry']['type'])
            attr.update(tuple(feature['properties'].keys()))
    return attr, geom

def create_fc(geom, attr, sr):
    fcs = dict()
    #http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#//000v00000153000000
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
        fcs[geometry]= arcpy.CreateFeatureclass_management('in_memory', geometry, geometry, '', 'DISABLED', 'DISABLED', sr, '', '0', '0', '0')

    for key, value in fcs.iteritems():
        for att in attr:
            # http://help.arcgis.com/en/arcgisdesktop/10.0/help/0017/001700000047000000.htm
            arcpy.AddField_management(value, att , "TEXT", '', '', '100')
    return fcs

def flaten_list(lis):
    out=[]
    for i in lis:
        if type(i) == 'string':
            out.append(i)
        else:
            out.append(str(i))
    return out


def insert_feature(fcs, feature):
    g = feature['geometry']['type']
    attrs = feature['properties']
    geom_obj = arcpy.AsShape(feature['geometry'])
    fc = None
    if g == 'Point':
        fc = fcs['POINT']
    elif g == 'MultiPoint':
        fc = fcs['MULTIPOINT']
    elif g == 'LineString' or g == 'MultiLineString':
        fc = fcs['POLYLINE']
    elif g == 'Polygon' or g == 'MultiPolygon':
        fc = fcs['POLYGON']
    with arcpy.da.InsertCursor(fc, tuple(['SHAPE@'] + attrs.keys())) as icur:
        print tuple(['SHAPE@'] + attrs.keys())
        print tuple([geom_obj] + flaten_list(attrs.values()))
        icur.insertRow(tuple([geom_obj] + flaten_list(attrs.values())))


def populate_data(fcs,data):
    if data['type'] == "Feature":
        insert_feature(fcs, data)
    else:
        for feature in data['features']:
            insert_feature(fcs, feature)

    return fcs


def export_gdb(fcs, gdb_path):
    (head, tail) = os.path.split(gdb_path)

    try:
        arcpy.CreateFileGDB_management(head, tail)
    except:
        for key, value in fcs.iteritems():
            try:
                arcpy.Delete_management(os.path.join(gdb_path,key))
            except:
                pass
        pass

    for key, value in fcs.iteritems():
        arcpy.CopyFeatures_management(value, os.path.join(gdb_path,key))


def main():
    with open('1.json', 'r') as json_data:
        data = json.load(json_data)
        attr,geom = get_field_names(data)
        #http://resources.arcgis.com/en/help/main/10.1/index.html#//018z0000000v000000S
        #Defualt is wgs 1984
        sr = arcpy.SpatialReference(4326)
        fcs=create_fc(geom, attr, sr)
        populate_data(fcs, data)
        export_gdb(fcs, r'C:\Users\Yogesh\Desktop\temp\temp\output.gdb')



if __name__ == "__main__":
    main()



