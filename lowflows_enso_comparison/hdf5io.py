
import os

import numpy
from numpy import float_, int_

from scipy.stats import find_repeats

from scikits.timeseries import const as _c
from scikits.timeseries import check_freq

import tables
from tables import IsDescription, HDF5ExtError, NodeError, \
    Int32Col, Float64Col, StringCol, openFile

import logging
loghdf = logging.getLogger('hdftools')


#####--------------------------------------------------------------------------
#---- --- Descriptors ---
#####--------------------------------------------------------------------------

class Stations(IsDescription):
    name = StringCol(23)
    id = StringCol(15)
    lat = Float64Col()
    lon = Float64Col()

class MonthlyResults(IsDescription): 
    id = StringCol(15)
    Jan = Float64Col()
    Feb = Float64Col()
    Mar = Float64Col()
    Apr = Float64Col()
    May = Float64Col()
    Jun = Float64Col()
    Jul = Float64Col()
    Aug = Float64Col()
    Sep = Float64Col()
    Oct = Float64Col()
    Nov = Float64Col()
    Dec = Float64Col()


class NDJResults(IsDescription): 
    id = StringCol(15)
    NDJ = Float64Col()
    FMA = Float64Col()
    MJJ = Float64Col()
    ASO = Float64Col()
        
class DJFResults(IsDescription):  
    id = StringCol(15)
    DJF = Float64Col()
    MAM = Float64Col()
    JJA = Float64Col()
    SON = Float64Col()
    
class JFMResults(IsDescription):  
    id = StringCol(15)
    JFM = Float64Col()
    AMJ = Float64Col()
    JAS = Float64Col()
    OND = Float64Col()



monthenum = tables.Enum(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])

JFMenum = tables.Enum(['JFM', 'AMJ', 'JAS', 'OND'])
FMAenum = tables.Enum(['FMA', 'MJJ', 'ASO', 'NDJ'])
MAMenum = tables.Enum(['MAM', 'JJA', 'SON', 'DJF'])
AMJenum = tables.Enum(['AMJ', 'JAS', 'OND', 'JFM'])
MJJenum = tables.Enum(['MJJ', 'ASO', 'NDJ', 'FMA'])
JJAenum = tables.Enum(['JJA', 'SON', 'DJF', 'MAM'])
JASenum = tables.Enum(['JAS', 'OND', 'JFM', 'AMJ'])
ASOenum = tables.Enum(['ASO', 'NDJ', 'FMA', 'MJJ'])
SONenum = tables.Enum(['SON', 'DJF', 'AMJ', 'JAS'])
ONDenum = tables.Enum(['OND', 'JFM', 'AMJ', 'JAS'])
NDJenum = tables.Enum(['NDJ', 'FMA', 'MJJ', 'ASO'])
DJFenum = tables.Enum(['DJF', 'MAM', 'JJA', 'SON'])

freq2enum = {_c.FR_QTREJAN:NDJenum, _c.FR_QTRSJAN:NDJenum,
             _c.FR_QTREFEB:DJFenum, _c.FR_QTRSFEB:DJFenum,
             _c.FR_QTREMAR:JFMenum, _c.FR_QTRSMAR:JFMenum,
             _c.FR_QTREAPR:FMAenum, _c.FR_QTRSAPR:FMAenum,
             _c.FR_QTREMAY:MAMenum, _c.FR_QTRSMAY:MAMenum,
             _c.FR_QTREJUN:AMJenum, _c.FR_QTRSJUN:AMJenum,
             _c.FR_QTREJUL:MJJenum, _c.FR_QTRSJUL:MJJenum,
             _c.FR_QTREAUG:JJAenum, _c.FR_QTRSAUG:JJAenum,
             _c.FR_QTRESEP:JASenum, _c.FR_QTRSSEP:JASenum,
             _c.FR_QTREOCT:ASOenum, _c.FR_QTRSOCT:ASOenum,
             _c.FR_QTRENOV:SONenum, _c.FR_QTRSNOV:SONenum,
             _c.FR_QTREDEC:ONDenum, _c.FR_QTRSDEC:ONDenum,
             _c.FR_QTR:ONDenum, _c.FR_MTH: monthenum
            }


#####--------------------------------------------------------------------------
#---- --- HDF5 creation ---
#####--------------------------------------------------------------------------

