import os
import numpy
from numpy import int_, float_, recarray

import numpy.ma as ma


import scikits.hydroclimpy as climpy
from scikits.hydroclimpy import _c
import scikits.hydroclimpy.io.coaps as coaps
import scikits.hydroclimpy.io.usgs as usgs


import hdf5io
reload(hdf5io)
from hdf5io import NodeError, HDF5ExtError


import matplotlib
matplotlib.use('Agg')
from matplotlib import pylab
from scikits.hydroclimpy.plotlib.ensotools import ENSOlines
# ENSOlines = cpl.ENSOcolors['lines']




# Let's hardcode the directory of the HDF5 archives for now.
hdf5_archive_dir = 'data'


def read_flows_period_differences(hdf5file, period, subgroup, phase, **kwargs):
    print "Read data for %s - %s - %s" % (period, subgroup, phase)
    if phase[-1] == 'G':
        valphase = 'noenso'
    elif phase[-1] == 'N':
        valphase = 'neutral'
    elif phase[-1] == 'W':
        valphase = 'warm'
    data = hdf5io.read_period_data(hdf5file, period,
                                   "values", subgroup, valphase)
    data_val = numpy.unique(data).view(recarray)
    data_val = data_val[numpy.argsort(data_val.id)]
    #
    data = hdf5io.read_period_data(hdf5file, period,
                                   "differences", subgroup, phase)
    data_dif = numpy.unique(data).view(recarray)
    data_dif = data_dif[numpy.argsort(data_dif.id)]
    #
    data = hdf5io.read_period_data(hdf5file, period,
                                   "apxpvalues", subgroup, phase)
    data_apx = numpy.unique(data).view(recarray)
    data_apx = data_apx[numpy.argsort(data_apx.id)]
    #
    selection = ~(numpy.isnan(data_dif.val) | numpy.isnan(data_apx.val))
    data_dif = data_dif[selection]
    data_apx = data_apx[selection]
    data_difrel = numpy.array([(i, lon, lat, dif / data_val.val[data_val.id == i][0])
                               for (i, lon, lat, dif) in data_dif],
                              dtype=data_dif.dtype).view(numpy.core.records.recarray)

    # Index data_apx ...........................................
    val = data_apx.val.copy()
    val[val <= 0.01] = 99.
    val[val <= 0.05] = 95.
    val[val <= 0.10] = 90.
    # Determines the local longitudes/latitudes ................
    return dict(data_dif=data_dif, data_difrel=data_difrel, data_apx=data_apx)


