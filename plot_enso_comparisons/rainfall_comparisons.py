'''
Created on Sep 25, 2009

@author: pierregm
'''

import numpy as np
import numpy.ma as ma
import matplotlib.pylab as m

from scikits.hydroclimpy.plotlib.ensotools import ENSOcolors
ecol = ENSOcolors['lines']

"""
SW_S (SW_M)
    Average monthly precipitation for the SouthWestern stations
    with the Standard (or Modified) JMAI.
    Keys are 'G' (global), 'N' (Neutral), 'C' (La Nina), 'W' (Warm)
    Values are organized per month (DJFMAMJJASON)
SE_S (SE_M)
    ... for the SouthEastern stations
"""


SW_M = {
'G' : [3.40, 3.91, 4.18, 4.53, 3.39, 3.00, 4.10, 4.73, 3.73, 3.36, 1.92, 2.56],
'N' : [3.33, 4.11, 4.05, 4.73, 3.24, 2.91, 4.01, 4.84, 3.98, 3.53, 1.99, 2.65],
'C' : [3.04, 3.13, 3.68, 3.50, 3.82, 3.93, 3.36, 5.11, 3.75, 2.32, 1.86, 1.80],
'W' : [3.91, 4.32, 5.12, 5.37, 3.60, 2.54, 4.72, 4.17, 3.08, 3.75, 1.80, 3.26],
'CN-sig' : [0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1],
'WN-sig' : [0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1]
        }
