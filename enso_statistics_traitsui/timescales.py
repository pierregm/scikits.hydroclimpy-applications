"""
Created on May 17, 2010

@author: pierregm
"""

from datetime import MAXYEAR, MINYEAR
import numpy as np

from enthought.chaco.scales.api import TimeScale, CalendarScaleSystem, \
    MDYScales, dt_to_sec
from enthought.chaco.scales.safetime import datetime




def to_seconds_from_epoch(dates, epoch=None):
    """
    Calculates the number of seconds from `epoch`

    Parameters
    ----------
    dates : var
        Array of dates, as datetime objects (or objects having a `.toordinal`
        method).
    epoch : var
        Reference date. By default, use the Unix epoch (1970/01/01)
    """
    # Get the proleptic gregorian nb of days
    try:
        ordinals = dates.toordinals()
    except AttributeError:
        ordinals = np.array([_.toordinal() for _ in dates])
    # Substract the Epoch
    try:
        epoch = epoch.toordinal()
    except AttributeError:
        epoch = 719163.
    ordinals -= epoch
    # Transforms to seconds
    ordinals *= 24 * 3600
    return ordinals


TimeScale.SECS_PER_UNIT['year_of_decade'] = 3652.5 * 24 * 3600
TimeScale.CALENDAR_UNITS = ("day_of_month", "month_of_year", "year_of_decade")
MYScales = MDYScales + [TimeScale(year_of_decade=range(1, 10, 2)),
                        TimeScale(year_of_decade=(1, 6)),
                        TimeScale(year_of_decade=(1,))]


def cal_ticks(self, start, end):
    """ ticks() method for calendar-based intervals """
    # Make sure `start` is a proper datetime object
    try:
        start = datetime.fromtimestamp(start)
    except ValueError:
        start = datetime(MINYEAR, 1, 1, 0, 0, 0)
    # Make sure `end` is a proper datetime object
    try:
        end = datetime.fromtimestamp(end)
    except ValueError:
        end = datetime(MAXYEAR, 1, 1, 0, 0, 0)

    if self.unit == "day_of_month":
        s = start.year + 1 / 12.0 * start.month
        e = end.year + 1 / 12.0 * end.month
        num_months = int(round((e - s) * 12)) + 1   # add 1 for fencepost
        start_year = start.year
        start_month = start.month
        ym = [divmod(i, 12) for i in range(start_month - 1,
                                           start_month - 1 + num_months)]
        months = [start.replace(year=start_year + y, month=m + 1, day=1)
                  for (y, m) in ym]
        ticks = [dt.replace(day=i) for dt in months for i in self.vals]

    elif self.unit == "month_of_year":
        years_range = range(start.year, end.year + 1)
        years = [start.replace(year=newyear, day=1) for newyear in years_range]
        ticks = [dt.replace(month=i, day=1) for dt in years for i in self.vals]

    elif self.unit == "year_of_decade":
        years_range = np.arange(start.year, end.year + 1)
        selected = np.logical_or.reduce([years_range % 10 == (i - 1) for i in self.vals])
        ticks = [datetime(year=i, month=1, day=1) for i in years_range[selected]]

    else:
        raise ValueError("Unknown calendar unit '%s'" % self.unit)

    if len(ticks) > 0:
        # Find the first and last index in all_ticks that falls within (start,end)
        for start_ndx in range(len(ticks)):
            if ticks[start_ndx] >= start:
                break
        for end_ndx in range(len(ticks) - 1, 0, -1):
            if ticks[end_ndx] <= end:
                break
        ticks = ticks[start_ndx : end_ndx + 1]

    return map(dt_to_sec, ticks)

TimeScale.cal_ticks = cal_ticks


