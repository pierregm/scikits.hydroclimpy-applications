"""
Created on Jan 21, 2010

@author: pierregm


Database structure
------------------

* ``series_monthly_OBSERVATION``
  Stores the series of monthly observations for each station.
  The first column is the dates, the following columns are named ``COOPXXXXXX``.


"""

import sqlite3
import itertools

import numpy as np
import numpy.ma as ma

import scikits.hydroclimpy as hydro
import scikits.hydroclimpy.enso as enso
import scikits.hydroclimpy.io.coaps as coaps

import scikits.hydroclimpy.io.sqlite as sql


stationfile_csv = "../kml/stations.csv"
stationfile_rdb = "stations.rdb"
import sqlite3



def create_stationinfo_table(stationfile_csv, dbname='coaps.sqlite'):
    """
    Create a table storing information for each station of the COAPS network.

    The information is read from a CSV file and stored into a SQLite database
    name d by the variable `database_name`.

    Parameters
    ----------
    stationfile_csv : string
        Name of the CSV file storing the station information.
    database_name : string, optional
        Name of the database.
    """
    # Add the list of stations
    ndtype = [('COOPID', '|S6'), ('STATION_NAME', '|S30'),
              ('LONGITUDE', '<f8'), ('LATITUDE', '<f8'), ('ELEVATION', '<f8'),
              ('CROPID', '|S5'),
              ('COUNTY_WITHIN', '|S12'), ('COUNTY_REPRESENT', '|S40')]
    stations_nd = np.genfromtxt(stationfile_csv, delimiter=";", names=True,
                                dtype=ndtype)
    stations_db = sql.tosqlite(stations_nd, dbname, 'stations_list',
                               autoid=True, overwrite=True)



def dump_monthly_series(observations, dbname='coaps.sqlite'):
    """
    Dump the monthly data for observations ``observations``
    in the sqlite database ``coaps.sqlite``.

    The table stores the monthly series into a table named `series_monthly_XXXX`
    where `XXXX` is the observation ("rain", "tmin" or "tmax").
    The field (column) names of the table follow the template ``COOP%06i`` 


    Parameters
    ----------
    observations : string
        String describing the kind of observations

    Notes
    -----
    * The 'rain' series is the cumulative precipitation for the month
    * The 'tmin' and 'tmax' series are the average min and max temperatures
      for the month
    * Any month with more than 3 days missing is disabled.
    * Data is stored in different tables for each state.

    """
    options = dict(freq="M",
                   start_date="1950-01-01", end_date="2010-01-01",
                   max_missing=0.1)
    if observations in ('tmin', 'tmax'):
        options['func'] = ma.mean
    else:
        options['func'] = ma.sum
    seasonal = coaps.load_period_networkdata(observations, **options)
    #
    corrected_dtype = [("COOP%s" % _, float) for _ in seasonal.dtype.names]
    tbname = "series_monthly_%s" % observations
    sql.tstosqlite(seasonal.astype(corrected_dtype), dbname, tbname,
                   overwrite=True, autoid=True)



