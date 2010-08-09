"""
Classes to plot TimeSeries w/ matplotlib.

:author: Pierre GF Gerard-Marchant & Matt Knox
:contact: pierregm_at_uga_dot_edu - mattknow_ca_at_hotmail_dot_com
:date: $Date: 2008-03-04 19:51:32 -0500 (Tue, 04 Mar 2008) $
:version: $Id: basic_plots.py 354 2008-03-05 00:51:32Z backtopop $
"""
__author__ = "Pierre GF Gerard-Marchant & Matt Knox ($Author: backtopop $)"
__version__ = '1.0'
__revision__ = "$Revision: 354 $"
__date__ = '$Date: 2008-03-04 19:51:32 -0500 (Tue, 04 Mar 2008) $'

import numpy as np
import numpy.ma as ma
from numpy.ma import masked

print "Here #1"

import scikits.hydroclimpy as climpy
import scikits.hydroclimpy.enso as enso



import matplotlib
#matplotlib.use('Agg')
import scikits.hydroclimpy.plotlib as cpl
from  scikits.hydroclimpy.plotlib.ensotools import csfigure, \
                                                   ENSOcolors, ENSOpolygons, \
                                                   ENSOmap

import logging
logger = logging.getLogger('compare_enso')

logger.debug("The fun starts here...")

JMA = enso.load_jma()
ONI = enso.load_oni()


print JMA.ensoindices.convert('A')

def plot_jma(num=None, fill=True, full_year=False, fill_neutral=False):
    if num is None:
        fig = csfigure(series=JMA)
    else:
        fig = csfigure(num=num, series=JMA)
    fig.clear()
    fsp = fig.add_csplot(111)
    fill_colors = ENSOcolors['fill']
    polygon_colors = ENSOcolors['polygons']
    marker_colors = ENSOcolors['markers']
    line_colors = ENSOcolors['lines']
    #
    enso_indices = JMA.set_indices(full_year=full_year)
    xxthcentury = (JMA.years >= 1900)
    imask = enso_indices
    cold = JMA[((enso_indices == -1) & xxthcentury).filled(False)]
    neutral = JMA[((enso_indices == 0) & xxthcentury).filled(False)]
    warm = JMA[((enso_indices == +1) & xxthcentury).filled(False)]
    #
    _JMA = JMA[xxthcentury]
    #
    xdata = enso_indices._dates.tovalue()
    #
    fsp.tsplot(_JMA)
    if fill:
        cold = _JMA.view(type(_JMA))
        cold.unshare_mask()
        cold.__setmask__((enso_indices != -1), copy=True)
        fsp.fill(xdata, cold._series.filled(_JMA.thresholds[0]),
                 ec=fill_colors['C'], fc=fill_colors['C'])
        warm = _JMA.view(type(_JMA))
        warm.unshare_mask()
        warm.__setmask__((enso_indices != 1), copy=True)
        fsp.fill(xdata, warm._series.filled(JMA.thresholds[-1]),
                 ec=fill_colors['W'], fc=fill_colors['W'])
        if fill_neutral:
            neutral = _JMA.view(type(_JMA))
            neutral.unshare_mask()
            neutral.__setmask__((enso_indices != 0).filled(True), copy=True)
            fsp.fill(xdata, neutral._series.filled(0),
                     ec=fill_colors['N'], fc=fill_colors['N'])
    else:
        fsp.tsplot(cold, marker='o', c=marker_colors['C'], ls='')
        fsp.tsplot(neutral, marker='o', c=marker_colors['N'], ls='')
        fsp.tsplot(warm, marker='o', c=marker_colors['W'], ls='')
    #
    fsp.axhline(0, ls='-', c='k')
    fsp.axhline(_JMA.thresholds[-1], ls='-.', c=line_colors['W'])
    fsp.axhline(_JMA.thresholds[0], ls='-.', c=line_colors['C'])
    fsp.format_dateaxis()
    fsp.set_datelimits(end_date='2010')
    #
    fsp.set_ylabel("5-m Averaged SST Anomalies (oC)", fontweight='bold')
    fsp.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.5))
    fsp.set_xlabel("Years", fontweight='bold')
    cpl.show()
    return fig

