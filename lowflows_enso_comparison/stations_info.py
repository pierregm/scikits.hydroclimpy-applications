# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="pierregm"
__date__ ="$Sep 28, 2009 5:17:32 PM$"

import itertools
import numpy as np
import scikits.timeseries.extras as extras
import scikits.hydroclimpy as climpy
import scikits.hydroclimpy.io.usgs as usgs


USGS_SE = [(-82.32, 31.24, '02226500', 'Satilla River near Waycross, GA'),
           (-81.87, 31.22, '02228000', 'Satilla River at Atkinson, GA'),
           (-82.56, 30.68, '02314500', 'Suwannee River at US 441, Fargo, GA')]
USGS_SW = [(-84.34, 31.31, '02353000', 'Flint River at Newton, GA'),
           (-84.55, 31.38, '02353500', 'Ichawaynochaway Creek at Milford, GA'),
           (-84.58, 30.91, '02356000', 'Flint River at Bainbridge, GA'),
           (-84.74, 31.04, '02357000', 'Spring Creek near Iron City, GA')]
ndtype = np.dtype([('lon', float), ('lat', float), ('site_no', '|S8'),
                   ('desc', '|S40')])
USGS_SE = np.array(USGS_SE, dtype=ndtype)
USGS_SW = np.array(USGS_SW, dtype=ndtype)


end_date = climpy.Date('D', '2009-02-28')
USGS_data = {}
for site_no in itertools.chain(USGS_SE['site_no'], USGS_SW['site_no']):
    data = usgs.load_usgs_flows(site_no).fill_missing_dates()
    USGS_data[site_no] = data.adjust_endpoints(end_date=end_date)

table_template = []
csc = "*"
separator = csc.join(['-'*10, '-'*41, '-'*12, '-'*6, '-'*6, '-'*9])
for region in (USGS_SW, USGS_SE):
    table_template.append("%s%s%s" % (csc, separator, csc))
    for (site_no, desc) in zip(region['site_no'], region['desc']):
        data = USGS_data[site_no]
        start_date = data.dates[0].strfmt("%m/%d/%Y")
        mdata = extras.accept_atmost_missing(data.convert('M'), 0.1)
        nbtotal = len(mdata)
        nbvalid = mdata.any(-1).filled(False).sum()
        row = csc.join([" %8s " % site_no, "%40s " % desc,
                        " %10s " % start_date,
                        " %4i " % nbtotal, " %4i " % nbvalid, 
                        " (%03.1f%%) " % (nbvalid*100./nbtotal)])
        table_template.append("%s%s%s" % (csc, row, csc))
table_template.append("%s%s%s" % (csc, separator, csc))


if __name__ == "__main__":
    print "\n".join(table_template)
