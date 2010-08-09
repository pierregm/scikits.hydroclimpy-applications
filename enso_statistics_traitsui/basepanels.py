"""
Created on May 17, 2010

@author: pierregm
"""

from traceback import print_exc

import numpy as np
import numpy.ma as ma

import scikits.hydroclimpy as hydro
import scikits.hydroclimpy.enso as enso
import scikits.hydroclimpy.io.sqlite as sql

import geopy

from enthought.chaco.api import ArrayDataSource, DataRange1D, LabelAxis, Legend, LinearMapper, LinePlot, OverlayPlotContainer, PlotAxis, PlotLabel, add_default_grids
from enthought.chaco.scales_tick_generator import ScalesTickGenerator
from enthought.chaco.scales_axis import PlotAxis as ScalesPlotAxis
from enthought.chaco.tools.api import PanTool, ZoomTool, DragZoom, LegendTool, RangeSelection
from enthought.enable.component_editor import ComponentEditor
from enthought.traits.api import Any, Array, Bool, CFloat, DelegatesTo, Dict, Enum, Float, HasTraits, Instance, List, Property, Range, Str, on_trait_change
from enthought.traits.ui.api import EnumEditor, Group, HGroup, HSplit, Item, TextEditor, View

import multibarplot
from multibarplot import MultiBarPlot
from timescales import CalendarScaleSystem, MYScales, to_seconds_from_epoch
from zoom_plot_container import ReversedZoomOverlay, ZoomedPlotContainer
from enso_info import ElNinoOverlay, NeutralOverlay, LaNinaOverlay
import misc_tools
from misc_tools import print_decimal_coordinates, select_stations_around_reference

periods_dict = dict(MON=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    JFM=['JFM', 'AMJ', 'JAS', 'OND'],
                    DJF=['DJF', 'MAM', 'JJA', 'SON'],
                    NDJ=['NDJ', 'FMA', 'MJJ', 'ASO'])

oni = enso.load_oni()
jmai = enso.load_jma()



class PeriodSelector(HasTraits):
    period = Enum("MON", "JFM", "DJF", "NDJ")
    entries = dict(MON=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                  JFM=['JFM', 'AMJ', 'JAS', 'OND'],
                  DJF=['DJF', 'MAM', 'JJA', 'SON'],
                  NDJ=['NDJ', 'FMA', 'MJJ', 'ASO'])
    seasons = Property(depends_on="selector")

    def _get_seasons(self):
        return self.entries[self.period]

    traits_view = View(Item(name="period",
                            editor=EnumEditor(
                                         values={"MON": "1: Monthly",
                                                 "JFM": "2: JFM/AMJ/JAS/OND",
                                                 "DJF": "3: DJF/MAM/JJA/SON",
                                                 "NDJ": "4: NDJ/FMA/MJJ/ASO"})))



class ENSOISelector(HasTraits):
    ensoi_str = Enum("ONI", "JMAI")
    ensoi_obj = Property(depends_on="ensoi_str")
    traits_view = View(Item(name="ensoi_str", label="ENSOI"))
    #
    def _get_ensoi_obj(self):
        ensoi = self.ensoi_str
        if ensoi == "ONI":
            ensoi_obj = oni
        elif ensoi == "JMAI":
            ensoi_obj = jmai
        return ensoi_obj



class ObservationSelector(HasTraits):
    observation = Enum("rain", "tmin", "tmax")
    traits_view = View(Item(name="observation",
                            editor=EnumEditor(values={'rain':"Rain",
                                                      'tmin':"Min. temperatures",
                                                      'tmax':"Max. temperatures"})),)





