import AppKit
import vanilla
from pprint import pprint
from kerningHelper import get_repr_pair
import GlyphsApp.drawingTools as drawBot
#from lib.tools.debugTools import ClassNameIncrementer


class PairView(AppKit.NSView): # , metaclass=ClassNameIncrementer):

    def init(self):
        self = super(PairView, self).init()
        self._glyphData = []
        self._kern_value = 0
        self._inset = 10
        self.checked = False
        return self

    def setGlyphData_kerning_(self, glyph_list, kerning):
        self._glyphData = glyph_list
        self.setKerning_(kerning)
        self.setNeedsDisplay_(True)

    def setGlyphData_(self, glyph_list):
        self._glyphData = glyph_list
        self.setNeedsDisplay_(True)

    def setKerning_(self, kerning):
        if kerning is None:
            self._kern_value = 0
        else:
            self._kern_value = kerning
        self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        # draw here!
        try:
            AppKit.NSColor.whiteColor().set()
            AppKit.NSRectFill(rect)
            
            if self.delegate.checked:
                AppKit.NSColor.selectedControlColor().set()
                selectionPath = AppKit.NSBezierPath.bezierPathWithRoundedRect_cornerRadius_(AppKit.NSInsetRect(rect, 2, 2), 4)
                AppKit.NSColor.selectedControlColor().colorWithAlphaComponent_(0.1).set()
                selectionPath.fill()
                AppKit.NSColor.selectedControlColor().set()
                selectionPath.stroke()
                
            frame_width, frame_height = self.frame().size
            w, h = [i - 2 * self._inset for i in self.frame().size]

            glyph_pair = self._glyphData
            glyph_l, glyph_r = glyph_pair
            font = glyph_l.getParent()
            upm = font.info.unitsPerEm
            scale_factor = h / (upm * 1.2)
            drawBot.translate(frame_width / 2, self._inset)
            drawBot.scale(scale_factor)

            drawBot.stroke(None)
            if self._kern_value <= 0:
                drawBot.fill(1, 0.3, 0.75, 0.7)
            else:
                drawBot.fill(0, 0.8, 0, 0.7)
                # drawBot.fill(0.4, 1, 0.8)
            drawBot.rect(
                0 - abs(self._kern_value) / 2, - self._inset / scale_factor,
                abs(self._kern_value), 2 * self._inset / scale_factor)
            drawBot.rect(
                0 - abs(self._kern_value) / 2, (h - self._inset) / scale_factor,
                abs(self._kern_value), 2 * self._inset / scale_factor)
            drawBot.translate(0, upm / 3)
            drawBot.translate(-glyph_l.width - self._kern_value / 2, 0)
            for glyph in glyph_pair:
                #path = glyph.getRepresentation('defconAppKit.NSBezierPath') # this is broken in Glyphs v.1149 and below
                path = glyph._layer.completeBezierPath
                drawBot.stroke(None)
                # drawBot.fill(0, 1, 0)
                drawBot.fill(0)
                drawBot.drawPath(path)
                drawBot.translate(glyph.width + self._kern_value, 0)
        except:
            import traceback
            print(traceback.format_exc())
    def mouseUp_(self, event):
        self.delegate.checked = not self.delegate.checked
        self.setNeedsDisplay_(True)

class DrawPair(vanilla.Group):

    nsViewClass = PairView
    def __init__(self, posSize):
        self._setupView(self.nsViewClass, posSize)
        self.getNSView().delegate = self
        self.checked = False
    
    def setGlyphData_kerning(self, glyph, kerning):
        self.getNSView().setGlyphData_kerning_(glyph, kerning)

    def setKerning(self, kerning):
        self.getNSView().setKerning_(kerning)


class Test(object):

    def __init__(self, fonts):
        self.fonts = fonts
        self.w = vanilla.Window((1200, 600), minSize=(100, 100))
        _, _, w_width, w_height = self.w.getPosSize()
        prev_height = w_height / 3
        self.w.allFontsGroup = vanilla.Group((0, 0, -0, prev_height))
        self.steps = len(self.fonts)
        step = w_width / self.steps
        for f_index, f in enumerate(self.fonts):
            x = step * f_index
            control = DrawPair((x, 0, step, -0))

            self.kern_list = list(f.kerning.keys())
            initial_pair = self.kern_list[0]
            kern_value = f.kerning.get(initial_pair, 0)
            repr_pair = get_repr_pair(f, initial_pair)
            repr_glyphs = [f[g_name] for g_name in repr_pair]
            control.setGlyphData_kerning(repr_glyphs, kern_value)

            setattr(
                self.w.allFontsGroup,
                'pair_{}'.format(f_index),
                control
            )

        display_list = [', '.join(pair) for pair in self.kern_list]
        list_height = w_height - prev_height

        self.w.myList = vanilla.List(
            (0, -list_height, -0, -0),
            display_list,
            allowsMultipleSelection=False,
            selectionCallback=self.list_callback,
        )

        self.w.bind('resize', self.resize_callback)
        self.w.open()

    def list_callback(self, sender):
        pair_index = sender.getSelection()[0]
        pair = self.kern_list[pair_index]
        for f_index, f in enumerate(self.fonts):
            repr_pair = get_repr_pair(f, pair)
            repr_glyphs = [f[g_name] for g_name in repr_pair]
            kern_value = f.kerning.get(pair, 0)
            pair_obj = getattr(
                self.w.allFontsGroup, 'pair_{}'.format(f_index))
            pair_obj.setGlyphData_kerning(repr_glyphs, kern_value)

    def resize_callback(self, sender):
        _, _, w_width, w_height = self.w.getPosSize()
        step = w_width / self.steps
        step_dist = w_width / self.steps
        prev_height = w_height / 3

        for f_index, f in enumerate(self.fonts):
            pair_obj = getattr(
                self.w.allFontsGroup, 'pair_{}'.format(f_index))
            x = f_index * step_dist
            pair_obj.setPosSize((x, 0, step, prev_height))
        self.w.allFontsGroup.setPosSize((0, 0, -0, prev_height))
        list_height = w_height - prev_height

        self.w.myList.setPosSize((0, -list_height, -0, -0))


if __name__ == '__main__':
    a = AllFonts('styleName')

    Test(a)