def plot_val_table(fsp, func, freq, quantile, stationlist):
    #
    freq = climpy.check_freq(freq)
    if freq == _c.FR_MTH:
        (periodtype, periodnames) = ("monthly", hdf5io.monthenum._names.keys())
        periodnames = ['Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May',
                       'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov']
    elif (freq // _c.FR_QTR == 1):
        (periodtype, periodnames) = ("quarterly", fqtr2names[freq])
    else:
        raise NotImplementedError, "Unrecognized frequency %s" % freq
    #
    funcdict = dict(med='median',
                    mean='mean',
                    )
    funcname = funcdict[func]
    qtlname = '%03i' % (100 * quantile)
    qtlleg = {'000':'Minimum',
              '025':'Lower Quartile'}['%03i' % (100 * quantile)]
    #
    freq = climpy.check_freq(freq)
    if freq == _c.FR_MTH:
        (periodtype, periodnames) = ("monthly", hdf5io.monthenum._names.keys())
        periodnames = ['Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May',
                       'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov']
    elif (freq // _c.FR_QTR == 1):
        (periodtype, periodnames) = ("quarterly", fqtr2names[freq])
    else:
        raise NotImplementedError, "Unrecognized frequency %s" % freq
    #
    #
    flow_basename = "USGS_Q%s_%s%s.hdf5" % (qtlname, fqname, func)
    # Define the HDF5 files ....................................
    hdf5flow_filename = os.path.join(hdf5_archive_dir, flow_basename)
    file = hdf5io.openFile(hdf5flow_filename, 'r+')
    hdf5flow = hdf5io.remove_duplicates(file)
    #
    val = hdf5flow.getNode("/".join(['', 'values', 'modified', 'noenso'])).read()
    for (marker, color, station) in zip(['o'] * 3 + ['s'] * 4,
                                        ['k'] * 3 + ['r'] * 4,
                                        stationlist):
        locval = val[val['id'] == station]
        fsp.plot(range(12), [locval[p] for p in periodnames],
                marker=marker, label=station, c=color)
    fsp.set_yscale('log')
    fsp.xaxis.set_major_locator(pylab.MultipleLocator(1))
    fsp.set_xticklabels(periodnames)
    fsp.set_ylabel("Flows (cfs)", fontweight='bold')
    fsp.set_title("%s flows - %s" % (qtlleg, funcname), fontweight='bold')
    pylab.show()



def plot_val(fsp, station, func, quantile, group='modified'):
    #
    freq = _c.FR_MTH
    freq = climpy.check_freq(freq)
    if freq == _c.FR_MTH:
#        (periodtype, periodnames) = ("monthly", hdf5io.monthenum._names.keys())
        periodnames = ['Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May',
                       'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov']
    elif (freq // _c.FR_QTR == 1):
        (periodtype, periodnames) = ("quarterly", fqtr2names[freq])
    else:
        raise NotImplementedError, "Unrecognized frequency %s" % freq
    #
    funcdict = dict(med='median',
                    mean='mean',
                    )
    funcname = funcdict[func]
    qtlname = '%03i' % (100 * quantile)
    qtlleg = {'000':'Minimum',
              '025':'Lower Quartile'}['%03i' % (100 * quantile)]
    #
    #
    flow_basename = "USGS_Q%s_%s%s.hdf5" % (qtlname, fqname, func)
    # Define the HDF5 files ....................................
    hdf5flow_filename = os.path.join(hdf5_archive_dir, flow_basename)
    file = hdf5io.openFile(hdf5flow_filename, 'r+')
    hdf5flow = hdf5io.remove_duplicates(file)
    #
    if fsp.is_first_col():
        labels = {'G':u"Global",
                  'C':u"La Ni\xf1a",
                  'N':u"Neutral",
                  'W':u"El Ni\xf1o",
                  'NS':"N/S",
                  '90': '_nolabel_',
                  '95': '_nolabel_',
                  '99': '_nolabel_'}
    else:
        labels = {'G':'_nolabel_',
                  'C':'_nolabel_',
                  'N':'_nolabel_',
                  'W':'_nolabel_',
                  'NS':"N/S",
                  '90': "90%",
                  '95': "95%",
                  '99': "99%"}

    #
    val = hdf5flow.getNode("/".join(['', 'values', group, 'noenso'])).read()
    val = val[val['id'] == station]
    fsp.plot(range(12), [val[p] for p in periodnames],
             marker='^', ms=6, label=labels['G'], c=ENSOlines['G'])
    #
    val = hdf5flow.getNode("/".join(['', 'values', group, 'cold'])).read()
    val = val[val['id'] == station]
    val = numpy.array([val[p] for p in periodnames])
    apx = hdf5flow.getNode("/".join(['', 'apxpvalues', group, 'CN'])).read()
    apx = apx[apx['id'] == station]
    apx = numpy.array([apx[p] for p in periodnames])
    col_C = ENSOlines['C']
    fsp.plot(range(12), val, marker='', label='_nolabel_', c=col_C)
    fsp.plot(range(12), ma.array(val, mask=(apx < 0.1)),
             marker='^', label=labels['C'], c=col_C)
    fsp.plot(range(12), ma.array(val, mask=(apx >= 0.1) | (apx < 0.05)) ,
             marker='d', label='_nolabel_', ls='', c=col_C, ms=10)
    fsp.plot(range(12), ma.array(val, mask=(apx >= 0.05) | (apx < 0.01)) ,
             marker='s', label='_nolabel_', ls='', c=col_C, ms=10)
    fsp.plot(range(12), ma.array(val, mask=(apx > 0.01)) ,
             marker='o', label='_nolabel_', ls='', c=col_C, ms=10)
    #
    val = hdf5flow.getNode("/".join(['', 'values', group, 'neutral'])).read()
    val = val[val['id'] == station]
    fsp.plot(range(12), [val[p] for p in periodnames],
             marker='o', ms=6, label=labels['N'], c=ENSOlines['N'])
    #
    val = hdf5flow.getNode("/".join(['', 'values', group, 'warm'])).read()
    val = val[val['id'] == station]
    val = numpy.array([val[p] for p in periodnames])
    apx = hdf5flow.getNode("/".join(['', 'apxpvalues', group, 'WN'])).read()
    apx = apx[apx['id'] == station]
    apx = numpy.array([apx[p] for p in periodnames])
    col_W = ENSOlines['W']
    fsp.plot(range(12), val, marker='', label='_nolabel_', c=col_W)
    fsp.plot(range(12), ma.array(val, mask=(apx < 0.1)),
             marker='^', label=labels['W'], c=col_W)
    fsp.plot(range(12), ma.array(val, mask=(apx >= 0.1) | (apx < 0.05)) ,
             marker='d', label=labels['90'], ls='', c=col_W, ms=10)
    fsp.plot(range(12), ma.array(val, mask=(apx >= 0.05) | (apx < 0.01)) ,
             marker='s', label=labels['95'], ls='', c=col_W, ms=10)
    fsp.plot(range(12), ma.array(val, mask=(apx > 0.01)) ,
             marker='o', label=labels['99'], ls='', c=col_W, ms=10)
    #
    #fsp.set_yscale('log')
    #
    fsp.xaxis.set_major_locator(pylab.MultipleLocator(1))
    if fsp.is_last_row():
        fsp.set_xticklabels(periodnames, fontsize=10)
    else:
        fsp.set_xticklabels([])
    fsp.set_ylabel("Flows (cfs)", fontweight='bold', fontsize=10)
    fsp.yaxis.major.formatter.set_powerlimits((-3, 3))
#    fsp.set_title("%s Q%02i flows - %s" % (funcname.capitalize(),
#                                           100.*quantile,
#                                           station), fontweight='bold')
    fsp.set_title("%s" % (station), fontweight='bold', fontsize=10)
    if fsp.is_last_row():
        fsp.legend(numpoints=1, prop=dict(size='x-small'))

    hdf5flow.close()
    return



def plot_comparison(stationlist, quantile, funcname, figsize=None,
                    withtitle=False):
    if figsize:
        fig = pylab.figure(figsize=figsize)
    nstation = len(stationlist)
    for (i, station) in enumerate(stationlist):
        j = nstation * 100 + 20 + 2 * i + 1
        fspl = fig.add_subplot(j)
        plot_val(fspl, station, funcname, quantile, 'modified')
        fspl_lim = fspl.get_ylim()
        fspr = fig.add_subplot(j + 1)
        plot_val(fspr, station, funcname, quantile, 'standard')
        fspr_lim = fspr.get_ylim()
        lims = (min(fspl_lim[0], fspr_lim[-1]),
                max(fspl_lim[0], fspr_lim[-1]))
        fspl.set_ylim(lims)
        fspr.set_ylim(lims)
    fig.subplots_adjust(left=0.07, right=0.95)
    fig.axes[-2].set_xlabel("Modified", fontweight='bold')
    fig.axes[-1].set_xlabel("Standard", fontweight='bold')
    if withtitle:
        fig.text(0.5, 0.95,
                 "%s Q%02i flows" % (funcname.capitalize(), quantile * 100),
                 fontweight='bold', ha='center')
    return fig




#####-------------------------------------------------------------------------
if 1:
    freq_names = dict([(v, k) for (k, v) in _c.freq_constants.iteritems()])
    onlyGA = False
    func = 'mean'
    funclist = ('med', 'mean')
    freq = 'M'
#    freq = _c.FR_QTRSFEB
    fqname = freq_names[climpy.check_freq(freq)][3:]
    orientation = 'horizontal'
    reference = 'G'
    reference = 'N'
    #
    quantilelist = (0, 0.25)
    stationlist = ('02226500', '02228000', '02314500',
                   '02353000', '02353500', '02356000', '02357000')
    phasenames = ('CN', 'WN')

if 0:
    fig = pylab.figure()
    fsp = fig.add_subplot(221)
    plot_val_table(fsp, 'mean', freq, 0, stationlist)
    fsp = fig.add_subplot(222)
    plot_val_table(fsp, 'med', freq, 0, stationlist)
    fsp = fig.add_subplot(223)
    plot_val_table(fsp, 'mean', freq, 0.25, stationlist)
    fsp = fig.add_subplot(224)
    plot_val_table(fsp, 'med', freq, 0.25, stationlist)

if 1:
    for quantile in (0.25, 0):
        for func in ('mean', 'med'):
            qtlname = '%03i' % (100 * quantile)
            stationlist = ('02226500', '02228000', '02314500')
            figsize = [_ * 2 for _ in (4.5, 3)]
            fig = plot_comparison(stationlist, quantile, func, figsize=figsize)
            fig.savefig("Q%s_%s_SE_compa.png" % (qtlname, func), dpi=720)
            #
            stationlist = ('02353000', '02356000', '02357000', '02353500')
            figsize = [_ * 2 for _ in (4.5, 4)]
            fig = plot_comparison(stationlist, quantile, func, figsize=figsize)
            fig.savefig("Q%s_%s_SW_compa.png" % (qtlname, func), dpi=720)