SW_S = {
'G' : [3.40, 3.91, 4.18, 4.53, 3.39, 3.00, 4.10, 4.73, 3.73, 3.36, 1.92, 2.56],
'N' : [3.38, 4.06, 3.96, 4.56, 3.50, 2.89, 3.90, 4.67, 3.68, 3.16, 2.00, 2.68],
'C' : [3.03, 2.98, 3.71, 3.80, 3.26, 3.22, 4.56, 5.01, 3.50, 3.37, 1.85, 1.74],
'W' : [3.84, 4.57, 5.32, 5.31, 3.28, 3.00, 4.08, 4.56, 4.12, 3.75, 1.80, 3.25],
'CN-sig' : [0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1],
'WN-sig' : [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        }
#

SE_M = {
'G' : [3.40, 3.91, 4.18, 4.53, 3.39, 3.00, 4.10, 4.73, 3.73, 3.36, 1.92, 2.56],
'N' : [2.69, 3.50, 3.91, 4.34, 2.69, 2.89, 4.54, 4.89, 4.61, 3.60, 2.25, 1.92],
'C' : [2.71, 2.77, 2.19, 2.70, 3.23, 2.86, 4.13, 5.68, 5.90, 3.40, 1.82, 1.17],
'W' : [3.68, 3.86, 4.45, 4.54, 2.82, 2.49, 4.82, 4.77, 4.09, 3.45, 2.15, 3.00],
'CN-sig' : [0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1],
'WN-sig' : [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
        }
SE_S = {
'G' : [3.40, 3.91, 4.18, 4.53, 3.39, 3.00, 4.10, 4.73, 3.73, 3.36, 1.92, 2.56],
'N' : [2.69, 3.46, 3.62, 4.10, 2.72, 2.64, 4.56, 4.86, 4.63, 3.33, 2.24, 2.01],
'C' : [2.77, 2.68, 2.67, 3.28, 2.51, 3.28, 4.82, 5.42, 4.60, 3.83, 1.89, 1.02],
'W' : [3.67, 4.07, 4.89, 4.58, 3.34, 2.65, 4.22, 4.88, 5.17, 3.70, 2.15, 2.99],
'CN-sig' : [0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1],
'WN-sig' : [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        }


fig = m.figure(figsize=(10.25, 4))
baserange = range(1, 13)
defmarker = dict(marker='o', ls='-', ms=6)
sigmarker = dict(marker='s', ls='', ms=8)

fsp = fig.add_subplot(221)
legG = fsp.plot(baserange, SW_M['G'], c=ecol['G'], **defmarker)
legN = fsp.plot(baserange, SW_M['N'], c=ecol['N'], **defmarker)
legC = fsp.plot(baserange, SW_M['C'], c=ecol['C'], **defmarker)
legS = fsp.plot(baserange,
                ma.array(SW_M['C'], mask=np.logical_not(SW_M['CN-sig'])), 
                c=ecol['C'], **sigmarker)
legW = fsp.plot(baserange, SW_M['W'], c=ecol['W'], **defmarker)
fsp.plot(baserange, ma.array(SW_M['W'], mask=np.logical_not(SW_M['WN-sig'])),
         c=ecol['W'], **sigmarker)
fsp.set_title('Southwestern (M)')

fsp = fig.add_subplot(223)
legNS = fsp.plot(baserange, SW_S['G'], c=ecol['G'], **defmarker)
fsp.plot(baserange, SW_S['N'], c=ecol['N'], **defmarker)
fsp.plot(baserange, SW_S['C'], c=ecol['C'], **defmarker)
fsp.plot(baserange, ma.array(SW_S['C'], mask=np.logical_not(SW_S['CN-sig'])),
         c=ecol['C'], **sigmarker)
fsp.plot(baserange, SW_S['W'], c=ecol['W'], **defmarker)
fsp.plot(baserange, ma.array(SW_S['W'], mask=np.logical_not(SW_S['WN-sig'])),
         c=ecol['W'], **sigmarker)
fsp.set_title('Southwestern (S)')


fsp = fig.add_subplot(222)
fsp.plot(baserange, SE_M['G'], c=ecol['G'], **defmarker)
fsp.plot(baserange, SE_M['N'], c=ecol['N'], **defmarker)
fsp.plot(baserange, SE_M['C'], c=ecol['C'], **defmarker)
fsp.plot(baserange, ma.array(SE_M['C'], mask=np.logical_not(SE_M['CN-sig'])),
         c=ecol['C'], **sigmarker)
fsp.plot(baserange, SE_M['W'], c=ecol['W'], **defmarker)
fsp.plot(baserange, ma.array(SE_M['W'], mask=np.logical_not(SE_M['WN-sig'])),
         c=ecol['W'], **sigmarker)
fsp.set_title('Southeastern (M)')
fsp = fig.add_subplot(224)
fsp.plot(baserange, SE_S['G'], c=ecol['G'], **defmarker)
fsp.plot(baserange, SE_S['N'], c=ecol['N'], **defmarker)
fsp.plot(baserange, SE_S['C'], c=ecol['C'], **defmarker)
fsp.plot(baserange, ma.array(SE_S['C'], mask=np.logical_not(SE_S['CN-sig'])),
         c=ecol['C'], **sigmarker)
fsp.plot(baserange, SE_S['W'], c=ecol['W'], **defmarker)
fsp.plot(baserange, ma.array(SE_S['W'], mask=np.logical_not(SE_S['WN-sig'])),
         c=ecol['W'], **sigmarker)
fsp.set_title('Southeastern (S)')

for fsp in fig.axes:
    fsp.set_ylim(1, 6)
    fsp.set_xlim(0, 13)
    fsp.xaxis.set_major_locator(m.MultipleLocator(1))
    if not fsp.is_last_row():
        fsp.set_xticklabels('')
    else:
        fsp.set_xticklabels(' DJFMAMJJASON')
    if not fsp.is_first_col():
        fsp.set_yticklabels('')

fig.text(0.025, 0.5, "Average rainfall (mm/d)", fontweight='bold',
         ha='center', va='center', rotation=90)
fig.legend((legG, legN, legC, legW, legS, legNS),
           (u'Global', u'Neutral', u'La Ni\xf1a', u'El Ni\xf1o', 
            u'Signif.', u'Non signif.'),
           1)
fig.subplots_adjust(left=0.07, right=0.80, wspace=0.1)
fig.savefig('rainfall_comparison.png', dpi=540)
m.show()