def dump_seasonal_averages(observations, dbname="coaps.sqlite",
                           period="monthly", ensostr="ONI"):
    """
    Dump seasonal averages of observations in a SQLite database.

    The database is named following the template ``avg%(observations)s.sdb``.
    For each season, there are four tables named following the template 
    ``%(period)s_%(phase)s_%(ENSOindicator)``.
    Each table has N+1 columns: 
        * Station COOP ID (format ``COOP%06i``)
        * ENSO indicator (used to define the phase): in ('ONI', 'JMAI', 'MEI')
        * ENSO phase : in ('A', 'C', 'N', 'W')
        * N values for each season

    Parameters
    ----------
    observations: string
        String representing the observations to store.
    period : ('M', 'NDJ', 'DJF', 'JFM'), optional
        String representing the seasons. 
        Use 'M' for monthly, 'DJF' for 'DJF,MAM,JJA,SON'...
    ensostr : ('ONI', 'JMAI', 'MEI'), optional
        String representing the ENSO indicator to define ENSO phases
    """
    seasons = dict(monthly=['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                            'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC', ],
                   JFM=['JFM', 'AMJ', 'JAS', 'OND'],
                   DJF=['DJF', 'MAM', 'JJA', 'SON'],
                   NDJ=['NDJ', 'FMA', 'MJJ', 'ASO'])

    # Get the seasonal frequency
    period = period.upper()
    period_to_freq = dict(M=hydro._c.FR_MTH,
                          MONTHLY=hydro._c.FR_MTH,
                          NDJ=hydro._c.FR_QTREOCT,
                          DJF=hydro._c.FR_QTRENOV,
                          JFM=hydro._c.FR_QTREDEC,)
    try:
        freq = period_to_freq[period]
    except KeyError:
        errmsg = "Invalid period '%s': should be in %s."
        raise ValueError(errmsg % (period, period_to_freq.keys()))

    # Get the names of the fields
    # fieldslist = ["COOPID text primary key", "ENSOI text", "phase text"]
    fieldslist = ["id integer primary key autoincrement",
                  "COOPID text", "ENSOI text", "phase text"]
    if period in ("M", "MONTHLY"):
        period = "monthly"
    fieldslist += ["%s real" % _ for _ in seasons[period]]
    nbfields = len(fieldslist)

    # Get the conversion function:
    if freq == hydro._c.FR_MTH:
        conversion_func = None
    else:
        if observations == 'rain':
            conversion_func = ma.sum
        else:
            conversion_func = ma.mean

    # Load the ENSO information
    ensostr = ensostr.upper()
    if ensostr == 'ONI':
        ENSO = enso.load_oni()
    elif ensostr == 'JMAI':
        ENSO = enso.load_jma()
    elif ensostr == 'MEI':
        raise NotImplementedError
    else:
        errmsg = "Invalid ENSO indicator '%s': should be in ('ONI','JMAI','MEI')"
        raise ValueError(errmsg % ensostr)

    # Get the monthly series from the datatable and set the ENSO indicator
    tbname = "series_monthly_%s" % observations
    monthly = sql.tsfromsqlite(dbname, tbname, freq="M")
    monthly = enso.set_ensoindicator(monthly, ENSO)

    # Define dictionaries storing the averages
    avg_r = {}
    # Loop on the stations
    for station in monthly.dtype.names:
	    # Get the current station
        current = monthly[station]
        # Get the season
        seasonal = current.convert(freq, func=conversion_func)
        if (observations == "rain") and (freq != hydro._c.FR_MTH):
            mask = hydro.time_series(current.mask, dates=current.dates)
            seasonal.mask = mask.convert(freq, func=ma.sum)
        # Get the values per phase
        coopid = station[-6:]
        avg_r[(coopid, ensostr, 'A')] = seasonal.convert("A").mean(0)
        avg_r[(coopid, ensostr, 'C')] = seasonal.cold.convert("A").mean(0)
        avg_r[(coopid, ensostr, 'N')] = seasonal.neutral.convert("A").mean(0)
        avg_r[(coopid, ensostr, 'W')] = seasonal.warm.convert("A").mean(0)

    # Get the database name
    detect_types = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    connection = sqlite3.connect(dbname, detect_types=detect_types)
    # Define the creation/insertion lines
    tbname = "averages_%(period)s_%(observations)s" % locals()
    createstr = "create table %s (%s)" % (tbname, ", ".join(fieldslist))
    insertstr_template = "insert into %s values (%s)"
    insertstr = insertstr_template % (tbname, ", ".join(['?']*nbfields))
    # Create the table
    try:
        connection.execute(createstr)
    except sqlite3.OperationalError:
        pass
    # Define a generator for the values
    generator = ([None, ] + list(k) + list(v.astype(np.object).filled((None,)))
                 for (k, v) in avg_r.items())
    connection.executemany(insertstr, generator)
    connection.commit()
    connection.close()





if __name__ == "__main__":
    create_stationinfo_table("stations.csv")
    observations = ("rain", "tmin", "tmax")
    for observation in observations:
        print "\nDumping monthly series for %s" % observation,
        dump_monthly_series(observation)
        for period in ("monthly", "JFM", "DJF", "NDJ"):
            print "[%s]" % period
            dump_seasonal_averages(observation, period=period)

