"""
Created on May 17, 2010

@author: pierregm
"""

import numpy as np

from enthought.chaco.api import AbstractOverlay, BaseXYPlot, LinePlot, VPlotContainer
from enthought.enable.api import ColorTrait, Component
from enthought.traits.api import Instance, Float, Int


class ZoomOverlay(AbstractOverlay):
    """
    Draws a trapezoidal selection overlay from the source plot to the
    destination plot.  Assumes that the source plot lies above the destination
    plot.
    """

    source = Instance(BaseXYPlot)
    destination = Instance(Component)

    border_color = ColorTrait((0, 0, 0.7, 1))
    border_width = Int(1)
    fill_color = ColorTrait("dodgerblue")
    alpha = Float(0.3)

    def calculate_points(self, component):
        """
        Calculate the overlay polygon based on the selection and the location
        of the source and destination plots.
        """
        # find selection range on source plot
        x_start, x_end = self._get_selection_screencoords()
        if x_start > x_end:
            x_start, x_end = x_end, x_start

        y_end = self.source.y
        y_start = self.source.y2

        left_top = np.array([x_start, y_start])
        left_mid = np.array([x_start, y_end])
        right_top = np.array([x_end, y_start])
        right_mid = np.array([x_end, y_end])

        # Offset y because we want to avoid overlapping the trapezoid with the topmost
        # pixels of the destination plot.
        y = self.destination.y2 + 1

        left_end = np.array([self.destination.x, y])
        right_end = np.array([self.destination.x2, y])

        polygon = np.array((left_top, left_mid, left_end,
                            right_end, right_mid, right_top))
        left_line = np.array((left_top, left_mid, left_end))
        right_line = np.array((right_end, right_mid, right_top))

        return left_line, right_line, polygon

    def overlay(self, component, gc, view_bounds=None, mode="normal"):
        """
        Draws this overlay onto 'component', rendering onto 'gc'.
        """

        tmp = self._get_selection_screencoords()
        if tmp is None:
            return

        left_line, right_line, polygon = self.calculate_points(component)

        gc.save_state()
        try:
            gc.translate_ctm(*component.position)
            gc.set_alpha(self.alpha)
            gc.set_fill_color(self.fill_color_)
            gc.set_line_width(self.border_width)
            gc.set_stroke_color(self.border_color_)
            gc.begin_path()
            gc.lines(polygon)
            gc.fill_path()

            gc.begin_path()
            gc.lines(left_line)
            gc.lines(right_line)
            gc.stroke_path()
        finally:
            gc.restore_state()
        return

    def _get_selection_screencoords(self):
        """
        Returns a tuple of (x1, x2) screen space coordinates of the start
        and end selection points.  If there is no current selection, then
        returns None.
        """
        selection = self.source.index.metadata["selections"]
        if (selection is not None) and (len(selection) == 2):
            mapper = self.source.index_mapper
            return mapper.map_screen(np.array(selection))
        else:
            return None

    #------------------------------------------------------------------------
    # Trait event handlers
    #------------------------------------------------------------------------

    def _source_changed(self, old, new):
        if old is not None and old.controller is not None:
            old.controller.on_trait_change(self._selection_update_handler, "selection",
                                           remove=True)
        if new is not None and new.controller is not None:
            new.controller.on_trait_change(self._selection_update_handler, "selection")
        return

    def _selection_update_handler(self, value):
        if value is not None and self.destination is not None:
            r = self.destination.index_mapper.range
            (start, end) = (np.amin(value), np.amax(value))
            r.low = start
            r.high = end
        self.source.request_redraw()
        self.destination.request_redraw()
        return



class ReversedZoomOverlay(ZoomOverlay):
    """
    Draws a trapezoidal selection overlay from the source plot to the
    destination plot.  Assumes that the source plot lies *below* the destination
    plot.
    """


    def calculate_points(self, component):
        """
        Calculate the overlay polygon based on the selection and the location
        of the source and destination plots.
        """
        # find selection range on source plot
        x_start, x_end = self._get_selection_screencoords()
        if x_start > x_end:
            x_start, x_end = x_end, x_start

        y_end = self.source.y
        y_start = self.source.y2

        left_top = np.array([x_start, y_end])
        left_mid = np.array([x_start, y_start])
        right_top = np.array([x_end, y_end])
        right_mid = np.array([x_end, y_start])

        # Offset y because we want to avoid overlapping the trapezoid with the topmost
        # pixels of the destination plot.
        y = self.destination.y - 1

        left_end = np.array([self.destination.x, y])
        right_end = np.array([self.destination.x2, y])

        polygon = np.array((left_end, left_mid, left_top,
                            right_top, right_mid, right_end))
        left_line = np.array((left_top, left_mid, left_end))
        right_line = np.array((right_end, right_mid, right_top))

        return left_line, right_line, polygon





