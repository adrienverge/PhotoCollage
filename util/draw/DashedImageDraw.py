from PIL import Image, ImageDraw
import math


class DashedImageDraw(ImageDraw.ImageDraw):

    def thick_line(self, xy, direction, fill=None, width=0):
        # xy – Sequence of 2-tuples like [(x, y), (x, y), ...]
        # direction – Sequence of 2-tuples like [(x, y), (x, y), ...]
        if xy[0] != xy[1]:
            self.line(xy, fill=fill, width=width)
        else:
            x1, y1 = xy[0]
            dx1, dy1 = direction[0]
            dx2, dy2 = direction[1]
            if dy2 - dy1 < 0:
                x1 -= 1
            if dx2 - dx1 < 0:
                y1 -= 1
            if dy2 - dy1 != 0:
                if dx2 - dx1 != 0:
                    k = - (dx2 - dx1) / (dy2 - dy1)
                    a = 1 / math.sqrt(1 + k ** 2)
                    b = (width * a - 1) / 2
                else:
                    k = 0
                    b = (width - 1) / 2
                x3 = x1 - math.floor(b)
                y3 = y1 - int(k * b)
                x4 = x1 + math.ceil(b)
                y4 = y1 + int(k * b)
            else:
                x3 = x1
                y3 = y1 - math.floor((width - 1) / 2)
                x4 = x1
                y4 = y1 + math.ceil((width - 1) / 2)
            self.line([(x3, y3), (x4, y4)], fill=fill, width=1)
        return

    def dashed_line(self, xy, dash=(2, 2), fill=None, width=0):
        # xy – Sequence of 2-tuples like [(x, y), (x, y), ...]
        for i in range(len(xy) - 1):
            x1, y1 = xy[i]
            x2, y2 = xy[i + 1]
            x_length = x2 - x1
            y_length = y2 - y1
            length = math.sqrt(x_length ** 2 + y_length ** 2)
            dash_enabled = True
            postion = 0
            while postion <= length:
                for dash_step in dash:
                    if postion > length:
                        break
                    if dash_enabled:
                        start = postion / length
                        end = min((postion + dash_step - 1) / length, 1)
                        self.thick_line([(round(x1 + start * x_length),
                                          round(y1 + start * y_length)),
                                         (round(x1 + end * x_length),
                                          round(y1 + end * y_length))],
                                        xy, fill, width)
                    dash_enabled = not dash_enabled
                    postion += dash_step
        return

    def dashed_rectangle(self, xy, dash=(2, 2), outline=None, width=0):
        # xy - Sequence of [(x1, y1), (x2, y2)] where (x1, y1) is top left corner and (x2, y2) is bottom right corner
        x1, y1 = xy[0]
        x2, y2 = xy[1]
        halfwidth1 = math.floor((width - 1) / 2)
        halfwidth2 = math.ceil((width - 1) / 2)
        min_dash_gap = min(dash[1::2])
        end_change1 = halfwidth1 + min_dash_gap + 1
        end_change2 = halfwidth2 + min_dash_gap + 1
        odd_width_change = (width - 1) % 2
        self.dashed_line([(x1 - halfwidth1, y1), (x2 - end_change1, y1)],
                         dash, outline, width)
        self.dashed_line([(x2, y1 - halfwidth1), (x2, y2 - end_change1)],
                         dash, outline, width)
        self.dashed_line([(x2 + halfwidth2, y2 + odd_width_change),
                          (x1 + end_change2, y2 + odd_width_change)],
                         dash, outline, width)
        self.dashed_line([(x1 + odd_width_change, y2 + halfwidth2),
                          (x1 + odd_width_change, y1 + end_change2)],
                         dash, outline, width)
        return