def create_hdf5file(filename, freq, filedescr=""):  
    """Creates a new hdf5file for impact analysis.""" 
    # Open the file for appending ...............    
    h5file = openFile(filename, mode="a", title=filedescr)
    # Create the main groups ....................
    for (name, descr) in zip(("values", "differences", "apxpvalues"),
                             ("Rainfall values (mm/d)",
                              "Rainfall differences (mm/d)",
                              "Approximate p-values (mm/d)",)):
        group = h5file.createGroup(h5file.root, name, descr)
    # Create the subgroups ......................
    for name in ("values", "differences", "apxpvalues"):
        h5file.createGroup("/%s" % name, 'modified', "Modified ENSO index")
        h5file.createGroup("/%s" % name, 'standard', "Standard ENSO index")
        h5file.createGroup("/%s" % name, 'noenso', "Comparison Modified-Standard ENSO indices")
    # Check the frequency .......................
    freq = check_freq(freq)
    if freq == _c.FR_MTH:
        description = MonthlyResults
    elif freq in (_c.FR_QTREFEB, _c.FR_QTRSFEB, _c.FR_QTREMAY, _c.FR_QTRSMAY,
                  _c.FR_QTREAUG, _c.FR_QTRSAUG, _c.FR_QTRENOV, _c.FR_QTRSNOV):
        description = DJFResults
    elif freq in (_c.FR_QTREMAR, _c.FR_QTRSMAR, _c.FR_QTREJUN, _c.FR_QTRSJUN,
                  _c.FR_QTRESEP, _c.FR_QTRSSEP, _c.FR_QTREDEC, _c.FR_QTRSDEC,
                  _c.FR_QTR):
        description = JFMResults
    elif freq in (_c.FR_QTREJAN, _c.FR_QTRSJAN, _c.FR_QTREAPR, _c.FR_QTRSAPR,
                  _c.FR_QTREOCT, _c.FR_QTRSOCT, _c.FR_QTREOCT, _c.FR_QTRSOCT):
        description = NDJResults
    # Create the table for the 'values' group ...
    for subgroup in ("modified", "standard"):
        for (phase, label) in zip(("neutral", "warm", "cold", "noenso"),
                                  ("Neutral", "El Nino", "La Nina", "Global")):
            tablename = "/values/%s" % subgroup
            table = h5file.createTable(tablename, phase, description, label)
    # Create the tables for the differences/apxpvalues
    for group in ("differences", "apxpvalues"):
        # Comparison between phases
        for subgroup in ("modified", "standard"):
            for (phase, label) in zip(("CN", "WN", "CW", "CG", "NG", "WG"),
                                     ("La Nina - Neutral",
                                      "El Nino - Neutral",
                                      "La Nina - El Nino",
                                      "La Nina - Global",
                                      "Neutral - Global",
                                      "El Nino - Global"),):
                table = h5file.createTable("/".join(['', group, subgroup]),
                                           phase, description, label)
        # Comparison between methods
        for (phase, label) in zip(("cold", "warm", "neutral",),
                                 ("La Nina - (mod-std)",
                                  "El Nino - (mod-std)",
                                  "Neutral - (mod-std)",),):
                table = h5file.createTable("/".join(['', group, 'noenso']),
                                           phase, description, label)
    return h5file
                
#..............................................................................
def check_hdf5file(hdf5name):   
    """Check the validity of the current hdf5 file."""
    loghdf.info("Checking file %s..." % hdf5name)
    # Check that the file exists and is valid ...
    try:
        if not tables.isHDF5File(hdf5name):
            raise HDF5ExtError("The file '%s' is not a valid pytables!" % hdf5name) 
    except IOError:
        raise IOError("The file '%s' does not exist!" % hdf5name)
    hdf5file = tables.openFile(hdf5name, 'a')
    # Check the groups in order..................
    for gtype in hdf5file.listNodes("/"):
        gname = gtype._v_hdf5name
        if gname == 'values':
            for sgtype in hdf5file.listNodes("/%s" % gname):
                if sgtype._v_hdf5name not in ['modified', 'standard', 'noenso']:
                    raise NameError, "Unrecognized branch:%s" % sgtype._v_hdf5name
                if sgtype._v_hdf5name != 'noenso':
                    for phase in ('neutral', 'cold', 'warm', 'noenso'):
                        sgtype._g_checkHasChild(phase)
            loghdf.info("Group %s OK" % gname)
        elif gname in ('differences', 'apxpvalues'):
            for sgtype in hdf5file.listNodes("/%s" % gname):
                if sgtype._v_hdf5name not in ['modified', 'standard', 'noenso']:
                    raise NameError, "Unrecognized branch:%s" % sgtype._v_hdf5name
                if sgtype in ['modified', 'standard']:
                    for phase in ('CN', 'WN', 'CW', 'CG', 'NG', 'WG'):
                        sgtype._g_checkHasChild(phase)
                elif sgtype == 'noenso':
                    for phase in ('cold', 'neutral', 'warm'):
                        sgtype._g_checkHasChild(phase)                    
            loghdf.info("Group %s OK" % gname)
        elif gname == 'columns':
            loghdf.info("Group %s OK" % gname)
        elif gname == 'stations':
            loghdf.info("Group %s OK" % gname)
        else:
            raise HDF5ExtError("Unrecognized node '%s'" % gname)
    return hdf5file


