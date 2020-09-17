from random import randint
from asciimatics.screen import Screen

def demo(screen):
    while True:
        screen.print_at('Hello world!',
                        5, randint(0, 5),
                        colour=randint(0, screen.colours - 1),
                        bg=randint(0, screen.colours - 1))
        ev = screen.get_key()
        if ev in (ord('Q'), ord('q')):
            return
        screen.refresh()

Screen.wrapper(demo)
