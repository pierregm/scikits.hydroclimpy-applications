# -*- coding: utf-8 -*- 

import math
import operator
import gluon.contrib.simplejson as simplejson
import applications.sewater_climatetool.modules.gviz_api as gviz_api
reload(gviz_api)


periods_dict = dict(monthly=['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                             'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC', ],
                    JFM=['JFM', 'AMJ', 'JAS', 'OND'],
                    DJF=['DJF', 'MAM', 'JJA', 'SON'],
                    NDJ=['NDJ', 'FMA', 'MJJ', 'ASO'])


@service.jsonrpc
def system_listMethods():
    return ["get_region_markers", "get_stationinfo", "get_averages", "get_series"]
# systemListMethods.__name__ = 'system_listMethods' 



@service.jsonrpc
def get_region_markers(lat, lon, radius=None):
    # Undefined radius: just take everything
    if radius is None:
        records = db().select(db.stations_list.COOPID,
                              db.stations_list.LATITUDE,
                              db.stations_list.LONGITUDE,)
        return [(_.COOPID, _.LATITUDE, _.LONGITUDE) for _ in records]
    # Get the coordinates of a rectangular region center on (lat,lon)
    equatorial_radius = 6378.137 / 1.609344
    angular_distance = (radius / equatorial_radius) * 180./math.pi
    (lat_n, lat_s) = (lat + angular_distance, lat - angular_distance)
    angular_distance_s = angular_distance / math.cos(lat_s*math.pi/180.)
    lon_se = lon + angular_distance_s
    lon_sw = lon - angular_distance_s
    # Select only the points in the rectangular region
    stations = db.stations_list
    region = (stations.LATITUDE >= lat_s) & (stations.LATITUDE <= lat_n) &\
             (stations.LONGITUDE >= lon_sw) & (stations.LONGITUDE <= lon_se)
    records = db(region).select(stations.COOPID,
                                stations.LATITUDE,
                                stations.LONGITUDE,)
    # Now, select only the entries that fall in the circle
    # Distances from the circle's center are calculated using the haversine formula.
    selected = []
    (dlat, dlon) = (lat * math.pi/180., lon * math.pi/180.)
    for r in records:
        (COOPID, LAT, LON) = (r.COOPID, r.LATITUDE, r.LONGITUDE)
        (DLAT, DLON) = (LAT * math.pi/180., LON * math.pi/180.)
        d = 2 * math.asin(math.sqrt(math.sin((DLAT-dlat)/2.)**2 + 
                   math.cos(DLAT)*math.cos(dlat)*math.sin((DLON-dlon)/2.)**2))
        d *= equatorial_radius
        if d <= radius:
            selected.append((COOPID, LAT, LON))
    return selected

@service.jsonrpc
def get_stationinfo(coopid=None):
    record = db(db.stations_list.COOPID == str(coopid)).select()
    try:
        record = record[0]
    except IndexError:
        return {}
    info = record.as_dict();
    info["COUNTIES"] = record["COUNTY_WITHIN"].capitalize();
    # info = {"Station_name": record["STATION_NAME"],
    #         "COOP_ID": record["COOPID"],
    #         "Latitude": record["LATITUDE"],
    #         "Longitude": record["LONGITUDE"],
    #         "Altitude": record["ELEVATION"],
    #         "Counties": record["COUNTY_WITHIN"].capitalize(), }
    counties = record.COUNTY_REPRESENT.split(":")
    if len(counties) > 1:
        info["COUNTIES"] += " (%s)" % ", ".join(_.capitalize()
                                                for _ in counties[1:])
    return info


@service.jsonrpc
def get_averages(options):
    try:
        period = options["period"]
        obs = options["observation"]
        coopid = options["coopid"]
        ensoi = options["ENSOI"]
    except TypeError:
        raise TypeError("Invalid list index ?\n%s\n" % list(options))
    # Get the table to query
    tbname = "averages_%s_%s" % (period, obs)
    try:
        table = db[tbname]
    except KeyError:
        raise KeyError("The table '%s' is not available" % tbname)
    # Get the fields to get (ie, the seasons)
    fields = periods_dict[period]
    # Get the records matching the COOPID and the ENSOI, sorted by phase (ACNW)
    base_select = (table.COOPID == coopid) & (table.ENSOI == ensoi)
    records = db(base_select).select(*fields, orderby=table.phase)
    # Transform the records into a list 
    results_list = [fields] + [[r[_] for _ in fields] for r in records]
    # Get the selected baseline
    baseline = options["baseline"] or ""
    if baseline is "":
        # No baseline: just zip the results
        results = zip(*results_list)
    else:
        # Get the line nb corresponding to the baseline
        try:
            baseidx = "XACNW".index(baseline)
        except ValueError:
            results = results_list
        else:
            reference = results_list[baseidx]
            results = [results_list[0]] + \
                      [map(operator.sub, _, reference) for _ in results_list[1:]]
        results = zip(*results)
    # Describe the table the gviz_api way
    description = [("season", "string", "Season"),
                   ("global", "number", "Global"),
                   ("cold", "number", "La Ni\xf1a"),
                   ("neutral", "number", "Neutral"),
                   ("warm", "number", "El Ni\xf1o")]
    data_table = gviz_api.DataTable(description)
    data_table.LoadData(results)
    return data_table.ToJSon()


@service.jsonrpc
def get_series(options):
    tbname = "series_monthly_%(observation)s" % options
    table = db[tbname]
    field = "COOP%(coopid)s" % options
    records = db().select(table.dates, table[field])
###    data = records.as_list()
    data = [(r["dates"], r[field]) for r in records]
    description = [("dates", "date", "Date"),
                   ("values", "number",), ]
    data_table = gviz_api.DataTable(description)
    data_table.LoadData(data)
    return data_table.ToJSon()



def user():
    """
    exposes:
    http://..../[app]/default/user/login 
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request,db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    session.forget()
    return service()



def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html
    """
    response.flash = T('SECC Water group climate tool')
    return dict()


