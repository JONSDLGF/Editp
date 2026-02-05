import os
import sys

import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.resolve()

import ttytools

ver="v1.1.0"
tab = 0

rlist = []
texts = {}

if len(sys.argv)>1:
    if sys.argv[1] == "-o":
        rlist=sys.argv[2:]
    elif sys.argv[1] == "-h":
        print(
f"""
-----------------------------------------
   EDIT++ {ver} - Quick Help
-----------------------------------------
COMMANDS (Press ESC to type):

  open [file]    Open a new file
  save           Save current buffer
  sass [path]    Save as (custom path)
  
  tab <          Previous tab
  tab >          Next tab
  
  line [n]       Jump to line
  row [n]        Jump to column
  
  z              Undo last change
  cmd [shell]    Run system command
  exit           Close editor

HOTKEYS:
  Arrows         Move cursor
  Backspace      Delete character
  Enter          New line / Execute cmd
-----------------------------------------
"""
)
        sys.exit(-1)
    else:
        sys.stdout.write("why, use -h for more info")
        sys.exit(-1)

if len(rlist):
    for i in rlist:
        texts[i] = [
            open(i, "r").read(),
            [],
            0
        ]
else:
    rlist.append("/unknow.txt")
    texts[rlist[0]] = [ "", [], 0 ]

cur_y=1
cur_x=0
scrool_y=0
scrool_x=0

mesg="OK"

sys.stdout.write("\x1b[?1049h\x1b[?25l")

