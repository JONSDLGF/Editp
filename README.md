# EDIT++ (v1.1.0) — Documentación del código

Descripción
----------
Este script implementa un editor de texto de terminal minimalista (EDIT++). Usa control de terminal por secuencias ANSI y una utilidad llamada `ttytools` para manejo no bloqueante del TTY, dibujo de rectángulos y limpieza. Soporta múltiples ficheros abiertos en pestañas, movimiento por teclado, modo inserción, desfacer (undo) básico y ejecución de comandos de línea.

Resumen rápido de características
- Abrir uno o varios ficheros con `-o file1 file2 ...`
- Ayuda rápida con `-h`
- Interfaz en modo terminal con pestañas
- Modo inserción y modo normal
- Comandos en línea (al presionar ESC)
  - `open [path]`, `save`, `sass [path]`, `tab <|>`, `line [n]`, `row [n]`, `z` (undo), `cmd [shell]`, `exit`
- Undo simple por línea (almacena la línea antes del cambio)
- Uso de `ttytools.NonBlockingTTY()` para lectura no bloqueante

Requisitos
----------
- Python 3.7+
- Módulo `ttytools` (no estándar). El código usa:
  - `ttytools.NonBlockingTTY()` (context manager)
  - `ttytools.clear()`
  - `ttytools.rect(...)`
  Si `ttytools` no está disponible, el editor no funcionará.

Estructura y variables principales
---------------------------------
- ROOT_DIR: ruta del directorio del script.
- ver: versión del editor (`"v1.1.0"`).
- tab: índice de pestaña activa (entero).
- rlist: lista de rutas de archivos abiertos (lista de strings).
- texts: diccionario que mapea ruta -> [ contenido (str), historial_de_cambios (lista), puntero_historial (int) ]
  - texts[path][0]: contenido completo del fichero (str)
  - texts[path][1]: lista de cambios para undo; cada entrada es una tupla `(índice_de_línea, contenido_viejo o None)`
  - texts[path][2]: índice/puntero (no usado activamente para redo en el estado actual)

Estado de cursor / scroll / render
- cur_y: coordenada Y del cursor virtual (1-based en la UI).
- cur_x: coordenada X del cursor virtual.
- scrool_y: desplazamiento vertical (líneas arriba/abajo).
- scrool_x: desplazamiento horizontal (columnas).
- mesg: mensaje de estado mostrado en la UI.
- ins: booleano que indica modo inserción (True/False).
- render: si se debe volver a dibujar la pantalla.
- loop: controla el bucle principal del editor.

Inicialización
--------------
- Si se pasa `-o`, las rutas siguientes en argv se añaden a `rlist`.
- Si no se pasa nada, se crea una pestaña por defecto con `/unknow.txt`.
- Para cada fichero en `rlist` se lee su contenido y se crea la entrada en `texts`.
- Se activa el "alternate screen buffer" del terminal con `\x1b[?1049h` y se oculta el cursor `\x1b[?25l`.

Bucle principal (alto nivel)
----------------------------
1. Se entra en `with ttytools.NonBlockingTTY() as NBT:` para lecturas no bloqueantes del stdin.
2. Mientras `loop` sea True:
   - Si `render` es True:
     - Obtiene el tamaño del terminal (`os.get_terminal_size()`).
     - Ajusta `cur_x`, `cur_y` y `scrool_x`, `scrool_y` según límites.
     - Dibuja la barra de pestañas (divide la pantalla por el número de archivos).
     - Dibuja la caja principal de edición con `ttytools.rect(...)`.
     - Muestra las líneas visibles del archivo actual (respectando scroll).
     - Posiciona un marcador de cursor con colores ANSI.
   - Lee 1 byte de stdin: `cmr = sys.stdin.buffer.read(1)`.
   - Si `cmr` está vacío: no hay dato y no se renderiza.
   - Si `cmr == b"\x1b"` (ESC):
     - Lee la siguiente secuencia.
     - Si es una flecha (`ESC [ A/B/C/D`) ajusta `cur_x`, `cur_y`.
     - Si no es una secuencia de flecha, entra en modo "comando de texto" mostrando una línea para introducir un comando:
       - Sale temporalmente del modo NonBlocking (invoca `NBT.__exit__()`), pide `input()` y vuelve a entrar.
       - Interpreta el comando con un patrón `match` por prefijos.
       - Comandos soportados (ver sección "Comandos"):
         - `save`, `exit`, `z`, `cmd <...>`, `tab <|>`, `row n`, `open path`, `line n`, `sass path`.
   - Si `cmr` no es ESC:
     - Trata como edición en la línea actual:
       - Calcula `idx_y`, `idx_x` (índices 0-based según scroll y posicionamiento).
       - Antes de modificar, guarda en el historial la tupla `(índice_de_línea, contenido_viejo)` para permitir undo.
       - Soporta:
         - BACKSPACE (0x08 o 0x7f): borra carácter previo o elimina la línea si está vacía.
         - ENTER (10 o 13): divide la línea en dos (inserta nueva línea).
         - Inserción normal: inserta o sustituye caracteres según `ins`.
       - Si se escribe en una línea nueva más allá del final, añade un registro `(len(chars), None)` al historial y crea la nueva línea con el carácter.
       - Actualiza `texts[path][0]` con el contenido nuevo al final.
3. Al salir del bucle, restaura el buffer alternativo y el cursor con `\x1b[?1049l\x1b[?25h`.

Comandos soportados (introducidos tras ESC)
-------------------------------------------
- save
  - Guarda el buffer actual en el fichero `rlist[tab]` (intenta `open(..., "w").write(...)`).
  - Si falla, establece `mesg = "SASS?"` (mensaje de error en código original).
- sass [path]
  - "Save as": guarda el contenido actual en la ruta indicada.
