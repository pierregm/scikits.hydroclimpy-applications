'''
Created on Sep 22, 2009

@author: pierregm
'''

__author__ = "Pierre GF Gerard-Marchant & Matt Knox ($Author: backtopop $)"
__version__ = '1.0'
__revision__ = "$Revision: 354 $"
__date__ = '$Date: 2008-03-04 19:51:32 -0500 (Tue, 04 Mar 2008) $'

import numpy as np
import numpy.ma as ma
from numpy.ma import masked

import matplotlib
#matplotlib.use('Agg')

from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.collections import LineCollection, PolyCollection

import scikits.hydroclimpy as climpy
import scikits.hydroclimpy.enso as enso
import scikits.hydroclimpy.plotlib as cpl
from  scikits.hydroclimpy.plotlib.ensotools import csfigure, \
                                                   ENSOcolors, ENSOpolygons, \
                                                   ENSOmap

import logging
logger = logging.getLogger('compare_enso')

logger.debug("The fun starts here...")


def convert_to_decades(series):
    """
    Converts a series to decades

    Returns a series with the same frequency as the original, adjusted to start
    at the beginning of the starting 10-y period and to end at the end of
    the ending period.

    Parameters
    ----------
    series : TimeSeries
        Input time series
    """
    (ystart, yend) = series.years[[0, -1]]
    dstart = climpy.Date(series.freq,
                         year=10 * (ystart // 10), month=1, day=1)
    dend = climpy.Date(series.freq,
                       year=10 * (yend // 10) + 9, month=12, day=31)
    decades = series.adjust_endpoints(start_date=dstart, end_date=dend)
    return decades

if 1:
    from numpy.ma.testutils import *
    if 1:
        "Trst convert_to_decades"
        series = climpy.time_series(np.random.rand(12), start_date='1993', freq='Y')
        decades = convert_to_decades(series)
        assert_equal(decades.years[[0, -1]], (1990, 2009))
        #
        series = climpy.time_series(np.random.rand(123), start_date='1993', freq='M')
        decades = convert_to_decades(series)
        assert_equal(decades.years[[0, -1]], (1990, 2009))
        assert_equal(decades.months[[0, -1]], (1, 12))

def add_plot_legend(fig, labright='M.', lableft='S.'):
    """Adds the legend on the right side"""
    #............................................
    _leg = fig.add_axes([0.92, 0.865, 0.055, 0.085])
    _leg.fill((0, 0.5, 0.5, 0), (0, 0, 1, 1), fc=ENSOpolygons['W'])
    _leg.text(0.05, 0.5, 'EN', fontsize='smaller')
    _leg.fill((0.5, 1, 1, 0.5), (0, 0, 1, 1), fc=ENSOpolygons['C'])
    _leg.text(0.6, 0.5, 'LN', fontsize='smaller')
    _leg.set_xticks([])
    _leg.set_yticks([])
    #............................................
    _leg = fig.add_axes([0.92, 0.75, 0.055, 0.085])
    _leg.plot((0, 1,), (0, 1), ls='-', c='k', marker='')
    _leg.set_xticks([])
    _leg.set_yticks([])
    _leg.text(0.6, 0.15, labright, fontsize='smaller')
    _leg.text(0.1, 0.5, lableft, fontsize='smaller')

colorlist = [ENSOpolygons[c] for c in ('G', 'C', 'N', 'W')]
ENSOmap = ListedColormap(colorlist)
ENSOnorm = BoundaryNorm((-9999, -1, 0, +1, +9999), len(ENSOmap.colors))



# Get the data ............................................
origdata = 'Standard'
origdata = 'COAPS'
logger.debug("Get ENSO JMAI standard")
JMA = enso.load_jma(origdata, thresholds=(-0.5, +0.5), reference_period=None)
standard = JMA.set_indices(full_year=True, minimum_size=6, reference_season='OND')
modified = JMA.set_indices(full_year=False, minimum_size=6, reference_season='NDJ')
# Convert the indices to decades (starting after 1900) ....
(ystart, yend) = JMA.years[[0, -1]]
ystart = max(ystart, 1900)
dstart = climpy.Date(series.freq, year=10 * (ystart // 10), month=1, day=1)
dend = climpy.Date(series.freq, year=10 * (yend // 10) + 9, month=12, day=31)
standard = standard.adjust_endpoints(start_date=dstart, end_date=dend)
modified = modified.adjust_endpoints(start_date=dstart, end_date=dend)
ncols = 120
ndecades = standard.size // ncols

# Get the vertices of the polygons corresponding...
logger.debug("")
# to standard indices (upper left)
s_vert = np.array([[((i, j + 1), (i, j), (i + 1, j)) for i in range(ncols)]
                   for j in range(ndecades)])
s_vert.shape = (-1, 3, 2)
# to modified indices (lower right)
m_vert = np.array([[((i, j + 1), (i + 1, j + 1), (i + 1, j)) for i in range(ncols)]
                   for j in range(ndecades)])
m_vert.shape = (-1, 3, 2)

# Prepare the figure ......................................
logger.debug("Prepare figure...")
fig = cpl.figure(num=1, figsize=(13, 5))
fig.clear()
fsp = fig.add_axes([0.05, 0.1, 0.85, 0.85])

# Group the vertices into collections .....................
logger.debug("Prepare collections...")
# For the standard indices
s_coll = PolyCollection(s_vert, norm=ENSOnorm, cmap=ENSOmap, edgecolors='None')
s_coll.set_array(standard._series.filled(-9999).ravel())
fsp.add_collection(s_coll)
# For the modified indices
m_coll = PolyCollection(m_vert, norm=ENSOnorm, cmap=ENSOmap, edgecolors='None')
m_coll.set_array(modified._series.filled(-9999).ravel())
fsp.add_collection(m_coll)

# Plot the underlying grid ................................
logger.debug("Plot grid...")
xy_vert = [((i, 0), (i, ndecades)) for i in range(0, ncols, 12)]
xy_vert += [((0, j), (ncols, j)) for j in range(ndecades)]
xy_coll = LineCollection(xy_vert, colors='k')
fsp.add_collection(xy_coll)
fsp.grid(True, which='minor', ls=':', c='#990000', lw=0.75)

# Set the ticks ...........................................
logger.debug("Set ticks...")
# x-axis ticks
fsp.xaxis.set_major_locator(cpl.MultipleLocator(12))
fsp.xaxis.set_minor_locator(cpl.MultipleLocator(1))
fsp.set_xticks(np.arange(0, ncols, 12) + 6, minor=False)
fsp.set_xticklabels(["%02i" % i for i in range(10)])
fsp.set_xlim(0, ncols)
# y-axis ticks
fsp.set_yticks(np.arange(0, ndecades) + 0.5)
fsp.set_yticklabels(np.arange(dstart.year, dend.year, 10).astype('|S4'))
fsp.set_ylim(0, ndecades)
fsp.set_ylim(fsp.get_ylim()[::-1])

# Add the legend ..........................................
logger.debug("Add legend")
add_plot_legend(fig)
#
fig.savefig("JMA_comparison_annual_monthly_%s.png" % origdata.lower(), dpi=720)

comparison = {}
globcount = float(standard.count())
for (i, s) in zip((-1, 0, +1), ('LN', 'N', 'EN')):
    comparison["S-%s" % s] = ma.sum(standard == i) / globcount
    comparison["M-%s" % s] = ma.sum(modified == i) / globcount
for s in ('LN', 'N', 'EN'):
    comparison["(M-S)-%s" % s] = 1. - comparison["S-%s" % s] / comparison["M-%s" % s]


tabletemplate = """
*---------*---*%(sepline)s*
*         *   *%(headline)s*
*---------*---*%(sepline)s*
* La Nina * S *%(S-LN)s*
*         * M *%(M-LN)s*
*         * D *%(D-LN)s*
*---------*---*%(sepline)s*
* Neutral * S *%(S-N)s*
*         * M *%(M-N)s*
*         * D *%(D-N)s*
*---------*---*%(sepline)s*
* El Nino * S *%(S-EN)s*
*         * M *%(M-EN)s*
*         * D *%(D-EN)s*
*---------*---*%(sepline)s*
"""
_modified = modified.convert("A")
_standard = standard.convert("A")
csc = '*'
sepline = csc.join(['-'*8] * 12)
headline = csc.join(["%7s " % _ for _ in 'JFMAMJJASOND'])
m_sums = {'S-EN': ma.sum(_standard == +1, axis=0),
          'S-N' : ma.sum(_standard == 0, axis=0),
          'S-LN': ma.sum(_standard == -1, axis=0),
          'M-EN': ma.sum(_modified == +1, axis=0),
          'M-N' : ma.sum(_modified == 0, axis=0),
          'M-LN': ma.sum(_modified == -1, axis=0),
          }
results = dict([(k, csc.join(["%7i " % _ for _ in v]))
                for (k, v) in m_sums.items()])
results['D-LN'] = csc.join(["%+6.1f%% " % _ for _ in
                            100. * (m_sums['M-LN'] * 1. / m_sums['S-LN'] - 1.)])
results['D-N'] = csc.join(["%+6.1f%% " % _ for _ in
                            100. * (m_sums['M-N'] * 1. / m_sums['S-N'] - 1.)])
results['D-EN'] = csc.join(["%+6.1f%% " % _ for _ in
                            100. * (m_sums['M-EN'] * 1. / m_sums['S-EN'] - 1.)])
results.update(sepline=sepline, headline=headline)
print tabletemplate % results