ins = False
render= True
loop = True
with ttytools.NonBlockingTTY() as NBT:
    while loop:
        if render:
            Size = os.get_terminal_size()
            ttytools.clear()
            if cur_y>(Size.lines-6):
                scrool_y+=1
                cur_y=Size.lines-6
            if cur_y<0:
                if scrool_y>0:
                    scrool_y-=1
                cur_y=0
            if cur_x>(Size.columns-2):
                scrool_x+=1
                cur_x=Size.columns-2
            if cur_x<0:
                if scrool_x>0:
                    scrool_x-=1
                cur_x=0

            x = 1
            c = Size.columns//len(rlist)
            addh = ""
            for i in range(len(rlist)):
                addl = "" + "*" * (i == tab)
                ttytools.rect(
                    x,1,c,1,
                    info = (
                        addl + str(rlist[i])[10-c:] + addh
                    )
                )
                x += c

            ttytools.rect(
                1,
                2,
                Size.columns,
                Size.lines-4,
                divmod(cur_y,(Size.lines-5))[0],
                info="MODE " + "INSERT"*ins + "NORMNAL"*(not ins)
            )
            
            i     = 0
            char  = texts[rlist[tab]][0].splitlines()

            while (i<(Size.lines-6))and((i+scrool_y)<len(char)):
                sys.stdout.write(
                    f"\x1b[{3+i};{2}H"+
                    char[i+scrool_y][scrool_x:scrool_x+Size.columns-2]+"\n"
                )
                i+=1

            sys.stdout.write(
                f"\x1b[{divmod(cur_y,(Size.lines-5))[1]+2};{cur_x}H"
                "\x1b[35m\x1b[47m \x1b[0m")
            sys.stdout.flush()

        cmr = sys.stdin.buffer.read(1)

        render=True
        if not cmr:
            render=False
        elif cmr == b"\x1b":
            cmd = sys.stdin.buffer.read(1)
            if cmd == b"[":
                cmd_ = sys.stdin.buffer.read(1)
                if   cmd_ == b"A": cur_y -= 1
                elif cmd_ == b"B": cur_y += 1
                elif cmd_ == b"C": cur_x += 1
                elif cmd_ == b"D": cur_x -= 1
            else:
                y=Size.lines
                ttytools.rect(1,y-2,Size.columns,3)
                sys.stdout.write(f"\x1b[{y-1};{2}H" "[" + mesg + "]>")
                sys.stdout.write("\x1b[?25h") # Mostrar cursor para escribir
                sys.stdout.flush()
                NBT.__exit__()
                command = input("")
                NBT.__enter__()
                sys.stdout.write("\x1b[?25l") # Ocultar
                for i in [
                    [
                        0,command
                    ],[
                        1,command[:3]
                    ],[
                        2,command[:4]
                    ]]:
                    match i:
                        case [0,"save"]:
                            try:
                                open(rlist[tab],"w").write(texts[rlist[tab]][0])
                            except:
                                mesg = "SASS?"
                                break
                        case [0,"exit"]:
                            loop = False
                        case [0,"z"]:
                            t = texts[rlist[tab]]
                            if t[1]:
                                linea_idx, contenido_viejo = t[1].pop()
                                actual_chars = t[0].splitlines()
                                
                                if contenido_viejo is None:
                                    # Si antes no existía, la borramos
                                    actual_chars.pop(linea_idx)
                                else:
                                    # Si existía, restauramos su valor
                                    actual_chars[linea_idx] = contenido_viejo
                                
                                t[0] = "\n".join(actual_chars)
                                mesg = "ZOK"
                            else:
                                mesg = "ZNON"
                        case [1,"cmd"]:
                            sys.stdout.write("\x1b[?1049l\x1b[?25h")
                            sys.stdout.write(f"Runing: {command[4:]}\n\n")
                            sys.stdout.flush()
                            os.system(command[4:])
                            input("\n[Press Enter to return the editor]")
                            sys.stdout.write("\x1b[?1049h\x1b[?25l")
                            sys.stdout.flush()
                        case [1,"tab"]:
                            com = command[3:]
                            if com=="<":
                                tab = max(tab-1,0)
                            if com==">":
                                tab = min(tab+1,len(rlist)-1)
                        case [1,"row"]:
                            cur_x = max(int(command[4:]),0)
                        case [2,"open"]:
                            rootp = pathlib.Path(command[5:])
                            root = command[5:]
                            if rootp.exists() and rootp.is_file():
                                if root not in rlist:
                                    rlist.append(root)
                                    texts[root] = [
                                        rootp.read_text(),
                                        [],
                                        0
                                    ]
                                tab = len(rlist) - 1
                                mesg = "Opend"
                            else:
                                mesg = "File not exist"
                        case [2,"line"]:
                            cur_y = max(int(command[5:]),0)
                        case [2,"sass"]:
                            open(command[5:],"w").write(texts[rlist[tab]][0])
                        case _:
                            mesg="cmd?"
        else:
            chars:list = texts[rlist[tab]][0].splitlines()
            idx_y = (cur_y+scrool_y) - 1  # Ajustamos para índice 0-based
            idx_x = cur_x+scrool_x-2
            if idx_y < len(chars):
                # Guardamos: (número de línea, contenido antiguo)
                # Usamos .append() porque la lista empieza vacía
                cambio = (idx_y, chars[idx_y])
                texts[rlist[tab]][1].append(cambio)
                
                # Actualizamos el puntero (opcional, si quieres manejar Redo luego)
                texts[rlist[tab]][2] = len(texts[rlist[tab]][1]) - 1
                
                # 1. Aseguramos que cmr sea un valor comparable (entero)
                key = cmr[0] if isinstance(cmr, bytes) else cmr
                if idx_y < 0:
                    continue
                c = list(chars[idx_y])
                
                # --- BORRAR (Backspace) ---
                if key in [0x08, 0x7f]:
                    if len(c)<1: # Si la línea está vacía, la eliminamos
                        if len(chars) < 1:
                            chars.pop(idx_y)
                            cur_y = max(1, cur_y - 1)
                    else:
                        # Borramos el último carácter (o podrías usar c.pop(idx_x-1))
                        if ins:
                            c = c[:-1]
                        else:
                            c = [*c[:max(0, cur_x - 2)],*c[max(1, cur_x - 1):]]
                        chars[idx_y] = "".join(c)
                        cur_x = max(1, cur_x - 1)

                # --- ENTER (Salto de línea) ---
                elif key in [10, 13]: # \n o \r
                    # Dividimos la línea actual en dos partes según el cursor
                    izquierda = "".join(c[:idx_x])
                    derecha = "".join(c[idx_x:])
                    chars[idx_y] = izquierda
                    chars.insert(idx_y + 1, derecha)
                    cur_y += 1
                    cur_x = 0

                # --- ESCRITURA NORMAL ---
                elif idx_x >= len(c):
                    if ins:
                        c[idx_x] = chr(key)
                    else:
                        c=[*c[:idx_x],chr(key),*c[idx_x:]]
                    chars[idx_y] = "".join(c)
                    cur_x += 1
                else:
                    c.append(chr(key))
                    chars[idx_y] = "".join(c)
                    cur_x += 2

            else:
                key = cmr[0] if isinstance(cmr, bytes) else cmr
                if key in [0x08, 0x7f]:
                    cur_y = max(1, cur_y - 1)
                else:
                    # Si escribimos en una línea nueva, guardamos que antes no había nada
                    texts[rlist[tab]][1].append((len(chars), None))
                    chars.append(chr(cmr[0]))
                
            texts[rlist[tab]][0] = "\n".join(chars)
            mesg = "OK"
    NBT.__exit__()
    sys.stdout.write("\x1b[?1049l\x1b[?25h")