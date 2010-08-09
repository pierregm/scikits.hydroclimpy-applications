import shapelib
import dbflib



USGS_SE = [(-82.32, 31.24, '02226500', 'Satilla River near Waycross, GA'),
           (-81.87, 31.22, '02228000', 'Satilla River at Atkinson, GA'),
           (-82.56, 30.68, '02314500', 'Suwannee River at US 441, Fargo, GA')]
USGS_SW = [(-84.34, 31.31, '02353000', 'Flint River at Newton, GA'),
           (-84.55, 31.38, '02353500', 'Ichawaynochaway Creek at Milford, GA'),
           (-84.58, 30.91, '02356000', 'Flint River at Bainbridge, GA'),
           (-84.74, 31.04, '02357000', 'Spring Creek near Iron City, GA')]


COAPS_SE = [(-82.52, 31.52, '90211', 'Alma CAA Airport'),
            (-82.82, 31.52, '92783', 'Douglas'),
            (-82.80, 31.02, '94429', 'Homerville'), ]
COAPS_SW = [(-84.12, 31.52, '90140', 'Albany'),
            (-84.18, 31.79, '91500', 'Camilla'),
            (-84.77, 31.17, '92153', 'Colquitt'),
            (-84.77, 31.77, '92450', 'Cuthbert')]


if 1:
    file = "USGS_sGA.dbf"
    dbf = dbflib.create(file)
    dbf.add_field("LON", dbflib.FTDouble, 10, 4)
    dbf.add_field("LAT", dbflib.FTDouble, 10, 4)
    dbf.add_field("CODE", dbflib.FTString, 8, 0)
    dbf.add_field("NAME", dbflib.FTString, 40, 0)
    dbf.close()
    #
    dbf = dbflib.open(file, "r+b")
    for (i, record) in enumerate(USGS_SE + USGS_SW):
        dbf.write_record(i, record)
    dbf.close()
    #
    filename = "USGS_sGA.shp"
    outfile = shapelib.create(filename, shapelib.SHPT_POINT)
    for (i, record) in enumerate(USGS_SE + USGS_SW):
        obj = shapelib.SHPObject(shapelib.SHPT_POINT, i,
                                 [[(record[0], record[1])]])
        outfile.write_object(-1, obj)
    outfile.close()

if 1:
    file = "COAPS_sGA.dbf"
    dbf = dbflib.create(file)
    dbf.add_field("LON", dbflib.FTDouble, 10, 4)
    dbf.add_field("LAT", dbflib.FTDouble, 10, 4)
    dbf.add_field("CODE", dbflib.FTString, 8, 0)
    dbf.add_field("NAME", dbflib.FTString, 40, 0)
    dbf.close()
    #
    dbf = dbflib.open(file, "r+b")
    for (i, record) in enumerate(COAPS_SE + COAPS_SW):
        dbf.write_record(i, record)
    dbf.close()
    #
    filename = "COAPS_sGA.shp"
    outfile = shapelib.create(filename, shapelib.SHPT_POINT)
    for (i, record) in enumerate(COAPS_SE + COAPS_SW):
        obj = shapelib.SHPObject(shapelib.SHPT_POINT, i,
                                 [[(record[0], record[1])]])
        outfile.write_object(-1, obj)
    outfile.close()
