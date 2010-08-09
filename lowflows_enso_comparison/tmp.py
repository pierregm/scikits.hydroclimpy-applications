"""Test for recordarrays ordering at instantiation."""

import numpy as np
import scikits.timeseries as TS
from numpy.testing import *

# Arrays a and b are ordered in descending order, and the dates are in the
# inverse chronological order.
# Once the dates are ordered in chronological order, we expect the arrays a
and
# b to be in ascending order.

a = np.array([4, 3, 2, 1])
b = np.array([14, 13, 12, 11])
date_str = ['2000-01-01 04:00', '2000-01-01 03:00', '2000-01-01 02:00',
'2000-01-01 01:00']
dates = [TS.Date('S', date) for date in date_str]

trec = TS.fromrecords(zip(a, b), dates, names=['a', 'b'])

assert_array_equal(np.diff(trec.dates), 3600)   # dates are in chronological
order
assert_array_equal(np.diff(trec['a']), 1)  # This fails
assert_array_equal(np.diff(trec['b']), 1)  # This fails.