#..............................................................................
#def plot_jma_comparison(num=None, fill=True, fill_neutral=False):
#    #
#    fig = plot_jma(num, fill=True, full_year=False, fill_neutral=False)
#    fsp = fig.gca()
#    #
#    monthly_indices = JMA.set_indices(full_year=False, refseason='NDJ')
#    annual_indices = JMA.set_indices(full_year=True, refseason='OND')
#    annual_indices.__setmask__(annual_indices==monthly_indices)
#    fsp.tsplot(JMA[(annual_indices==-1).filled(False)], marker='v', ls='')
#    fsp.tsplot(JMA[(annual_indices==+1).filled(False)], marker='^', ls='')
#    fsp.tsplot(JMA[(annual_indices==0).filled(False)], marker='o', ls='')
#    
#    return fig

#####--------------------------------------------------------------------------
#--- --- Comparison ---
#####--------------------------------------------------------------------------
def get_colormatrix(series):
    "Returns a (n,120) array of colors for the given series."
    series = series.view(ma.MaskedArray)
    n = series.shape[-1] * 10
    series = series.filled(-9999).ravel()
    table = np.empty(np.ceil(series.size / float(n)) * n, dtype='|S7')
    polygons = ENSOpolygons
    table.flat = polygons['G'] = '#000000'
    tabdict = {'C':-1, 'N':0, 'W':+1, 'G':-9999, -9999:-9999}
    _table = table[:series.size]
    for (i, c) in polygons.iteritems():
        _table[series == tabdict[i]] = c
    table.shape = (-1, n)
    return table

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


def plot_jma_vs_jma_comparison(freq='M'):
    """
    Plots the comparison of monthly and annual indices for the JMA index.
    The monthly indices are defined for each month using Nov-Jan as reference
    season and a minimum of 6 consecutive months in the same ENSO conditions.
    The annual indices are defined for each period of 12 months, starting in Oct.,
    using Oct-Dec as reference season and a minimum of 6 consecutive months in
    the same ENSO conditions
    
    Parameters
    ----------
    freq : {int, string}
        Valid frequency specifier.
    """
    # Check that we have a valid frequency
    freq = climpy.check_freq(freq)
    # Get the ENSO indices: annual for 12 months period, monthly on a monthly basis
    logger.debug("Get ENSO JMAI...")
    annual = JMA.set_indices(full_year=True, reference_season='OND',
                             minimum_size=6)
    monthly = JMA.set_indices(full_year=False, reference_season='NDJ',
                              minimum_size=6)
    # Convert to the new frequency
    if freq != climpy._c.FR_MTH:
        annual = np.round_(annual.convert(freq, func=ma.mean))
        monthly = np.round_(monthly.convert(freq, func=ma.mean))
    # Convert the indices to a Nx12 series (N the nb of years)
    annual = annual.convert('A')
    monthly = monthly.convert('A')
    # Trim to select only the data after 1900.
    annual = annual[annual.year >= 1900]
    monthly = monthly[monthly.year >= 1900]
    # Get the colors
#    logger.debug("Get color matrices")
#    a_colors = get_colormatrix(annual)
#    m_colors = get_colormatrix(monthly)
#    edegecolors = 'none'
    ensomap = ENSOmap
    #
    logger.debug("Prepare figure...")
    fig = cpl.figure(num=1, figsize=(13, 5))
    fig.clear()
    fsp = fig.add_axes([0.05, 0.1, 0.85, 0.85])
    (nrows, ncols) = annual.shape #a_colors.shape
    logger.debug("Get vertices #1...")
    # Get the vertices of the polygons corresponding to standard indices
    a_vert = np.array([[((i, j + 1), (i, j), (i + 1, j)) for i in range(ncols)]
                       for j in range(nrows)])
    a_vert.shape = (-1, 3, 2)
    # Create a PolyCollection for the polygons.
    a_coll = matplotlib.collections.PolyCollection(a_vert,
                                                   norm=ENSOmap)
    fsp.add_collection(a_coll)
    # Same process, this time with the monthly indices
    logger.debug("Get vertices #2...")
    m_vert = np.array([[((i, j + 1), (i + 1, j + 1), (i + 1, j)) for i in range(ncols)]
                       for j in range(nrows)])
    m_vert.shape = (-1, 3, 2)
    m_coll = matplotlib.collections.PolyCollection(m_vert,
                                                  norm=ENSOmap)
    fsp.add_collection(m_coll)
    # Plot the underlying grid.
    logger.debug("Plot grid...")
    xy_vert = [((i, 0), (i, nrows)) for i in range(0, ncols, 12)]
    xy_vert += [((0, j), (ncols, j)) for j in range(nrows)]
    xy_coll = matplotlib.collections.LineCollection(xy_vert, colors='k')
    fsp.add_collection(xy_coll)
    fsp.grid(True, which='minor', ls=':', c='#999999', lw=0.5)
    # Set the ticks on the
    logger.debug("Set ticks...")
    fsp.xaxis.set_major_locator(cpl.MultipleLocator(12))
    fsp.xaxis.set_minor_locator(cpl.MultipleLocator(1))
    fsp.set_xticks(np.arange(0, ncols, 12) + 6, minor=False)
    fsp.set_xticklabels(["%02i" % i for i in range(10)])
    fsp.set_xlim(0, ncols)
    #............................................
    fsp.set_yticks(np.arange(0, nrows) + 0.5)
    fsp.set_yticklabels(["%i" % (i * 10 + 1900) for i in range(nrows + 1)])
    fsp.set_ylim(0, nrows)
    fsp.set_ylim(fsp.get_ylim()[::-1])
    #............................................
    logger.debug("Add legend")
    add_plot_legend(fig)
    #
    #cpl.show()
    return fig



