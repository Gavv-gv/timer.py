"""
MicroPython max7219 cascadable 8x8 LED matrix driver
https://github.com/mcauser/micropython-max7219

MIT License
Copyright (c) 2017 Mike Causer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from micropython import const
import framebuf2 as framebuf

_NOOP = const(0)
_DIGIT0 = const(1)
_DECODEMODE = const(9)
_INTENSITY = const(10)
_SCANLIMIT = const(11)
_SHUTDOWN = const(12)
_DISPLAYTEST = const(15)

class Matrix8x8:
    def __init__(self, spi, cs, num):
        """
        Driver for cascading MAX7219 8x8 LED matrices.

        >>> import max7219
        >>> from machine import Pin, SPI
        >>> spi = SPI(1)
        >>> display = max7219.Matrix8x8(spi, Pin('X5'), 4)
        >>> display.text('1234',0,0,1)
        >>> display.show()

        """
        self.spi = spi
        self.cs = cs
        self.cs.init(cs.OUT, True)
        self.buffer = bytearray(8*num)
        self.num = num
        fb = framebuf.FrameBuffer(self.buffer,8*num,8, framebuf.MONO_HLSB)
        self.framebuf = fb
        # Provide methods for accessing FrameBuffer graphics primitives. This is a workround
        # because inheritance from a native class is currently unsupported.
        # http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
        self.fill = fb.fill  # (col)
        self.pixel = fb.pixel # (x, y[, c])
        self.hline = fb.hline  # (x, y, w, col)
        self.vline = fb.vline  # (x, y, h, col)
        self.line = fb.line  # (x1, y1, x2, y2, col)
        self.rect = fb.rect  # (x, y, w, h, col)
        self.fill_rect = fb.fill_rect  # (x, y, w, h, col)
        self.text = fb.text  # (string, x, y, col=1)
        self.scroll = fb.scroll  # (dx, dy)
        self.blit = fb.blit  # (fbuf, x, y[, key])
        self.init()

    def large_text(self, s, x, y, m, c: int = 1, r: int = 0, t=None):
        """
        large text drawing function uses the standard framebuffer font (8x8 pixel characters)
        writes text, s,
        to co-cordinates x, y
        size multiple, m (integer, eg: 1,2,3,4. a value of 2 produces 16x16 pixel characters)
        colour, c [optional parameter, default value c=1]
        optional parameter, r is rotation of the text: 0, 90, 180, or 270 degrees
        optional parameter, t is rotation of each character within the text: 0, 90, 180, or 270 degrees
        """
        colour = c
        smallbuffer = bytearray(8)
        letter = framebuf.FrameBuffer(smallbuffer, 8, 8, framebuf.MONO_HMSB)
        r = r % 360 // 90
        dx = 8 * m if r in (0, 2) else 0
        dy = 8 * m if r in (1, 3) else 0
        if r in (2, 3):
            s = self._reverse(s)
        t = r if t is None else t % 360 // 90
        a, b, c, d = 1, 0, 0, 1
        for i in range(0, t):
            a, b, c, d = c, d, -a, -b
        x0 = 0 if a + c > 0 else 7
        y0 = 0 if b + d > 0 else 7
        for character in s:
            letter.fill(0)
            letter.text(character, 0, 0, 1)
            for i in range(0, 8):
                for j in range(0, 8):
                    if letter.pixel(i, j) == 1:
                        p = x0 + a * i + c * j
                        q = y0 + b * i + d * j
                        if m == 1:
                            self.pixel(x + p, y + q, colour)
                        else:
                            self.fill_rect(x + p * m, y + q * m, m, m, colour)
            x += dx
            y += dy

    def _write(self, command, data):
        self.cs(0)
        for m in range(self.num):
            self.spi.write(bytearray([command, data]))
        self.cs(1)

    def init(self):
        for command, data in (
            (_SHUTDOWN, 0),
            (_DISPLAYTEST, 0),
            (_SCANLIMIT, 7),
            (_DECODEMODE, 0),
            (_SHUTDOWN, 1),
        ):
            self._write(command, data)

    def brightness(self, value):
        if not 0 <= value <= 15:
            raise ValueError("Brightness out of range")
        self._write(_INTENSITY, value)

    def show(self):
        for y in range(8):
            self.cs(0)
            for m in range(self.num):
                self.spi.write(bytearray([_DIGIT0 + y, self.buffer[(y * self.num) + m]]))
            self.cs(1)

