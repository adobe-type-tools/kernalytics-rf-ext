# encoding: utf-8
from __future__ import print_function
#from mojo.glyphPreview import GlyphPreview
import AppKit
import math
import vanilla
import GlyphsApp.drawingTools as drawBot
#from mojo.canvas import Canvas
from GlyphsApp.UI import CanvasView
from pprint import pprint
import importlib

import kerningHelper
#importlib.reload(kerningHelper)
import pairView
#importlib.reload(pairView)
from pairView import DrawPair
# from lib.tools.debugTools import ClassNameIncrementer


def sub_points(p1, p2):
    (x1, y1) = p1
    (x2, y2) = p2
    return x2 - x1, y2 - y1


def calc_distance(p1, p2):
    dx, dy = sub_points(p1, p2)
    return math.hypot(dx, dy)


class CanvasDelegate(object):

    def __init__(self, parent):
        self.parent = parent
        self.drag_index = None

    def draw(self, view):
        self.graph_in_window = []
        c_width, c_height = self.parent.graph_width, self.parent.graph_height

        drawBot.fill(None)

        # horizontal line
        drawBot.stroke(0)
        drawBot.strokeWidth(0.5)
        drawBot.line((0, c_height / 2), (c_width, c_height / 2))

        # vertical lines
        # the combination of both margins equal one additional step
        graph_margin = self.parent.step_dist / 2
        for i in range(self.parent.steps + 1):
            x = graph_margin + i * self.parent.step_dist
            drawBot.line((x, 0), (x, c_height))

        # the graph
        drawBot.stroke(0, 0, 1)
        drawBot.strokeWidth(5)
        drawBot.lineCap('round')

        prev = None
        max_value = max([abs(v) for v in self.parent.number_values])
        zero_point = c_height / 2
        min_scale = 40
        self.max_allowed_value = 500
        self.graph_scale = max_value / self.parent.graph_height
        self.min_graph_scale = min_scale / self.parent.graph_height
        slider_controls = []

        for i, value in enumerate(self.parent.number_values):
            if max_value > min_scale:
                self.amplitude = value / max_value
            else:
                self.amplitude = value / min_scale

            x = graph_margin + i * self.parent.step_dist
            y = zero_point + c_height * 0.4 * self.amplitude
            y_window = (
                self.parent.w_height - self.parent.graph_height +
                y - self.parent.padding
            )
            self.graph_in_window.append((x, y_window))
            if prev:
                drawBot.line(prev, (x, y))
            prev = x, y
            slider_controls.append((x, y))

        # slider heads
        for x, y in slider_controls:
            radius = 10
            drawBot.fill(1)
            drawBot.stroke(0)
            drawBot.strokeWidth(0.5)
            drawBot.oval(x - radius, y - radius, 2 * radius, 2 * radius)

    def update_textBox(self, tb_index):
        text_box = getattr(
            self.parent.w, 'textbox_{}'.format(tb_index))
        text_box.set(self.parent.label_values[tb_index])

    def mouseDragged(self, event):
        if self.drag_index is not None:
            drag_index = self.drag_index
            x, y = self.graph_in_window[drag_index]
            dx, dy = sub_points((x, y), event.locationInWindow())
            original_value = self.parent.number_values[drag_index]
            if self.graph_scale <= self.min_graph_scale:
                self.graph_scale = self.min_graph_scale

            new_value = original_value + (dy * self.graph_scale)
            pair_obj = getattr(
                self.parent.w.pairPreview, 'pair_{}'.format(drag_index))

            if new_value > self.max_allowed_value:
                new_kern_value = self.max_allowed_value
            elif new_value < -self.max_allowed_value:
                new_kern_value = -self.max_allowed_value
            else:
                new_kern_value = int(round(new_value))

            self.parent.values[drag_index] = new_kern_value

            pair_obj.setKerning(new_kern_value)
            self.parent.w.c.update()
            self.parent.update_display(self.parent.values)
            self.parent.update_kerning(
                self.drag_index, self.parent.pair, new_kern_value)
            self.update_textBox(drag_index)

    def mouseDown(self, event):
        # find point closest to mouse pointer
        mx, my = event.locationInWindow()
        distances = []
        for i, (x, y) in enumerate(self.graph_in_window):
            d = calc_distance((mx, my), (x, y))
            distances.append((i, d))
        distances.sort(key=lambda x: x[1])
        self.drag_index, _ = distances[0]
        pair_obj = getattr(
            self.parent.w.pairPreview, 'pair_{}'.format(self.drag_index))

        # reset value on double click
        if event.clickCount() > 1:
            self.parent.values[self.drag_index] = None
            pair_obj.setKerning(None)
            self.parent.update_display(self.parent.values)
            self.parent.update_kerning(
                self.drag_index, self.parent.pair, None)
            self.update_textBox(self.drag_index)
            self.parent.w.c.update()


