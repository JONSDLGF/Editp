import sys

def rect(x,y,w,h,sh=None,sw=None,info=""):
    w-=2
    sys.stdout.write(
        f"\x1b[{y};{x}H" +
        "+" + "-"*w + "+"
    )
    if info!="":
        sys.stdout.write(
            f"\x1b[{y};{x+1}H" +
            ("[" + info + "]")
        )
    if h!=1:
        h-=2
        for i in range(h):
            sys.stdout.write(
                f"\x1b[{y+i+1};{x}H" +
                "|" + " "*w + "|"
            )
        sys.stdout.write(
            f"\x1b[{y+i+2};{x}H" +
            "+" + "-"*w + "+"
        )
        if sh!=None:
            sys.stdout.write(
                f"\x1b[{y+sh};{x+w+1}H" +
                "#"
            )
        if sw!=None:
            sys.stdout.write(
                f"\x1b[{y+h+1};{x+sw}H" +
                "#"
            )

clear=lambda:\
    sys.stdout.write("\x1b[H\x1b[2J\x1b[3J")


import termios
import tty
import select

class NonBlockingTTY:
    def __enter__(self):
        # Guardamos la configuración original
        self.old_settings = termios.tcgetattr(sys.stdin)
        # Ponemos la terminal en modo "cbreak" (lectura carácter a carácter)
        tty.setcbreak(sys.stdin.fileno())
        return self

    def __exit__(self):
        # Al salir (o si hay error), restauramos la terminal
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)