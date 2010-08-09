"""
Created on May 17, 2010

@author: pierregm



"""

import numpy as np

from enthought.chaco.api import ArrayDataSource, BarPlot, DataRange1D, LabelAxis, LinearMapper, OverlayPlotContainer
from enthought.traits.api import Array, Float, Instance, Int, List, Property


class MultiBarPlot(OverlayPlotContainer):
    """
    Convenience class to draw multiple barplots in the same overlay.
    
    Attributes
    ----------
    
    rawdata : array
        Array of data to be plotted.
        The array must be 1D if it is structured, 2D otherwise.
    nbvars : int
        Number of independent variables.
        If `rawdata` is structured, `nbvars` is the number of fields.
        Otheriwse, it is the number of columns of the 2D array.
    nbdata : int
        Number of data for each variable.
        `nbdata` is the number of data in each field (or in each column)

    """
    rawdata = Array(desc="Data")
    #
    nbvars = Property(Int, depends_on="rawdata",
                      desc="Number of independent data (bins)")
    nbdata = Property(Int, depends_on="rawdata",
                      desc="Number of categories in each bin")
    #
    indices = Property(List, depends_on=("rawdata", "bar_width"),)
    values = Property(List, depends_on="rawdata")
    barplots = List(desc="List of barplots")
    bar_width = Float(10)
    labels = List
    fill_colors = List
    legend_labels = List
    bottom_axis = Instance(LabelAxis)
    #
    def _get_nbvars(self):
        rawdata = self.rawdata
        nbvars = len(rawdata.dtype.names or ())
        # No named fields: take the 2nd dimension
        if nbvars == 0:
            if rawdata.ndim == 2:
                nbvars = rawdata.shape[1]
            else:
                errmsg = "The input data should be 2D atmost"
                raise ValueError(errmsg)
        return nbvars
    #
    def _get_nbdata(self):
        return len(self.rawdata)
    #
    def _get_indices(self):
        (nbdata, nbvars, rawdata) = (self.nbdata, self.nbvars, self.rawdata)
        # Get the size of each individual bin
        bin_width = self.bar_width / nbvars
        # Construct an array of indices
        offset = (nbvars - 1) / 2.
        indices = np.arange(nbdata) + \
                  (np.arange(nbvars)[:, None] - offset) * bin_width
        return indices
    #
    def _get_values(self):
        (nbvars, rawdata) = (self.nbvars, self.rawdata)
        if rawdata.dtype.names:
            values = rawdata.view((float, nbvars)).T
        else:
            values = values.T
        return values

    def _create_barplots(self):
        # Get the size of each individual bin
        bin_width = self.bar_width / self.nbvars
        barplots = []
        for (i, v) in zip(self.indices, self.values):
            index = ArrayDataSource(i)
            index_range = DataRange1D(index,
                                      low= -0.5,
                                      high=self.nbdata + 0.5,
                                      tight_bounds=True)
            index_mapper = LinearMapper(range=index_range)
            #
            value = ArrayDataSource(v)
            value_range = DataRange1D(value, tight_bounds=True)
            value_mapper = LinearMapper(range=value_range)
            barplot = BarPlot(index=index,
                              index_mapper=index_mapper,
                              value=value,
                              value_mapper=value_mapper,
                              line_color=0x111111,
                              labels=self.labels,
                              bar_width=bin_width,
                              antialias=True)
            barplot.padding = 30
            barplots.append(barplot)
        self.barplots = barplots
        return barplots

    def _update_barplots(self):
        values = self.values
        bounds = (values.min(), values.max())
        for (plot, index, value) in zip(self.barplots, self.indices, values):
            plot.index.set_data(index)
            plot.value.set_data(value)
            plot.value_range.set_bounds(*bounds)

    def _rawdata_changed(self):
        if len(self.barplots):
            self._update_barplots()
        else:
            self._create_barplots()
    #
    def _legend_labels_default(self):
        labels = self.rawdata.dtype.names
        if labels is None:
            labels = range(self.nbvars)
        return labels