class ZoomedPlotContainer(VPlotContainer):

    reference_plot = Instance(LinePlot)
    zoomed_plot = Instance(LinePlot)
    #

    def _do_layout(self):
        """ Actually performs a layout (called by do_layout()).
        """
        if self.stack_order == "bottom_to_top":
            components = (self.zoomed_plot, self.reference_plot)
            relative_sizes = (4 / 3., 2 / 3.)
        else:
            components = (self.reference_plot, self.zoomed_plot)
            relative_sizes = (2 / 3., 4 / 3.)
        if self.halign == "left":
            align = "min"
        elif self.halign == "center":
            align = "center"
        else:
            align = "max"
        #import pdb; pdb.set_trace()
        return self._do_stack_layout(components, relative_sizes, align)


    def _do_stack_layout(self, components, relative_sizes, align):
        """ Helper method that does the actual work of layout.
        """
        size = list(self.bounds)
        if self.fit_components != "":
            self.get_preferred_size()
            if "h" in self.fit_components:
                size[0] = self._cached_preferred_size[0] - self.hpadding
            if "v" in self.fit_components:
                size[1] = self._cached_preferred_size[1] - self.vpadding

        ndx = self.stack_index
        other_ndx = 1 - ndx
        other_dim = self.other_dimension

        # Assign sizes of non-resizable components, and compute the total size
        # used by them (along the stack dimension).
        total_fixed_size = 0
        resizable_components = []
        size_prefs = {}
        total_resizable_size = 0

        for component in components:
            if not self._should_layout(component):
                continue
            if self.stack_dimension not in component.resizable:
                total_fixed_size += component.outer_bounds[ndx]
            else:
                preferred_size = component.get_preferred_size()
                size_prefs[component] = preferred_size
                total_resizable_size += preferred_size[ndx]
                resizable_components.append(component)

        new_bounds_dict = {}

        # Assign sizes of all the resizable components along the stack dimension
        if resizable_components:
            space = self.spacing
            avail_size = size[ndx] - total_fixed_size - space
            if total_resizable_size > 0:
                scale = avail_size / float(total_resizable_size)
                for component in resizable_components:
                    tmp = list(component.outer_bounds)
                    tmp[ndx] = int(size_prefs[component][ndx] * scale)
                    new_bounds_dict[component] = tmp
            else:
                each_size = int(avail_size / len(resizable_components))
                for (component, f) in zip(resizable_components, relative_sizes):
                    tmp = list(component.outer_bounds)
                    tmp[ndx] = each_size * f
                    new_bounds_dict[component] = tmp

        # Loop over all the components, assigning position and computing the
        # size in the other dimension and its position.
        cur_pos = 0
        for component in components:
            if not self._should_layout(component):
                continue

            position = list(component.outer_position)
            position[ndx] = cur_pos

            bounds = new_bounds_dict.get(component, list(component.outer_bounds))
            cur_pos += bounds[ndx] + self.spacing

            if (bounds[other_ndx] > size[other_ndx]) or \
                    (other_dim in component.resizable):
                # If the component is resizable in the other dimension or it exceeds the
                # container bounds, set it to the maximum size of the container

                #component.set_outer_position(other_ndx, 0)
                #component.set_outer_bounds(other_ndx, size[other_ndx])
                position[other_ndx] = 0
                bounds[other_ndx] = size[other_ndx]
            else:
                #component.set_outer_position(other_ndx, 0)
                #old_coord = component.outer_position[other_ndx]
                position[other_ndx] = 0
                if align == "min":
                    pass
                elif align == "max":
                    position[other_ndx] = size[other_ndx] - bounds[other_ndx]
                elif align == "center":
                    position[other_ndx] = (size[other_ndx] - bounds[other_ndx]) / 2.0

            component.outer_position = position
            component.outer_bounds = bounds
            component.do_layout()
        return