class StationInfoPanel(HasTraits):
    """
    Display some information about the selected station.

    The information is stored in a SQLite database.
    

    Attributes
    ----------
    dbname: string
        String representing the path of the database.
    stations: string
        Name of the table storing the station information
    coopid: string
        COOP id of the station
    """
    dbname = Str
    stations_table = Str("stations_list")
    coopid = Str(desc="COOP identification code", label="COOP #")
    name = Str(desc="Station name", label="Station Name")
    latitude = CFloat
    longitude = CFloat
    elevation = CFloat(desc="Elevation", label="Elevation (m)")
    latitude_str = Property(Str, depends_on="latitude")
    longitude_str = Property(Str, depends_on="longitude")
    counties_list = Str
    counties = Property(List, depends_on='counties_list',
                        label="Counties represented")

    traits_view = View(Item(name="coopid"),
                       Item(name="name"),
                       Item(name="latitude_str"),
                       Item(name="longitude_str"),
                       Item(name="elevation"),
                       Item(name="counties", style='readonly'
                            ))

    #
    def _get_counties(self):
        """
    Transforms the colon-separated string of the field 'COUNTY_REPRESENT' into
    an actual list.
        """
        counties = [_.capitalize() for _ in self.counties_list.split(":")]
        return counties
    #
    def _coopid_changed(self, coopid):
        """
    
        """
        connection = sql.connect(self.dbname, detect_types=sql.DETECT_TYPES)
        fields = "STATION_NAME, LATITUDE, LONGITUDE, ELEVATION, COUNTY_REPRESENT"
        query_template = "select %s from %s where COOPID='%s'"
        query = query_template % (fields, self.stations_table, coopid)
        print "query_template:%s - dbname:%s" % (query, self.dbname)
        try:
            info = connection.execute(query).fetchone()
        finally:
            connection.close()
        #
        fnames = ("name", "latitude", "longitude", "elevation", "counties_list")
        params = dict(coopid=coopid)
        params.update((k, v) for (k, v) in zip(fnames, info))
        params["elevation"] = params["elevation"] or np.nan
        print "#%s: %s" % (coopid, params)
        (self.name, self.latitude, self.longitude, self.elevation, self.counties_list) = info
        return params

    def _get_latitude_str(self):
        return print_decimal_coordinates(self.latitude, is_lat=True)

    def _get_longitude_str(self):
        return print_decimal_coordinates(self.longitude, is_lat=False)





class AveragesStatsPanel(OverlayPlotContainer):

    default_ylabel = {"rain": u"Precipitation [mm]",
                      "tmin": u"Min. temperatures [\u00B0C]",
                      "tmax": u"Max. temperatures [\u00B0C]"}

    dbname = Str
    coopid = Str
    observation = Enum("rain", "tmin", "tmax")
    #
    rawdata = Array(dtype=[(_, float) for _ in "ACNW"])
    reference = Property(Array, depends_on=("rawdata", "baseline"))
    data = Property(Array, depends_on=("rawdata", "reference"))
    #
    period_selector = Instance(PeriodSelector)
    period = DelegatesTo("period_selector")
    labels = DelegatesTo("period_selector", prefix="seasons")
    baseline_choices = ["None", "All years",
                        u"La Ni\xF1a", "Neutral", u"El Ni\xF1o"]
    baseline = Enum(*baseline_choices)
    #
    ensoi_selector = Instance(ENSOISelector)
    ensoi_str = DelegatesTo("ensoi_selector")
    #
    plot_container = Instance(OverlayPlotContainer)
    multibarplot = Instance(MultiBarPlot)
    bottom_axis = Instance(LabelAxis)
    fill_colors = List((0x999999, 0x6666cc, 0x669933, 0xffcc33)) # GCNW
    #
    traits_view = View(HGroup(Item(name="period_selector",
                                   style="custom",
                                   show_label=False),
                              Item(name="baseline"),
                              Item("ensoi_selector",
                                   style="custom",
                                   show_label=False)),
                       Item("plot_container", editor=ComponentEditor(),
                            show_label=False,
                            width=600, height=300),
                       )

    def _get_reference(self):
        index = self.baseline_choices.index(self.baseline)
        field = [None, 'A', 'C', 'N', 'W'][index]
        if field:
            return self.rawdata[field]
        return np.zeros(self.rawdata.size, dtype=float)

    def _get_data(self):
        data = np.empty_like(self.rawdata)
        values = self.rawdata.view((float, 4)) - self.reference[:, None]
        data.flat = map(tuple, values)
        return data

    def _get_labels(self):
        labels = periods_dict.get(self.period, [])
        self.multibarplot.labels = labels
        return labels
    #
    def _update_rawdata(self):
        (period, observation) = (self.period, self.observation)
        # Get the table name
        if period == "MON":
            tbname = "averages_monthly_%s" % observation
            nbseasons = 12
        else:
            tbname = "averages_%s_%s" % (period, observation)
            nbseasons = 4
        # Construct the query
        query_tpl = "select * from %s where COOPID='%s' and ENSOI='%s'"
        query = query_tpl % (tbname, self.coopid, self.ensoi_str)
        # Get the data
        try:
            connection = sql.connect(self.dbname, detect_types=sql.DETECT_TYPES)
            records = connection.execute(query).fetchall()
        except:
            return {}
        finally:
            connection.close()
        # Process the ENSO data
        data = np.empty(nbseasons, dtype=[(_, float) for _ in "ACNW"])
        for r in records:
            data[r[3]] = r[4:]
        try:
            self.multibarplot.rawdata = data
        except AttributeError:
            pass
        self.rawdata = data

    @on_trait_change("coopid,ensoi_str,period")
    def _update_plots(self):
        self._update_rawdata()
        print "AveragesPanels._update_plots()"
        (multibarplot, bottom_axis) = (self.multibarplot, self.bottom_axis)
        if multibarplot is None:
            return
        multibarplot.rawdata = self.data
        nbdata = multibarplot.nbdata
        for plot in multibarplot.barplots:
            plot.x_mapper.range.set_bounds(-0.5, nbdata - 0.5)
        self._update_bottom_axis()