- exit
  - Cierra el editor (loop = False).
- z
  - Undo básico: extrae la última entrada del historial `texts[path][1]` y la restaura:
    - Si el contenido viejo es `None`, elimina la línea (fue una línea recién creada).
    - Si había contenido, lo restaura en la línea correspondiente.
  - Mensajes: `ZOK` si OK, `ZNON` si no hay cambios que deshacer.
- cmd [shell command]
  - Sale del modo alterno del terminal (`\x1b[?1049l`) y ejecuta `os.system()` con la parte después de `cmd `; espera ENTER para volver y reentra en modo alterno.
- open [path]
  - Si el fichero existe y es archivo, lo añade a `rlist` (si no estaba) y lo abre (pone `tab` a esa pestaña).
- tab < o >
  - Cambia la pestaña activa anterior / siguiente.
- line [n]
  - Mueve el cursor vertical a la línea n.
- row [n]
  - Mueve el cursor horizontal a la columna n.

Manejo de cursor y posicionamiento (detalles)
--------------------------------------------
- El sistema usa coordenadas visuales 1-based para `cur_x` y `cur_y`, y luego las transforma para índices 0-based cuando se trabaja con listados de líneas.
- El cálculo de dónde posicionar el cursor en pantalla:
  - Se usa `f"\x1b[{fila};{col}H"` para ubicar el cursor de terminal.
  - El editor dibuja un "cursor visual" con colores invertidos: `\x1b[35m\x1b[47m \x1b[0m`.
- Las variables `scrool_y` y `scrool_x` controlan qué porción del texto está visible.

Formato interno de texto
------------------------
- El contenido se mantiene como una sola cadena con saltos de línea (`texts[path][0]`).
- Al editar se transforma temporalmente en lista de líneas (`splitlines()`), se modifica y luego se une con `"\n".join(...)`.
- El undo guarda solo la línea previa (no un diff completo), por lo que:
  - No hay redo implementado.
  - Cambios complejos (p. ej. inserciones multi-línea) pueden no deshacerse correctamente en todos los casos.

Dependencias y utilidades externas
---------------------------------
- `ttytools`: módulo externo esperado para:
  - Gestión del TTY en modo no bloqueante
  - Dibujo de rectángulos en pantalla y limpieza del terminal
  - Si no se dispone, se puede sustituir implementando funciones alternativas para:
    - Entrar/salir de NonBlockingTTY
    - `clear()` (p. ej. enviar `\x1b[2J\x1b[H`)
    - `rect()` (dibujar cuadros con líneas y texto)

Limitaciones conocidas y observaciones
-------------------------------------
- Mensajes y labels:
  - El texto "NORMNAL" en la UI es un typo (probablemente debería ser "NORMAL").
  - Mensajes como "SASS?" y "Opend" contienen ortografía/ingles mezclado.
- Manejo de inserción y borrado:
  - La lógica para insertar borrar caracteres (cur_x/cur_y y `idx_x`) es algo frágil; hay operaciones con offsets `-2`, `-1`, etc., que pueden causar off-by-one en bordes.
  - Algunos cálculos de `cur_x`/`cur_y` y `scrool_*` son heurísticos y podrían comportarse raro en terminales muy pequeñas.
- Undo:
  - Solo guarda una versión por línea. No hay undo por carácter ni tiempo limitado.
  - No hay manejo de histórico persistente ni redo.
- Lectura de teclas:
  - Solo se lee 1 byte a la vez; secuencias UTF-8 multibyte no se manejan bien (solo bytes individuales se convierten a `chr(key)`).
  - Soporta ASCII básico y flechas, pero no combinaciones más complejas.
- Compatibilidad:
  - Depende de comportamiento ANSI estándar; puede variar entre emuladores de terminal.
  - No hay manejo de señales (SIGWINCH para resize, p. ej. relectura de tamaño de terminal solo en render).

Sugerencias de mejora
---------------------
- Arreglar typos y mensajes para mayor claridad.
- Implementar manejo correcto de UTF-8 (decodificar secuencias de bytes completas).
- Mejorar la estructura de undo (p. ej. guardar diffs o snapshots por cambio).
- Añadir soporte para guardar automáticamente y confirmar antes de cerrar si hay cambios no guardados.
- Implementar manejo de redimensionado de terminal mediante SIGWINCH para actualizar render en tiempo real.
- Extraer la lógica de render y la lógica de edición en clases separadas para facilitar pruebas unitarias.
- Añadir tests automatizados y validación de entradas.
- Documentar o incluir `ttytools` o reemplazarlo por una dependencia más conocida (p. ej. curses) si procede.

Ejemplos de uso
---------------
- Abrir el editor con varios ficheros:
  ```
  python edit.py -o archivo1.txt archivo2.txt
  ```
- Ver ayuda:
  ```
  python edit.py -h
  ```
- Dentro del editor, presionar ESC y escribir:
  - `open /ruta/al/archivo.txt`
  - `save`
  - `sass /ruta/nuevo.txt`
  - `tab >`
  - `line 10`
  - `row 5`
  - `cmd ls -la`
  - `z`  (deshacer último cambio de línea)

Notas finales
-------------
Este README documenta la implementación actual según el código fuente provisto. Si quieres que genere:
- Un README con instrucciones para ejecutar y empaquetar `ttytools`,
- Un diagrama de flujo del bucle principal,
- O que traduzca nombres y mensajes al español correcto y arregle los typos del código (proponga un parche),
puedo hacerlo y preparar un patch o un nuevo archivo con cambios sugeridos.

Licencia
--------
No se especifica licencia en el código original. Añade una licencia al repositorio si lo vas a publicar (por ejemplo: MIT, Apache-2.0, GPLv3).
