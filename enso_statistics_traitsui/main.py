"""
Created on May 19, 2010

@author: pierregm
"""

import os

import numpy as np

import scikits.hydroclimpy.enso as enso

from enthought.traits.api import CTrait, DelegatesTo, HasTraits, Instance, Range, Str, on_trait_change
from enthought.traits.ui.api import View, Item, Group, HSplit


import basepanels
from basepanels import *




class GlobalContainer(HasTraits):
    #
    default_ensoi = {"ONI":enso.load_oni(),
                     "JMAI":enso.load_jma()}
    #
    station_finder = Instance(StationFinder)
    station_selector = Instance(StationSelector)
    observation_selector = Instance(ObservationSelector)
    ensoi_selector = Instance(ENSOISelector)
    period_selector = Instance(PeriodSelector)
    #
    info_tab = Instance(StationInfoPanel,
                        label="Station Information",
                        desc="Generic information about the COOP station")
#    configuration_tab = Instance(ConfigurationPanel,
#                                 label="Extra configuration")
    averages_tab = Instance(AveragesStatsPanel,
                            label="Averages/Anomalies")
    distributions_tab = Instance(DistributionPanel,
                                 label="Distribution")
    series_tab = Instance(SeriesPanel,
                          label="Series")
    #
    coopid = Str
#    period = DelegatesTo("extras")
    period = Str
    period_selector = Instance(PeriodSelector)
    observation = DelegatesTo("observation_selector")
    ensoi = Enum("ONI", "JMAI")
    #
    traits_view = View(Item(name="station_finder",
                            style="custom", show_label=False),
                       HSplit(Item(name="station_selector",
                                   style="custom", show_label=False,
                                   padding=10),
                              Item(name="observation_selector",
                                   style="custom", show_label=False)),
                       Group(
                             Item(name="info_tab",
                                  style='custom', show_label=False),
                             Item(name="averages_tab",
                                  style='custom', show_label=False),
                             Item(name="distributions_tab",
                                  style='custom', show_label=False),
                             Item(name="series_tab",
                                  style='custom', show_label=False),
#                             Item(name="configuration_tab",
#                                  style='custom', show_label=False),
                             layout="tabbed"),
                       resizable=True)
    #
    def _update_available_stations(self):
#        available_stations = self.station_finder.available_stations
        self.station_selector.available_stations = self.station_finder.available_stations
    #
    def _update_selected_coopid(self):
        self.coopid = coopid = self.station_selector.selected_coopid
        print "Container.coopid changed to %s" % coopid
        self.info_tab.coopid = coopid
        self.averages_tab.coopid = coopid
        self.distributions_tab.coopid = coopid
        self.series_tab.coopid = coopid
    #
    def _update_observation(self):
        observation = self.observation_selector.observation
        print "Container.observation changed to %s" % observation
        self.averages_tab.observation = observation
        self.distributions_tab.observation = observation
        self.series_tab.observation = observation

#    @on_trait_change("ensoi")
#    def _update_ensoi(self):
#        print "Container.update_ensoi"
#        ensoi = self.ensoi
#        self.averages_tab.ensoi = ensoi
#        self.distributions_tab.ensoi = ensoi
#        self.series_tab.ensoi = self.default_ensoi[ensoi]


    def __init__(self, dbname, **kwargs):
        # Initialize the StationFinder and the other selectors
        self.station_finder = finder = StationFinder(dbname)
        self.observation_selector = ObservationSelector()
        self.station_selector = selector = StationSelector()#available_stations=self.station_finder_panel.all_stations)
        self.period_selector = PeriodSelector()
        self.ensoi_selector = ENSOISelector()
        selector.available_stations = finder.available_stations
        # Initialize the tabs
        self.info_tab = StationInfoPanel(dbname=dbname)
        self.averages_tab = AveragesStatsPanel(dbname,
                                               observation=self.observation,
                                               )
        self.distributions_tab = DistributionPanel(dbname=dbname,
                                                   observation=self.observation,
                                                   )
        self.series_tab = SeriesPanel(dbname,
                                      observation=self.observation,
                                      )
        # Set the period/ENSOI selectors for each tab
        self.averages_tab.period_selector = \
            self.distributions_tab.period_selector = self.period_selector
        self.averages_tab.ensoi_selector = \
            self.distributions_tab.ensoi_selector = \
            self.series_tab.ensoi_selector = self.ensoi_selector
        #
        self.station_finder.on_trait_change(self._update_available_stations,
                                            "available_stations")
        self.station_selector.on_trait_change(self._update_selected_coopid,
                                              "selected_coopid")
        self.observation_selector.on_trait_change(self._update_observation,
                                                  "observation")





if __name__ == '__main__':

    dbname = "~/workspace/hydrosandbox/storing/coaps.sqlite"
    dbname = os.path.expanduser(dbname)

    container = GlobalContainer(dbname)
    container.configure_traits()
    finder = container.station_finder
    selector = container.station_selector