#    _coopid_changed = _period_changed = _ensoi_changed = _observation_changed = _update_plots

    @on_trait_change("observation")
    def _update_period(self):
        ylabel = self.default_ylabel[self.observation]
        if self.multibarplot is None:
            return
        self._update_plots()
        underlays = self.multibarplot.barplots[-1].underlays
        for u in underlays:
            if not isinstance(u, LabelAxis):
                u.title = self.default_ylabel[self.observation]

    def _create_bottom_axis(self):
        plot = self.multibarplot.barplots[-1]
        bottom_axis = LabelAxis(plot, orientation="bottom",
                                positions=range(0, self.multibarplot.nbdata),
                                labels=self.labels,
                                small_haxis_style=True)
        bottom_axis.tick_interval = 1.
        bottom_axis.tick_in = 0
        # 
        try:
            plot.underlays[1] = bottom_axis
        except IndexError:
            plot.underlays.append(bottom_axis)
        self.bottom_axis = bottom_axis

    def _update_bottom_axis(self):
        # Shortcuts
        multibarplot = self.multibarplot
        plots = multibarplot.barplots
        # Check the underlays of each subplot and update the LabelAxis one
        for plot in plots:
            underlays = plot.underlays
            for underlay in underlays:
                if not isinstance(underlay, LabelAxis):
                    continue
                # NEVER FORGET to reset the underlay
                underlay._invalidate()
                # Now we can set the new positions & labels
                underlay.positions = range(0, multibarplot.nbdata)
                underlay.labels = self.labels

    def _baseline_changed(self):
        self.multibarplot.rawdata = self.data

    def add_legend(self, padding=10, align="ur"):
        legend = Legend(component=self.plot_container, padding=10, align="ur")
        legend.tools.append(LegendTool(legend, drag_button="right"))
        multibarplot = self.multibarplot
        legend.plots = dict(zip(multibarplot.legend_labels,
                                multibarplot.barplots))
        self.plot_container.overlays.append(legend)

    #-------------------------------------------------------------------------

    def __init__(self, dbname, **kwargs):
        self.ensoi_selector = ENSOISelector()
        self.period_selector = PeriodSelector()
        super(OverlayPlotContainer, self).__init__(**kwargs)
        #
        self.dbname = dbname
        self.plot_container = plot_container = OverlayPlotContainer(padding=(20, 5, 5, 5))
        self.multibarplot = multibarplot = MultiBarPlot(rawdata=self.rawdata,
                                                        bar_width=0.8)
        multibarplot._create_barplots()
        multibarplot.legend_labels = self.baseline_choices[1:]
        #
        nbdata = multibarplot.nbdata
        for (plot, color) in zip(self.multibarplot.barplots, self.fill_colors):
            plot.fill_color = color
            plot.x_mapper.range.set_bounds(-0.5, nbdata - 0.5)
            plot_container.add(plot)
        #
        label = self.default_ylabel[self.observation]
        vertical_axis = PlotAxis(plot, orientation="left",
                                 title=label,)
        plot.underlays.append(vertical_axis)
        #
        self._create_bottom_axis()
        #
        self.add_legend()





class DistributionPanel(HasTraits):
    dbname = Str
    period_selector = Instance(PeriodSelector)
    period = DelegatesTo("period_selector")
    #
    seasons = DelegatesTo("period_selector")
    selected_season = Str
    season_selector = EnumEditor(values={})
    #
    ensoi_selector = Instance(ENSOISelector, label="ENSOI")
    ensoi_str = DelegatesTo("ensoi_selector")
