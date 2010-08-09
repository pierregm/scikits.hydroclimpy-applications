import os
import scikits.climpy.core.tools as tools
import scikits.climpy.iotools as iotools

import matplotlib.pyplot as mpl
#from mpl_toolkits.basemap import Basemap
from matplotlib.toolkits.basemap import Basemap
import scikits.climpy.plotlib.maptools as maptools


config = iotools._config.configure()
coaps_config = dict(config.items('COAPS'))


def load_basemap(basemapname, limits=None, resolution='h',
                 config=coaps_config):
    """Loads a predefined basemap, or creates a new one from the limits.
    An Alberts Equal Areas is assumed.
    """
    _basemapname = os.path.join(config['datadir'], basemapname)
    if not os.path.exists(_basemapname):
        _basemapname = basemapname
    try:
        basemap = tools.unarchive(_basemapname)
    except IOError:
        (llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat) = limits
        basemap = Basemap(projection='aea',
                          llcrnrlon=llcrnrlon, llcrnrlat=llcrnrlat,
                          urcrnrlon=urcrnrlon, urcrnrlat=urcrnrlat,
#                          lat_1=40.,lat_2=60,lon_0=35,lat_0=50.,
                          lat_1=29.5, lat_2=45.5, lat_0=23, lon_0= -96,
                          resolution=resolution,
                          )
        tools.archive(basemap, _basemapname)
    return basemap


basemap = load_basemap('SouthGA_basemap.bin',
                       (-85.0, 30.50, -81.00, 32.01),
                       resolution='h',
                      )
# Define a figure and an axis
fig = mpl.figure()
fsp = fig.add_subplot(1, 1, 1)

# Draw the state & coast lines ....
basemap.drawstates(linewidth=1.25, color='k', ax=fsp)
basemap.drawcoastlines(linewidth=1.1, color='grey', ax=fsp)

riverfile = os.path.join('/home/backtopop/Work/GIS-Data/',
                                                   'NationalAtlas',
                                                   'NationalAtlas_GA_rivers',
                                                   'hydrogl020.shp'
                        )
basemap.readshapefile(riverfile, 'rivers', linewidth=0.8,
                      color='#999999', zorder=1, ax=fsp,)

#
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
#
annotate_args = dict(stretch='semi-condensed', fontsize=12,
                     textcoords='offset points')
annotate_args = dict(fontsize=10,)

(lon, lat) = basemap(*zip(*[(a, b) for (a, b, _, _) in COAPS_SE]))
coaps = fsp.plot(lon, lat, marker='o', ls='', mec='k', mfc='k', label='COAPS')
for (x, y, code, name) in COAPS_SE:
    fsp.annotate(" " + code, basemap(x, y), **annotate_args)
(lon, lat) = basemap(*zip(*[(a, b) for (a, b, _, _) in COAPS_SW]))
fsp.plot(lon, lat, marker='o', ls='', mec='k', mfc='k')
for (x, y, code, name) in COAPS_SW:
    fsp.annotate(" " + code, basemap(x, y), **annotate_args)
#
(lon, lat) = basemap(*zip(*[(a, b) for (a, b, _, _) in USGS_SE]))
usgs = fsp.plot(lon, lat, marker='^', ls='', mec='k', mfc='k', label='USGS')
for (x, y, code, name) in USGS_SE:
    fsp.annotate(" " + code, basemap(x, y), **annotate_args)
(lon, lat) = basemap(*zip(*[(a, b) for (a, b, _, _) in USGS_SW]))
fsp.plot(lon, lat, marker='^', ls='', mec='k', mfc='k')
for (x, y, code, name) in USGS_SW:
    fsp.annotate(" " + code, basemap(x, y), **annotate_args)
#
fsp.set_xlim(98400., 482300.)
fsp.set_ylim(33627., 228051.)
fsp.set_position((0.05, 0.35, 0.90, 0.6))

draw_default_args = dict(ax=fsp, resol=1, xoffset=0.001)
basemap.draw_default_parallels(**draw_default_args)
basemap.draw_default_meridians(**draw_default_args)

usgslabel = "USGS\n"
usgslabel += "\n".join(["%s : %s" % (a, b) for (_, _, a, b) in (USGS_SE + USGS_SW)])
coapslabel = "COAPS\n"
coapslabel += "\n".join(["%s : %s" % (a, b) for (_, _, a, b) in (COAPS_SE + COAPS_SW)])

from matplotlib.legend import Legend
leg = Legend(fig, (usgs,), (usgslabel,), loc="lower left", numpoints=1)
for t in leg.get_texts():
    t.set_fontsize(10)
fig.legends.append(leg)
leg = Legend(fig, (coaps,), (coapslabel,), loc="lower right", numpoints=1)
for t in leg.get_texts():
    t.set_fontsize(10)
fig.legends.append(leg)

fig.savefig('station_location.png', dpi=600)

#mpl.show()