def plot_jma_vs_oni_comparison(freq='M'):
    """
    Plots the comparison of ONI vs JMAI ENSO indices at the given frequency.
    """
    # Check that we have a valid frequency
    freq = climpy.check_freq(freq)
    # Get the ENSO indices: annual for 12 months period, monthly on a monthly basis
    JMAi = JMA.indices(full_year=False, reference_season='NDJ', minimum_size=6)
    ONIi = ONI.indices(full_year=False, reference_season=None, minimum_size=5)
    # Convert to the new frequency
    if freq != climpy._c.FR_MTH:
        JMAi = np.round_(JMAi.convert(freq, func=ma.mean))
        ONIi = np.round_(ONIi.convert(freq, func=ma.mean))
    # Convert the indices to a Nx12 series (N the nb of years)
    JMAi = JMAi.convert('A')
    ONIi = ONIi.convert('A')
    #
    JMAi = JMAi[JMAi.year >= 1900]
    ONIi = ONIi[ONIi.year >= 1900]
    #
    j_colors = get_colormatrix(JMAi)
    o_colors = get_colormatrix(ONIi)
    #
    fig = cpl.figure(num=1, figsize=(13, 5))
    fig.clear()
    fsp = fig.add_axes([0.05, 0.1, 0.85, 0.85])
    (nrows, ncols) = j_colors.shape
    edgecolors = 'none'
    #
    j_vert = np.array([[((i, j + 1), (i, j), (i + 1, j)) for i in range(ncols)]
                          for j in range(nrows)]).reshape(-1, 3, 2)
    j_coll = matplotlib.collections.PolyCollection(j_vert,
                                                  facecolors=j_colors.ravel(),
                                                  edgecolors=edgecolors)
    fsp.add_collection(j_coll)
    #............................................
    o_vert = np.array([[((i, j + 1), (i + 1, j + 1), (i + 1, j)) for i in range(ncols)]
                          for j in range(nrows)]).reshape(-1, 3, 2)
    o_coll = matplotlib.collections.PolyCollection(o_vert,
                                                  facecolors=o_colors.ravel(),
                                                  edgecolors=edgecolors)
    fsp.add_collection(o_coll)
    #............................................
    xy_vert = [((i, 0), (i, nrows)) for i in range(0, ncols, 12)]
    xy_vert += [((0, j), (ncols, j)) for j in range(nrows)]
    xy_coll = matplotlib.collections.LineCollection(xy_vert,
                                                    colors='k')
    fsp.add_collection(xy_coll)
    #............................................
    fsp.xaxis.set_major_locator(cpl.MultipleLocator(12))
    fsp.set_xticks(np.arange(0, ncols, 12) + 6)
    fsp.set_xticklabels(["%02i" % i for i in range(12)])
    fsp.set_xlim(0, ncols)
    #............................................
    fsp.set_yticks(np.arange(0, nrows) + 0.5)
    fsp.set_yticklabels(["%i" % (i * 10 + 1900) for i in range(nrows + 1)])
    fsp.set_ylim(0, nrows)
    fsp.set_ylim(fsp.get_ylim()[::-1])
    add_plot_legend(fig, lableft='JMA', labright='ONI')
    cpl.show()
    return fig


