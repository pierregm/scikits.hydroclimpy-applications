"""
Created on May 17, 2010

@author: pierregm
"""

import numpy as np
import scikits.hydroclimpy as hydro
import scikits.hydroclimpy.enso as enso

from enthought.chaco.api import AbstractOverlay, BaseXYPlot
from enthought.enable.api import ColorTrait
from enthought.traits.api import Array, Instance, Int, List, Color, \
    on_trait_change

from timescales import to_seconds_from_epoch





class ENSOOverlay(AbstractOverlay):
    #
    ensoi = Instance(enso.ENSOIndicator,
                     desc="ENSO indicator (JMAI, ONI...)")
    value = Int(desc="Value corresponding to the ENSO phase")
    starting_dates = Array(desc="Starting dates of the ENSO phase")
    ending_dates = Array(desc="Ending dates of the ENSO phase")

    source = Instance(BaseXYPlot, desc="Plot of which to add the overlay")
    fill_color = ColorTrait((0.5, 0.5, 0.5, 1))
    alpha = 0.3
    polygons = List
    border_color = ColorTrait((0, 0, 0.7, 1))
    border_width = Int(1)
    #
    @on_trait_change("ensoi,value")
    def get_dates(self):
        try:
            ensoi = self.ensoi.indices
        except AttributeError:
            # In case self.ensoi hasn't been initialized yet...
            return
        # Make sure the dates are in days
        dates = ensoi.dates.asfreq("D", relation="start")
        value = self.value
        # Group the data
        klust = hydro.Cluster(ensoi.series.filled(-9), 0)
        selected = (klust.uniques == value)
        # Get the start and ending dates
        start_idx = klust.starts[selected]
        self.starting_dates = to_seconds_from_epoch(dates[start_idx])
        end_idx = start_idx + klust.sizes[selected]
        self.ending_dates = to_seconds_from_epoch(dates[end_idx])

    def restrict_dates(self):
        # Find the first and last dates of the current plot
        index_range = self.source.index_mapper.range
        (current_start, current_end) = (index_range.low, index_range.high)
        # Get the boundaries of the ENSO phase
        (enso_start, enso_end) = (self.starting_dates, self.ending_dates)

        restriction = (enso_end >= current_start) & (enso_start <= current_end)
        start = np.maximum(enso_start[restriction], current_start)
        end = np.minimum(enso_end[restriction], current_end)
        return (start, end)

    def get_polygons(self):
        source = self.source
        value_range = source.value_mapper.range
        (yb, yt) = (value_range.low, value_range.high)
        (start, end) = self.restrict_dates()
        #
        polygons = []
        for (xl, xr) in zip(start, end):
            p = np.array([[xl, yb], [xr, yb], [xr, yt], [xl, yt]])
#            print "Adding polygon: %s" % p, "(%s->%s)" % (s, e)
            polygons.append(source.map_screen(p))
        self.polygons = polygons
        return polygons

    def overlay(self, component, gc, view_bounds=None, mode="normal"):
        """
        Draws this overlay onto 'component', rendering onto 'gc'.
        """
        gc.save_state()
        polygons = self.get_polygons()
        try:
            gc.translate_ctm(*component.position)
            gc.set_alpha(self.alpha)
            gc.set_fill_color(self.fill_color_)
            gc.set_line_width(self.border_width)
            gc.set_stroke_color(self.border_color_)
            for p in polygons:
                gc.begin_path()
                gc.lines(p)
                gc.fill_path()
        finally:
            gc.restore_state()
        return

    def __init__(self, ensoi, **kwargs):
        super(AbstractOverlay, self).__init__(**kwargs)
        self.ensoi = ensoi
        value = self.value or kwargs.pop("value", 0)
        self.get_dates()





class ElNinoOverlay(ENSOOverlay):
    value = Int(+1)
    fill_color = ColorTrait((1.0, 0.8, 0.2, 1.0))
    border_color = ColorTrait((1.0, 0.8, 0.2, 1.0))

class NeutralOverlay(ENSOOverlay):
    value = Int(0)
    fill_color = ColorTrait((0.4, 0.6, 0.2, 1.0))
    border_color = ColorTrait((0.4, 0.6, 0.2, 1.0))

class LaNinaOverlay(ENSOOverlay):
    value = Int(-1)
    fill_color = ColorTrait((0.4, 0.4, 0.8, 1.0))
    border_color = ColorTrait((0.4, 0.4, 0.8, 1.0))