#    seasonlist = Property(List, depends_on="period")
#    season = Enum(values="seasonlist")
    plot_container = Instance(ZoomedPlotContainer)
    #
    def _period_changed(self):
        # We can't test on a change of seasons, because seasons is a Property...
        # ...of PeriodSelector, and Properties don't advertise changes very well...
        self.season_selector.values = dict((s, "%02i: %s" % (i, s)) \
                                           for (i, s) in enumerate(self.seasons))
    #
    traits_view = View(HGroup(Item(name="period_selector",
                                   style="custom",
                                   show_label=False,
                                   padding=5),
                              Item(name="selected_season",
                                   editor=season_selector,
                                   label="Season",
#                                   show_label=False,
                                   padding=5),
                              Item(name="ensoi_selector",
                                   style="custom",
                                   show_label=False,
                                   padding=5),
                                   ),
                       Item("plot_container", editor=ComponentEditor(),
                            show_label=False,
                            width=600, height=300),
                       resizable=True,)

    def __init__(self, **kwargs):
        self.period_selector = PeriodSelector()
        self.ensoi_selector = ENSOISelector()
        super(HasTraits, self).__init__(**kwargs)
        self._period_changed()




class SeriesPanel(OverlayPlotContainer):

    default_ylabel = {"rain": u"Precipitation [mm]",
                      "tmin": u"Min. temperatures [\u00B0C]",
                      "tmax": u"Max. temperatures [\u00B0C]"}

    dbname = Str
    coopid = Str
    observation = Str
    #
    ensoi_selector = Instance(ENSOISelector)
    ensoi = DelegatesTo("ensoi_selector", prefix="ensoi_obj")
    #
    rawdata = Array
    annual = Property(Array, depends_on="rawdata")
    index = Property(List, depends_on="rawdata")
    values = Property(Array, depends_on="rawdata")
    #
    plot_container = Instance(ZoomedPlotContainer)
    reference_plot = Instance(LinePlot)
    zoomed_plot = Instance(LinePlot)
    enso_overlays = Dict
    #
    display_el_nino = Bool(False)
    display_neutral = Bool(False)
    display_la_nina = Bool(False)
    #
    traits_view = View(Item(name="plot_container",
                            editor=ComponentEditor(),
                            show_label=False,
                            width=600, height=300),
                       HGroup(Item(name="ensoi_selector",
                                   style='custom',
                                   show_label=False),
                              Item(name="display_el_nino",
                                   label=u"El Ni\xF1o",),
                              Item(name="display_neutral",
                                   label="Neutral",),
                              Item(name="display_la_nina",
                                   label=u"La Ni\xF1a"),
                              label="Display ENSO"),
                       resizable=True,
                       )

    #--- Properties ---
    def _get_annual(self):
        monthly = hydro.fromrecords(self.rawdata, freq="M")
        annual = monthly.convert("A", func=np.ma.sum)
        return annual
    #
    def _get_index(self):
        index = to_seconds_from_epoch(self.rawdata["dates"])
        return index
    #
    def _get_values(self):
        return self.rawdata["val"]

    @on_trait_change("coopid")
    def _update_rawdata(self):
        # Open the connection with the database
        connection = sql.connect(self.dbname, detect_types=sql.DETECT_TYPES)
        # Construct the query
        tbname = "series_monthly_%s" % self.observation
        colname = "COOP%s" % self.coopid
        query_tpl = "select dates,%s from %s"
        query = query_tpl % (colname, tbname)
        # Get the data
        ndtype = [("dates", object), ("val", float)]
        try:
            records = connection.execute(query).fetchall()
        except:
            records = []
            return np.empty(0, dtype=ndtype)
        finally:
            connection.close()
        self.rawdata = data = np.array(records, dtype=ndtype)
        self.update_plots()
        return data
    #
    @on_trait_change("observation")
    def _update_observation(self):
        self._update_rawdata()
        label = self.default_ylabel[self.observation]
        try:
            self.plot_container.overlays[0].text = label
