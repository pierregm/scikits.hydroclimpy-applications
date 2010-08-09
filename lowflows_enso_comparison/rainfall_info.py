
import itertools
import numpy as np
import scikits.timeseries.extras as extras
import scikits.hydroclimpy as climpy
import scikits.hydroclimpy.io.coaps as coaps



COAPS_SE = [(-82.52, 31.52, '90211', 'Alma CAA Airport'),
            (-82.82, 31.52, '92783', 'Douglas'),
            (-82.80, 31.02, '94429', 'Homerville'), ]
COAPS_SW = [(-84.12, 31.52, '90140', 'Albany'),
            (-84.18, 31.79, '91500', 'Camilla'),
            (-84.77, 31.17, '92153', 'Colquitt'),
            (-84.77, 31.77, '92450', 'Cuthbert')]
ndtype = np.dtype([('lon', float), ('lat', float), ('site_no', '|S5'),
                   ('desc', '|S20')])
COAPS_SE = np.array(COAPS_SE, dtype=ndtype)
COAPS_SW = np.array(COAPS_SW, dtype=ndtype)


end_date = climpy.Date('D', '2009-02-28')
COAPS_data = {}
for site_no in itertools.chain(COAPS_SE['site_no'], COAPS_SW['site_no']):
    data = coaps.load_coaps_data(site_no)['rain']
    data = data.fill_missing_dates()
    COAPS_data[site_no] = data.adjust_endpoints(end_date=end_date)

table_template = []
csc = "*"
separator = csc.join(['-'*7, '-'*21, '-'*12, '-'*6, '-'*6, '-'*9])
for region in (COAPS_SW, COAPS_SE):
    table_template.append("%s%s%s" % (csc, separator, csc))
    for (site_no, desc) in zip(region['site_no'], region['desc']):
        data = COAPS_data[site_no]
        start_date = data.dates[0].strfmt("%m/%d/%Y")
        mdata = extras.accept_atmost_missing(data.convert('M'), 0.1)
        nbtotal = len(mdata)
        nbvalid = mdata.any(-1).filled(False).sum()
        row = csc.join([" %5s " % site_no, "%20s " % desc,
                        " %10s " % start_date,
                        " %4i " % nbtotal, " %4i " % nbvalid, 
                        " (%03.1f%%) " % (nbvalid*100./nbtotal)])
        table_template.append("%s%s%s" % (csc, row, csc))
table_template.append("%s%s%s" % (csc, separator, csc))

print "\n".join(table_template)


if __name__ == "__main__":
    print "Hello World";
    print COAPS_data