class FlexibleWindow(object):

    min_w_height = 800
    button_width = 150
    padding = 10

    def __init__(self, fonts):

        self.fonts = fonts
        if len(self.fonts) in range(4):
            self.min_unit_width = 350
            self.p_point_size = 160
        elif len(self.fonts) in range(4, 7):
            self.min_unit_width = 200
            self.p_point_size = 120
        else:
            self.min_unit_width = 150
            self.p_point_size = 100

        # by default, all checkboxes are unchecked
        self.checked = [0 for i in range(len(self.fonts))]

        self.min_w_width = len(self.fonts) * self.min_unit_width
        # cmb_kern_dict is an ordered dict
        self.cmb_kern_dict = kerningHelper.get_combined_kern_dict(fonts)
        self.pair_list = list(self.cmb_kern_dict.keys())
        self.filtered_pairlists = self.make_filtered_pairlists(
            self.cmb_kern_dict)

        # initial value for the first pair to show
        initial_pair = self.pair_list[0]
        self.pair = initial_pair
        initial_value = self.cmb_kern_dict[initial_pair]
        self.values = initial_value
        self.steps = len(self.values)
        self.update_display(self.values)
        self.drag_index = None

        self.w = vanilla.Window(
            (self.min_w_width, self.min_w_height),
            title='Kern-A-Lytics',
            minSize=(self.min_w_width / 2, self.min_w_height / 2),
        )

        _, _, self.w_width, self.w_height = self.w.getPosSize()
        self.graph_height = self.w_height / 3
        self.graph_width = (
            self.w_width - 2 * self.padding)
        self.step_dist = self.graph_width / self.steps
        graph_margin = self.step_dist / 2
        self.canvas_delegate = CanvasDelegate(self)
        self.w.c = CanvasView(
            (self.padding, self.padding, -self.padding, self.graph_height),
            delegate=self.canvas_delegate,
            #canvasSize=(self.graph_width, self.graph_height),
            # backgroundColor=AppKit.NSColor.orangeColor(),
            #backgroundColor=AppKit.NSColor.clearColor(),
            #drawsBackground=False,
        )

        # buttons
        buttons = [
            # button label, callback name
            ('Delete Pairs', 'delete_button_callback'),
            ('Average Pairs', 'average_button_callback'),
            ('Equalize Pairs', 'transfer_button_callback'),
            ('Interpolate Pair', 'interpolate_button_callback'),
            # ('Transfer Pair', 'transfer_button_callback'),
            ('+10', 'plus_button_callback'),
            ('-10', 'minus_button_callback'),
            # ('+10%', 'dummy_button_callback'),
            # ('-10%', 'dummy_button_callback'),
        ]

        button_top = -210
        # list starts at 210 and has 10 padding at bottom
        # total whitespace: 200 height - 8 * 20 = 40
        # individual_whitespace = 40 / (len(buttons) - 1)
        button_height = 20
        button_space = len(buttons) * button_height
        button_whitespace = (abs(button_top) - self.padding) - button_space
        button_step_space = button_whitespace / (len(buttons) - 1)
        for i, (b_label, b_callback_name) in enumerate(buttons):
            button = vanilla.Button((
                -(self.padding + self.button_width),
                button_top + i * button_height,
                self.button_width, button_height), b_label,
                callback=getattr(self, b_callback_name)
            )
            setattr(
                self.w,
                'button_{}'.format(i),
                button)
            # button_top += self.padding / 2
            button_top += button_step_space

        # graph labels with monospaced digits
        nsfont = AppKit.NSFont.monospacedDigitSystemFontOfSize_weight_(14, 0.0)
        for i, number in enumerate(self.label_values):
            tb_x = self.padding + graph_margin + i * self.step_dist
            self.tb_y = self.padding * 2 + self.graph_height
            self.tb_height = 20
            self.tb_width = 100

            tb_control = vanilla.TextBox(
                (
                    tb_x - self.tb_width / 2, self.tb_y,
                    self.tb_width, self.tb_height),
                number,
                alignment='center',
                sizeStyle='small',
                selectable=True,
            )

            tb_control.getNSTextField().setFont_(nsfont)
            setattr(
                self.w,
                'textbox_{}'.format(i),
                tb_control)

        # pair preview
        pp_origin_x = self.padding
        pp_origin_y = self.padding * 4 + self.graph_height + self.tb_height
        self.w.pairPreview = vanilla.Group(
            (pp_origin_x, pp_origin_y, self.w_width, self.p_point_size)
        )
        for f_index, f in enumerate(self.fonts):
            x = self.step_dist * f_index
            pair_preview = DrawPair((x, 0, self.step_dist, -0))

            initial_pair = self.pair_list[0]
            kern_value = self.cmb_kern_dict.get(initial_pair)[f_index]
            if kern_value is None:
                kern_value = 0

            repr_pair = kerningHelper.get_repr_pair(f, initial_pair)
            # XXXX the following line is problematic
            # if UFOs with different group structures are opened
            repr_glyphs = [f[g_name] for g_name in repr_pair]
            pair_preview.setGlyphData_kerning(repr_glyphs, kern_value)

            setattr(
                self.w.pairPreview,
                'pair_{}'.format(f_index),
                pair_preview
            )

        # checkboxes
        for i, f in enumerate(self.fonts):
            cb_x = self.padding + graph_margin + i * self.step_dist
            cb_control = vanilla.CheckBox(
                (
                    cb_x - 6,
                    pp_origin_y + self.p_point_size + self.padding * 2,
                    22, 22),
                '',
                value=False,
                sizeStyle='regular',
                callback=self.checkbox_callback
            )

            setattr(
                self.w,
                'checkbox_{}'.format(i),
                cb_control)

        # pop-up button for list filtering
        list_width = self.w_width - self.button_width - self.padding * 3

        self.w.list_filter = vanilla.PopUpButton(
            (10, -240, -(self.padding + self.button_width + self.padding), 20),
            self.filter_options,
            callback=self.filter_callback
        )

        # list of kerning pairs (bottom)
        column_pairs = self.make_columns(self.pair_list)
        self.w.display_list = vanilla.List(
            (10, -210, -(self.padding + self.button_width + self.padding), -10),
            column_pairs,
            columnDescriptions=[{'title': 'L'}, {'title': 'R'}],
            allowsMultipleSelection=False,
            selectionCallback=self.list_callback)

        self.w.bind('resize', self.resize_callback)
        self.w.open()

    def make_filtered_pairlists(self, cmb_kern_dict):
        '''
        Creates the filtered lists for selection in popup button
        '''
        filter_lists = []
        self.filter_options = []
        small_average_value = 5
        outlier_factor = 5

        all_pairs = list(cmb_kern_dict.keys())
        filter_lists.append(all_pairs)
        self.filter_options.append(
            'All Pairs ({})'.format(len(all_pairs)))

        single_pair_dict = kerningHelper.single_pair_dict(
            self.cmb_kern_dict)
        filter_lists.append(list(single_pair_dict.keys()))
        self.filter_options.append(
            'Single Pairs ({})'.format(len(single_pair_dict)))

        same_value_dict = kerningHelper.same_value_dict(
            cmb_kern_dict)
        filter_lists.append(list(same_value_dict.keys()))
        self.filter_options.append(
            'Same Value Across all Masters ({})'.format(len(same_value_dict)))

        zero_value_dict = kerningHelper.zero_value_dict(
            self.cmb_kern_dict)
        filter_lists.append(list(zero_value_dict.keys()))
        self.filter_options.append(
            'Zero-Value Pairs ({})'.format(len(zero_value_dict)))

        largest_value_dict = kerningHelper.largest_value_dict(
            self.cmb_kern_dict)
        filter_lists.append(list(largest_value_dict.keys()))
        self.filter_options.append(
            'Long-Distance Kerning Pairs ({})'.format(len(largest_value_dict)))

        high_gamut_dict = kerningHelper.high_gamut_dict(
            self.cmb_kern_dict)
        filter_lists.append(list(high_gamut_dict.keys()))
        self.filter_options.append(
            'High Gamut Across Pairs ({})'.format(len(high_gamut_dict)))

        outlier_dict = kerningHelper.outlier_dict(
            self.cmb_kern_dict, outlier_factor)
        filter_lists.append(list(outlier_dict.keys()))
        self.filter_options.append(
            'Outliers by a Factor of {} ({})'.format(
                outlier_factor, len(outlier_dict)))

        exception_dict = kerningHelper.exception_dict(
            self.fonts, self.cmb_kern_dict)
        filter_lists.append(list(exception_dict.keys()))
        self.filter_options.append(
            'Exceptions ({})'.format(len(exception_dict)))

        small_average_dict = kerningHelper.small_average_dict(
            self.cmb_kern_dict, small_average_value)
        filter_lists.append(list(small_average_dict.keys()))
        self.filter_options.append(
            'Average Kern Distance < {} ({})'.format(
                small_average_value, len(small_average_dict)))

        # self.filter_options.append(
        #     'Zero Test ({})'.format(len([])))

        return filter_lists

    def make_columns(self, pair_list):
        column_pairs = []
        for left, right in [pair for pair in pair_list]:
            pair_dict = {}
            pair_dict['L'] = left
            pair_dict['R'] = right
            column_pairs.append(pair_dict)
        return column_pairs

    def update_textBoxes(self):
        for i, value in enumerate(self.label_values):
            text_box = getattr(
                self.w, 'textbox_{}'.format(i))
            text_box.set(self.label_values[i])

    def update_display(self, value_list):
        self.label_values = [
            '' if value is None else str(int(value)) for value in value_list
        ]
        self.number_values = [
            0 if value is None else int(value) for value in value_list
        ]

    def update_kerning(self, font_index, pair, value):
        font = self.fonts[font_index]
        if value is None:
            if pair in font.kerning.keys():
                del font.kerning[pair]
        else:
            font.kerning[pair] = value

    def resize_callback(self, sender):
        _, _, self.w_width, self.w_height = self.w.getPosSize()

        self.graph_width = (
            self.w_width - 2 * self.padding)

        # button_left = self.w_width - self.padding - self.button_width
        self.step_dist = self.graph_width / self.steps
        graph_margin = self.step_dist / 2
        pp_origin_y = self.padding * 3 + self.graph_height + self.tb_height

        (pc_x, pc_y, _, pc_height) = self.w.pairPreview.getPosSize()
        self.w.pairPreview.setPosSize(
            (pc_x, pc_y, self.graph_width, pc_height))

        for i, number in enumerate(self.label_values):
            text_box = getattr(
                self.w, 'textbox_{}'.format(i))
            check_box = getattr(
                self.w, 'checkbox_{}'.format(i))
            tb_x = self.padding + graph_margin + i * self.step_dist
            text_box.setPosSize(
                (
                    tb_x - self.tb_width / 2, self.tb_y,
                    self.tb_width, self.tb_height))

            cb_x = self.padding + graph_margin + i * self.step_dist
            check_box.setPosSize(
                (
                    cb_x - 6, pp_origin_y + self.p_point_size + self.padding,
                    22, 22))

            pair_preview = getattr(
                self.w.pairPreview, 'pair_{}'.format(i))
            pp_origin = self.step_dist * i
            pair_preview.setPosSize(
                (pp_origin, 0, self.step_dist, -0))

    def filter_callback(self, sender):
        sel_index = sender.get()
        self.pair_list = self.filtered_pairlists[sel_index]
        self.w.display_list.set(self.make_columns(self.pair_list))

    def list_callback(self, sender):
        if not sender.getSelection() and len(self.w.display_list) is 0:
            # list is empty, don’t attempt any selection

            print('empty list')
            pass

        else:
            if not sender.getSelection():
                # list is new, select first item in new list
                sel_index = 0
                self.w.display_list.setSelection([sel_index])
            else:
                # normal -- just select the next item
                sel_index = sender.getSelection()[0]

            self.pair = self.pair_list[sel_index]
            new_values = self.cmb_kern_dict.get(self.pair)
            self.values = new_values
            self.w.c.update()
            self.update_display(new_values)
            self.update_textBoxes()

            print(self.pair, new_values)
            for f_index, f in enumerate(self.fonts):
                repr_pair = kerningHelper.get_repr_pair(f, self.pair)
                repr_glyphs = [f[g_name] for g_name in repr_pair]
                kern_value = f.kerning.get(self.pair, 0)
                pair_obj = getattr(
                    self.w.pairPreview, 'pair_{}'.format(f_index))
                pair_obj.setGlyphData_kerning(repr_glyphs, kern_value)

    def checkbox_callback(self, sender):
        for i, _ in enumerate(self.fonts):
            cb_obj = getattr(
                self.w, 'checkbox_{}'.format(i))
            self.checked[i] = cb_obj.get()

    def update_stack(self, pair, value_list):
        self.values = value_list
        self.cmb_kern_dict[pair] = value_list

        self.update_display(value_list)
        self.update_textBoxes()
        for i, value in enumerate(value_list):
            pair_obj = getattr(
                self.w.pairPreview, 'pair_{}'.format(i))
            pair_obj.setKerning(value)
        self.w.c.update()

    def delete_button_callback(self, sender):
        for i, f in enumerate(self.fonts):
            self.update_kerning(i, self.pair, None)
        new_values = [None for i in range(len(self.fonts))]
        self.update_stack(self.pair, new_values)
        print('deleting {} {}'.format(*self.pair))

    def _interpolate(self, poles, factor, extrapolate=False):
        p_min, p_max = poles
        difference = p_max - p_min
        result = p_min + difference * factor
        if extrapolate:
            result = p_max + difference * factor
        return result

    def interpolate_button_callback(self, sender):
        # This is not really thought through.
        # For instance: what happens if all boxes are checked?
        c_index = [i for i, b_value in enumerate(self.checked) if b_value == 1]
        number_values = [0 if v is None else v for v in self.values]
        new_values = [v for v in self.values]
        factor = 0.5

        if len(number_values) > 3:
            print('Need at least 3 masters to interpolate')
            pass

        if not c_index:
            print('Please select interpolation target(s)')
            pass

        for c_i in c_index:
            if c_i == 0:
                # extrapolation on the left
                poles = (number_values[2], number_values[1])
                value = self._interpolate(poles, factor, extrapolate=True)
            elif c_i == (len(number_values) - 1):
                # extrapolation on the right
                poles = (number_values[-3], number_values[-2])
                value = self._interpolate(poles, factor, extrapolate=True)
            else:
                # normal interpolation
                poles = (number_values[c_i - 1], number_values[c_i + 1])
                value = self._interpolate(poles, factor)
            kern_value = int(round(value))
            new_values[c_i] = kern_value
        self.update_stack(self.pair, new_values)

    def transfer_button_callback(self, sender):
        c_index = [i for i, b_value in enumerate(self.checked) if b_value == 1]
        if len(c_index) == 0:
            print('Select a source checkbox.')
        elif len(c_index) > 1:
            print('Select only one source checkbox.')
        else:
            c_index_number = c_index[0]
            t_value = self.values[c_index_number]
            new_values = [t_value for i in range(len(self.fonts))]
            self.update_stack(self.pair, new_values)
            print('Transfering value {} across pairs'.format(t_value))

    def average_button_callback(self, sender):
        number_values = [0 if v is None else v for v in self.values]
        average_value = int(round(sum(number_values) / len(number_values)))
        new_values = [average_value for i in range(len(self.fonts))]
        self.update_stack(self.pair, new_values)
        print('Setting pairs to average value {}'.format(average_value))

    def increase_values(self, value_list, amount):
        '''
        Change all or selected values by amount.
        Used by plus_ and minus_button_callback functions.
        '''
        c_index = [i for i, b_value in enumerate(self.checked) if b_value == 1]
        number_values = [0 if v is None else v for v in value_list]
        if len(c_index) in [0, len(self.fonts)]:
            # all or nothing are checked
            new_values = [value + amount for value in number_values]
        else:
            # only some are checked
            new_values = [
                value + amount if
                i in c_index else
                value for i, value in enumerate(number_values)
            ]
        return new_values

    def plus_button_callback(self, sender):
        new_values = self.increase_values(self.values, 10)
        self.update_stack(self.pair, new_values)

    def minus_button_callback(self, sender):
        new_values = self.increase_values(self.values, -10)
        self.update_stack(self.pair, new_values)

    def dummy_button_callback(self, sender):
        pass


if __name__ == '__main__':

    a = AllFonts('styleName')
    FlexibleWindow(a)