#            self.reference_plot.overlays[1].title = label
#            self.zoomed_plot.underlays[1].title = label
        except AttributeError:
            # Bah, the plots weren't initialized yet...
            pass
    #
    def create_plot(self, **kwargs):
        index = ArrayDataSource(self.index)
        value = ArrayDataSource(self.values)
        xmapper = LinearMapper(range=DataRange1D(index))
        ymapper = LinearMapper(range=DataRange1D(value))
        default_args = dict(padding=(50, 20, 10, 20), #LRTB
                            orientation='h',
                            resizable='hv',
                            border_visible=True,
                            overlay_border=True)
        default_args.update(**kwargs)
        plot = LinePlot(index=index, index_mapper=xmapper,
                        value=value, value_mapper=ymapper,
                        **default_args)
        #
        calendar = CalendarScaleSystem(*MYScales)
        yaxis = PlotAxis(plot, orientation='left', title='')
        xaxis = ScalesPlotAxis(plot, orientation='bottom',
                               tick_generator=ScalesTickGenerator(scale=calendar))
        plot.underlays.extend((xaxis, yaxis))
        #
        add_default_grids(plot)
        return plot
    #
    @on_trait_change("rawdata")
    def update_plots(self):
        index = self.index
        values = self.values
        #
        reference_plot = self.reference_plot
        zoomed_plot = self.zoomed_plot
        #
        if reference_plot is None:
            return
        reference_plot.index.set_data(index)
        reference_plot.value.set_data(values)
        zoomed_plot.index.set_data(index)
        zoomed_plot.value.set_data(values)
    #
    def initialize_enso_overlays(self):
        # Shortcuts to the plot
        ref_plot = self.reference_plot
        zoom_plot = self.zoomed_plot
        container = self.plot_container
        # Get the ENSO indicator
        ensoi = self.ensoi
        # Define the ENSO overlays for each plot
        el_nino_ref = ElNinoOverlay(ensoi, source=ref_plot, visible=False)
        el_nino_zoom = ElNinoOverlay(ensoi, source=zoom_plot, visible=False)
        neutral_ref = NeutralOverlay(ensoi, source=ref_plot, visible=False)
        neutral_zoom = NeutralOverlay(ensoi, source=zoom_plot, visible=False)
        la_nina_ref = LaNinaOverlay(ensoi, source=ref_plot, visible=False)
        la_nina_zoom = LaNinaOverlay(ensoi, source=zoom_plot, visible=False)
        # Add them to the container
        n = len(container.overlays)
        container.overlays.extend((el_nino_ref, el_nino_zoom,
                                   neutral_ref, neutral_zoom,
                                   la_nina_ref, la_nina_zoom))
        # Store them in a dictionary for easier access
        ovl_list = ('el_nino_ref', 'el_nino_zoom',
                    'neutral_ref', 'neutral_zoom',
                    'la_nina_ref', 'la_nina_zoom')
        return dict((lab, ovl) for (lab, ovl) in \
                    zip(ovl_list, container.overlays[n:]))
    #
    @on_trait_change("ensoi")
    def update_enso_overlays(self):
        # Updates the `ensoi` attribute for each ENSO overlat
        for phase_overlay in self.enso_overlays.values():
            phase_overlay.ensoi = self.ensoi
        # Force a redraw if plot_container has been initialized
        if self.plot_container is not None:
            self.plot_container.request_redraw()
    #
    @on_trait_change("display_el_nino,display_neutral,display_la_nina")
    def toggle_enso_overlay(self):
        enso_ = self.enso_overlays
        enso_["el_nino_ref"].visible = enso_["el_nino_zoom"].visible = self.display_el_nino
        enso_["neutral_ref"].visible = enso_["neutral_zoom"].visible = self.display_neutral
        enso_["la_nina_ref"].visible = enso_["la_nina_zoom"].visible = self.display_la_nina
        self.plot_container.request_redraw()


    def __init__(self, dbname, **kwargs):
        self.ensoi_selector = ENSOISelector()
        super(OverlayPlotContainer, self).__init__(**kwargs)
        self.dbname = dbname
        # Initialize the rawdata (empty array w/ the correct dtype)
        rawdata = np.array([], dtype=[("dates", object), ("val", float)])
        self.rawdata = rawdata
        # Define the two plots
        self.zoomed_plot = zoomed_plot = self.create_plot(padding=(50, 20, 10, 10))
        self.reference_plot = reference_plot = self.create_plot()
        #
        reference_plot.controller = RangeSelection(reference_plot)
        #
        reference_plot.tools.append(PanTool(reference_plot))
        # The ZoomTool tool is stateful and allows drawing a zoom
        # box to select a zoom region.
        zoom = ZoomTool(reference_plot, tool_mode="box", always_on=False)
        reference_plot.overlays.append(zoom)

        # The DragZoom tool just zooms in and out as the user drags
        # the mouse vertically.
        dragzoom = DragZoom(reference_plot, drag_button="right")
        reference_plot.tools.append(dragzoom)

        # Initialize the plot container
        container = ZoomedPlotContainer(padding=10,
                                        spacing=5,
                                        fill_padding=True,
                                        stack_order='top_to_bottom',
#                                        bgcolor="lightgray",
                                        use_backbuffer=True)
        self.plot_container = container
        # Add the plots to the container
        container.add(zoomed_plot)
        container.zoomed_plot = zoomed_plot
        container.add(reference_plot)
        container.reference_plot = reference_plot
        # Add the overlays ----------------------
        # First, the common label to the plots' y-axis
        label_overlay = PlotLabel(text=self.default_ylabel[self.observation],
                                  angle=90,
                                  overlay_position="inside left",
                                  hjustify="center", vjustify="center",
                                  component=container)
        # Then, the zoom tool
        zoom_overlay = ReversedZoomOverlay(source=reference_plot,
                                           destination=zoomed_plot)
        container.overlays.extend((label_overlay, zoom_overlay))
        self.enso_overlays = self.initialize_enso_overlays()
        #
        (width, height) = reference_plot.outer_bounds
        reference_plot.set_outer_bounds(width, 0.5 * height)
        container.invalidate_and_redraw()