#..............................................................................
def create_stations_table(h5file, stationnames, stationcoords):
    """Creates a station tables from the given list of names and coordinates.

Input:
    h5file : HDF5File
        A valid pytable file
    stationnames : dictionary
        A dictionary (station id <str>, station names <str>).
    stationcoords : dictionary
        A dictionary (station id <str>, (station lon., station lat.) <(float, float)>)
    """
    try:
        table = h5file.createTable("/", 'stations', Stations, "Station info")
    except NodeError:
        loghdf.info("The 'stations' table already exists ! Skipping creation...")
        return h5file
    station = table.row
    for (idcode, name) in stationnames.iteritems():
        station['id'] = idcode
        station['name'] = name
        (station['lon'], station['lat']) = stationcoords[idcode]
        station.append()
    table.flush()
    # Create the column group for quick access ..
    gcolumns = h5file.createGroup(h5file.root, "columns", "Columns selectors")   
    for (name, descr) in zip(('id', 'name', 'lon', 'lat'),
                             ("ID", "Name", "Longitude", "Latitude")):
        h5file.createArray(gcolumns, name,
                           numpy.array([x[name] for x in table.iterrows()]),
                           "%s selector" % descr)
    return h5file
    
def remove_duplicates(hdf5file):
    """Removes the duplicates from each table of hdf5file."""
    # Build a list of all tables.......
    tableslist = [n for n in hdf5file.walkNodes()
                  if isinstance(n, tables.table.Table) and 'id' in n.colnames]
    for tbl in tableslist:
        idcol = tbl.col('id')
        nullrow = tuple([-9999] * len(tbl[-1]))
        # Find the duplicates..........
        for dup in find_repeats(idcol)[0]:
            duprow = (idcol == dup).nonzero()[0]
            baserow = tbl[duprow[0]]
            # Set the duplicates to the null row....
            for r in [d for d in duprow[1:] 
                      if (tbl[d] == baserow) or \
                         (tbl[d].tostring() == baserow.tostring())]:
                tbl.modifyRows(r, rows=[nullrow, ])
        # Save the results .........................
        tbl.flush()        
        # Get the list of the flagged rows .........
        nullist = numpy.array([r.nrow for r in tbl if r['id'] == -9999])
        # Remove the flagged rows iteratively ......
        while len(nullist) > 0:
            first = nullist[0]
            last = nullist[(numpy.diff(nullist) != 1).nonzero()]
            if not last.size:
                last = nullist[-1]
            else:
                last = last[0]
            if first == last:
                last += 1
            tbl.removeRows(first, last)
            tbl.flush()
            nullist = numpy.array([r.nrow for r in tbl if r['id'] == -9999])
    return hdf5file

#####--------------------------------------------------------------------------
#---- --- HDF5 access ---
#####--------------------------------------------------------------------------
#
def read_period_data(h5file, period, group, subgroup, phase):
    """
    
Example: get the Modified-Neutral values for January:
    data = read_monthly_data(h5file, month, 'values','modified','neutral')
    """
    # Check the hdf5 file ..................
    if not isinstance(h5file, tables.File):
        raise TypeError("The input is not a valid pytables.File object! "\
                        "(got %s instead)" % type(h5file))
    # Check the month ......................
    period = str(period)
#    if period not in monthenum or month:
#        raise ValueError("Unrecognized month '%s': should be in %s" % \
#                         (month, monthenum._names.keys()))
    #
    table = h5file.getNode("/".join(['', group, subgroup, phase]))
    stations = h5file.root.stations
    #
    ndtype = numpy.dtype([('id', '|S15'), ('lon', float_), ('lat', float_), ('val', float_)])
#    data = []
#    node = table.read()
#    ids = h5file.root.columns.id
#    lats = numpy.array(h5file.root.columns.lat)
#    lons = numpy.array(h5file.root.columns.lon)
#    for (idcode,val) in zip(node["id"],node[month]):
#        id_indx = (ids==idcode)
#        data.append((idcode, lons[id_indx].item(), lats[id_indx].item(), val))
#    data = numpy.array(data, dtype=ndtype).view(numpy.recarray)
    # With set, we get rid of duplicates .....
    data = [set([(s['id'], s['lon'], s['lat'], val[period]) 
                for val in table.where("id=='%s'" % s['id'])])
            for s in stations.iterrows()]
    # Merge the sets in a big one ............
    data = reduce(lambda x, y:x.union(y), data)
    data = numpy.fromiter(data, dtype=ndtype)
    return data