#------------------------------------------------------------------------------
if __name__ == '__main__':
    if 0:
        fig = plot_jma(num=2)
        fig.savefig("JMA_monthly.png", dpi=720)
    if 1:
        fig = plot_jma_vs_jma_comparison()
#        fig.savefig("JMA_comparison_annual_monthly.png", dpi=720)
    if 0:
        fig = plot_jma_vs_oni_comparison()
        fig.savefig("JMA_ONI_comparison_annual_monthly.png", dpi=720)
    if 0:
        import scikits.timeseries.const as _c
        fig = plot_jma_vs_jma_comparison(freq=_c.FR_QTRSFEB)
        fig.savefig("JMA_comparison_annual_QTRDJF.png", dpi=720)

    #
if 0:
    annual = JMA.indices(full_year=True, refseason='OND').convert('A')
    monthly = JMA.indices(full_year=False, refseason='NDJ').convert('A')
    #
    #
    annual_indices = climpy.ClimateSeries(JMA.indices(full_year=True, refseason='OND'),
                                          ensoindicator=JMA)
    annual_indices.set_ensoindices(full_year=True, refseason='OND')
    monthly_indices = climpy.ClimateSeries(JMA.indices(full_year=False, refseason='NDJ'),
                                           ensoindicator=JMA)
    monthly_indices.set_ensoindices(full_year=False, refseason='NDJ')
    #
    nbmonths_y = apply_onphase(annual_indices[annual_indices.year >= 1900].convert('A'),
                               ma.count, axis=0)
    nbmonths_m = apply_onphase(monthly_indices[monthly_indices.year >= 1900].convert('A'),
                               ma.count, axis=0)
    monthlist = [' Jan ', ' Feb ', ' Mar ', ' Apr ', ' May ', ' Jun ',
                 ' Jul ', ' Aug ', ' Sep ', ' Oct ', ' Nov ', ' Dec ']
    blurb = ["%7s&%3s" % (" ", " ") + '&'.join(monthlist) + "\\\\"]
    blurb += ["%7s&%3s" % ("Cold", "(A)") + \
              '&'.join(["%5s" % m for m in nbmonths_y[-1]]) + "\\\\"]
    blurb += ["%7s&%3s" % ("Cold", "(M)") + \
              '&'.join(["%5s" % m for m in nbmonths_m[-1]]) + "\\\\"]
    blurb += ["%7s&%3s" % ("Neutral", "(A)") + \
              '&'.join(["%5s" % m for m in nbmonths_y[0]]) + "\\\\"]
    blurb += ["%7s&%3s" % ("Neutral", "(M)") + \
              '&'.join(["%5s" % m for m in nbmonths_m[0]]) + "\\\\"]
    blurb += ["%7s&%3s" % ("Warm", "(A)") + \
              '&'.join(["%5s" % m for m in nbmonths_y[1]]) + "\\\\"]
    blurb += ["%7s&%3s" % ("Warm", "(M)") + \
              '&'.join(["%5s" % m for m in nbmonths_m[1]]) + "\\\\"]



if 0:
    a_table = ma.where(annual == -1, 'C', 'X')
    a_table[(annual == 0).filled(False)] = 'N'
    a_table[(annual == 1).filled(False)] = 'W'
    a_table = a_table.filled('X')
    annual_table = np.array(["%s" % ''.join(v.tolist())
                                for (y, v) in zip(a_table.year, a_table.series)
                                if y > 1900])
    #.............
    m_table = ma.where(monthly == -1, 'C', 'X')
    m_table[(monthly == 0).filled(False)] = 'N'
    m_table[(monthly == 1).filled(False)] = 'W'
    m_table.filled('X')
#    m_table = np.array(["%s&%s\\" % (y,''.join(v.tolist()))
#                           for (y,v) in zip(m_table.dates, m_table.series)])
    m_table = np.array(["%s" % ''.join(v.tolist()) for v in m_table.series])
    monthly_table = np.empty((11, 10,), dtype='|S12')
    monthly_table.flat = 'X' * 12
    _t = m_table[32:]
    monthly_table.flat[:len(_t)] = _t