class StationFinder(HasTraits):
    #
    geocoder = geopy.geocoders.Google()
    #
    dbname = Str(desc="Path of the SQLite database")
    stations_table = Str("stations_list")
    all_stations = Array()
    # (reference is for Tallahasse, FL)
    ref_address = Str("Tallahassee, FL",
                      label="Address/ZIP")
    ref_dec_latitude = Float(label=u"Latitude [\xB0]")
    ref_dec_longitude = Float(label=u"Longitude [\xB0]")
    selection_radius = Range(low=5., high=120., value=20.)
    #
    available_stations = Array
    #
    traits_view = View(Group(Item(name="ref_address",
                                  editor=TextEditor(auto_set=False,
                                                    enter_set=True)),
                             Item(name="ref_dec_latitude",
                                  editor=TextEditor(evaluate=lambda x:float(x),
                                                    auto_set=False,
                                                    enter_set=False)
                                  ),
                             Item(name="ref_dec_longitude",
                                  editor=TextEditor(evaluate=lambda x:float(x),
                                                    auto_set=False,
                                                    enter_set=True)),
                             Item(name="selection_radius")),
                       resizable=True,
                       title="Station Selector")

    def find_reference_coordinates(self):
        (name, (lat, lon)) = self.geocoder.geocode(self.ref_address)
        self.ref_dec_latitude = lat
        self.ref_dec_longitude = lon
    #
    def find_available_stations(self):
        all_stations = self.all_stations
        selected = select_stations_around_reference(all_stations,
                                                    self.ref_dec_longitude,
                                                    self.ref_dec_latitude,
                                                    self.selection_radius)
        self.available_stations = selected
        return selected


    def __init__(self, dbname, **kwargs):
        self.dbname = dbname
        # Open the connection
        connection = sql.connect(dbname, detect_types=sql.DETECT_TYPES)
        ndtype = [('coopid', '|S6'), ('name', '|S30'),
                  ('lat', float), ('lon', float)]
        # Define the query
        fields = "COOPID, STATION_NAME, LATITUDE, LONGITUDE"
        query = "select %s from %s" % (fields, self.stations_table)
        # Retrieve the fields and close
        try:
            info = connection.execute(query).fetchall()
            self.all_stations = np.array(info, dtype=ndtype)
        finally:
            connection.close()
        # Update the default available stations
        self.find_reference_coordinates()
        self.find_available_stations()
        # Define the action to perform if the reference changes
        self.on_trait_change(self.find_reference_coordinates,
                             "ref_address")
        self.on_trait_change(self.find_available_stations,
                             'ref_dec_latitude,ref_dec_longitude,selection_radius')
    #





class StationSelector(HasTraits):
    """
    
    """
    #
    available_stations = Array()
    available_coopids = List
    available_coopids_editor = EnumEditor(values={})
    selected_coopid = Str(label="COOP ID")
    #
    traits_view = View(Item(name="selected_coopid",
                            label="COOP id",
                            editor=available_coopids_editor))
    #
    def _available_stations_changed(self):
        available = self.available_stations
        coopids = available['coopid']
        # Count the nb of results (in power of 10)
        n = np.ceil(np.log10(len(available) or 1))
        if n == 1:
            template = "%i:%s (%s mi)"
        else:
            # We need to make sure the numeric tags are aligned
            template = "%%%ii:%%s (%%s mi)" % n
        #
        description = dict((s, template % (i, s, int(d)))
                           for (i, (s, d)) in enumerate(zip(coopids,
                                                            available['distance_from_ref'])))
        self.available_coopids = list(coopids)
        self.available_coopids_editor.values = description



