import kivy
kivy.require("1.8.1")
from kivy.effects.dampedscroll import DampedScrollEffect
from time import time

class call_control:

    def __init__(self, max_call_interval):
        self._max_call_interval = max_call_interval
        self._last_call = time()

    def __call__(self, function):

        def wrapped(*args, **kwargs):
            now = time()

            if now - self._last_call > self._max_call_interval:
                self._last_call = now

                function(*args, **kwargs)

        return wrapped


class Effect(DampedScrollEffect):
    def __init__(self, Next, Prev, **kwargs):
        super().__init__(**kwargs)
        self.next = Next
        self.prev = Prev
    def on_overscroll(self, *args):
        super().on_overscroll(*args)

        if self.overscroll < -50:
            self.changeChap(self.prev)
        elif self.overscroll > 50:
            self.changeChap(self.next)

    @call_control(max_call_interval=2)
    def changeChap(self, func):
        return func()

from kivy.clock import Clock
from kivy.uix.button import Button
import timeit

class MultiExpressionButton(Button):

    def __init__(self, **kwargs):
        super(MultiExpressionButton, self).__init__(**kwargs)
        self.start = 0
        self.single_hit = 0
        self.press_state = False
        self.register_event_type('on_single_press')
        self.register_event_type('on_double_press')
        self.register_event_type('on_long_press')

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            self.start = timeit.default_timer()
            if touch.is_double_tap:
                self.press_state = True
                self.single_hit = 0
                self.dispatch('on_double_press')
        else:
            return super(MultiExpressionButton, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.press_state is False:
            if self.collide_point(touch.x, touch.y):
                stop = timeit.default_timer()
                awaited = stop - self.start

                def not_double(time):
                    nonlocal awaited
                    if awaited > 0.3:
                        self.dispatch('on_long_press')
                    else:
                        self.dispatch('on_single_press')

                self.single_hit = Clock.schedule_once(not_double, 0.2)
            else:
                return super(MultiExpressionButton, self).on_touch_down(touch)
        else:
            self.press_state = False

    def on_single_press(self):
        pass

    def on_double_press(self):
        pass

    def on_long_press(self):
        pass

# Unused multithreading / multiprocessing decorator that for some reason wont work,
# possibly due to wraps decorator not being defined or clear on what it can do
from concurrent.futures import ThreadPoolExecutor
_DEFAULT_POOL = ThreadPoolExecutor()
def threadpool(f, executor=None):
    @wraps(f)
    def wrap(*args, **kwargs):
        return (executor or _DEFAULT_POOL).submit(f, *args, **kwargs)

    return wrap

from webdata import UrlReading
def asList(url):
    data = UrlReading(url)
    return data.current, data.title, data.next, data.prev, data.content