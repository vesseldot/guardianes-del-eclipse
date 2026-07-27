"""
interfaz.py — HUD, menus, seleccion de guardian, tienda y transiciones.

Regla de rendimiento que se aplica en todo el archivo: los elementos de UI
se crean UNA vez y despues solo se muestran u ocultan. Ademas los textos
solo se reescriben cuando su valor cambia, porque asignar .text obliga a
regenerar la geometria del texto y hacerlo cada frame se nota.
"""

from ursina import (Entity, Text, Button, Quad, camera, color as ucolor,
                    Vec2, Vec3, destroy)
from datos import GUARDIANES, OBJETOS
from config import RAIZ
from entorno import cargar_textura

CLARO = ucolor.rgb32(240, 238, 232)
TENUE = ucolor.rgb32(150, 148, 142)
PANEL = ucolor.rgba32(20, 20, 22, 190)
RESALTE = ucolor.rgba32(150, 120, 40, 230)   # boton actualmente elegido

DIR_UI = RAIZ / "assets" / "ui"

# Cache de texturas de interfaz: varias pantallas pueden pedir la misma imagen
# y cargarla dos veces seria pagar dos veces la memoria.
_cache_ui = {}


def cargar_ui(archivo, max_lado=1920):
    """Textura de 'assets/ui', o None si la imagen todavia no existe.

    Se pasa por entorno.cargar_textura porque la ruta del proyecto lleva
    acentos y el cargador por nombre de Ursina falla con ella. Si falta el
    archivo, la pantalla se dibuja sin fondo igual que antes: el juego nunca
    depende de que el arte este terminado.
    """
    if archivo in _cache_ui:
        return _cache_ui[archivo]
    ruta = DIR_UI / archivo
    tex = cargar_textura(ruta, repetir=False, max_lado=max_lado) if ruta.exists() else None
    if tex is None:
        print(f"[interfaz] sin imagen de fondo para {archivo}")
    _cache_ui[archivo] = tex
    return tex


class Pantalla:
    """Base: agrupa elementos y los muestra u oculta en bloque."""

    def __init__(self, fondo=None):
        self.raiz = Entity(parent=camera.ui, enabled=False)
        self.fondo = self._poner_fondo(fondo) if fondo else None

    def _poner_fondo(self, archivo):
        """Imagen a pantalla completa detras del resto de la pantalla.

        z=1 la manda al fondo: en camera.ui lo que tiene mas z se dibuja
        detras, asi que textos y botones (z=0) quedan por delante. La escala
        es (aspect_ratio, 1) porque el espacio de UI mide 1 de alto y
        'aspect_ratio' de ancho: eso cubre la pantalla justa.
        """
        tex = cargar_ui(archivo)
        if tex is None:
            return None
        return Entity(parent=self.raiz, model="quad", texture=tex,
                      scale=(camera.aspect_ratio, 1), z=1)

    def mostrar(self):
        self.raiz.enabled = True

    def ocultar(self):
        self.raiz.enabled = False


# ---------------------------------------------------------------- HUD
class HUD(Pantalla):

    def __init__(self):
        super().__init__()

        self.txt_jugador = Text(parent=self.raiz, text="", origin=(-.5, .5),
                                position=(-.86, .46), scale=.85, color=CLARO)
        self.barra_jugador_fondo = Entity(parent=self.raiz, model="quad", color=PANEL,
                                          scale=(.34, .022), position=(-.69, .41))
        self.barra_jugador = Entity(parent=self.raiz, model="quad", color=ucolor.rgb32(210, 205, 195),
                                    scale=(.34, .022), position=(-.69, .41), origin=(-.5, 0))
        self.barra_jugador.x = -.86

        # Estamina (verde) y FP (azul) apiladas bajo la vida.
        Entity(parent=self.raiz, model="quad", color=PANEL,
               scale=(.34, .016), position=(-.69, .378))
        self.barra_estamina = Entity(parent=self.raiz, model="quad", color=ucolor.rgb32(140, 190, 95),
                                     scale=(.34, .016), position=(-.86, .378), origin=(-.5, 0))
        Entity(parent=self.raiz, model="quad", color=PANEL,
               scale=(.34, .016), position=(-.69, .35))
        self.barra_fp = Entity(parent=self.raiz, model="quad", color=ucolor.rgb32(90, 150, 220),
                               scale=(.34, .016), position=(-.86, .35), origin=(-.5, 0))

        self.txt_frascos = Text(parent=self.raiz, text="", origin=(-.5, .5),
                                position=(-.86, .31), scale=.75, color=CLARO)

        # Arma y hechizo equipados (abajo a la izquierda).
        self.txt_arma = Text(parent=self.raiz, text="", origin=(-.5, 0),
                             position=(-.86, -.34), scale=.8, color=CLARO)
        self.txt_hechizo = Text(parent=self.raiz, text="", origin=(-.5, 0),
                                position=(-.86, -.40), scale=.8, color=CLARO)

        self.txt_jefe = Text(parent=self.raiz, text="", origin=(0, 0),
                             position=(0, -.36), scale=.9, color=CLARO)
        self.barra_jefe_fondo = Entity(parent=self.raiz, model="quad", color=PANEL,
                                       scale=(.62, .026), position=(0, -.41))
        self.barra_jefe = Entity(parent=self.raiz, model="quad", color=ucolor.rgb32(215, 120, 110),
                                 scale=(.62, .026), position=(-.31, -.41), origin=(-.5, 0))

        self.txt_fase = Text(parent=self.raiz, text="", origin=(.5, 0),
                             position=(.86, -.44), scale=.7, color=TENUE)
        self.txt_fragmentos = Text(parent=self.raiz, text="", origin=(.5, .5),
                                   position=(.86, .46), scale=.8, color=CLARO)

        # Indicador de fijado (lock-on) sobre la barra del jefe.
        self.txt_fijado = Text(parent=self.raiz, text="", origin=(0, 0),
                               position=(0, -.31), scale=.7, color=RESALTE)

        # Cache de ultimos valores para no reescribir texto cada frame.
        self._ult = dict(vida=-1, jefe=-1, fase=-1, frag=-1, nombre="", nombre_jefe="",
                         est=-1, fp=-1, frascos=-1, arma="", hechizo="",
                         hlisto=None, fijado=None)

    def actualizar(self, jugador, jefe, fragmentos):
        if jugador.nombre != self._ult["nombre"]:
            self.txt_jugador.text = jugador.nombre
            self._ult["nombre"] = jugador.nombre

        vida = int(jugador.vida)
        if vida != self._ult["vida"]:
            pct = max(0.0, jugador.vida / jugador.vida_max)
            self.barra_jugador.scale_x = .34 * pct
            self._ult["vida"] = vida

        est = int(jugador.estamina)
        if est != self._ult["est"]:
            self.barra_estamina.scale_x = .34 * max(0.0, jugador.estamina / jugador.estamina_max)
            self._ult["est"] = est

        fp = int(jugador.fp)
        if fp != self._ult["fp"]:
            self.barra_fp.scale_x = .34 * max(0.0, jugador.fp / jugador.fp_max)
            self._ult["fp"] = fp

        if jugador.frascos != self._ult["frascos"]:
            self.txt_frascos.text = f"frascos  {jugador.frascos}"
            self._ult["frascos"] = jugador.frascos

        if jugador.arma["nombre"] != self._ult["arma"]:
            self.txt_arma.text = f"arma  {jugador.arma['nombre']}"
            self._ult["arma"] = jugador.arma["nombre"]

        # El hechizo: nombre + color segun este listo (verde/claro) o no (tenue).
        listo = jugador._cd_hechizo <= 0 and jugador.fp >= jugador.hechizo["costo_fp"]
        if jugador.hechizo["nombre"] != self._ult["hechizo"] or listo != self._ult["hlisto"]:
            self.txt_hechizo.text = f"hechizo  {jugador.hechizo['nombre']}"
            self.txt_hechizo.color = CLARO if listo else TENUE
            self._ult["hechizo"] = jugador.hechizo["nombre"]
            self._ult["hlisto"] = listo

        if jugador.fijado != self._ult["fijado"]:
            self.txt_fijado.text = "> objetivo fijado <" if jugador.fijado else ""
            self._ult["fijado"] = jugador.fijado

        if fragmentos != self._ult["frag"]:
            self.txt_fragmentos.text = f"fragmentos  {fragmentos}"
            self._ult["frag"] = fragmentos

        if jefe is None:
            self.txt_jefe.text = ""
            self.barra_jefe.scale_x = 0
            self.txt_fase.text = ""
            return

        if jefe.nombre != self._ult["nombre_jefe"]:
            self.txt_jefe.text = jefe.nombre.upper()
            self._ult["nombre_jefe"] = jefe.nombre

        vjefe = int(jefe.vida)
        if vjefe != self._ult["jefe"]:
            self.barra_jefe.scale_x = .62 * max(0.0, jefe.vida_pct)
            self._ult["jefe"] = vjefe

        if jefe.fase != self._ult["fase"]:
            self.txt_fase.text = f"fase {jefe.fase} / {jefe.total_fases}"
            self._ult["fase"] = jefe.fase


# ---------------------------------------------------------- TITULO
class PantallaTitulo(Pantalla):
    """Portada previa al menu: emblema y 'pulsa cualquier tecla'.

    Existe para que el juego no abra directamente en una lista de botones.
    Cualquier tecla o clic pasa al menu (ver Juego.tecla).
    """

    # Segundos de un ciclo completo de parpadeo del aviso.
    CICLO_AVISO = 2.4

    def __init__(self):
        super().__init__(fondo="menu.png")

        tex_logo = cargar_ui("logo.png", max_lado=1024)
        if tex_logo is not None:
            # Mas grande que en el menu: aqui el emblema es el protagonista y
            # no compite con ningun boton.
            self.logo = Entity(parent=self.raiz, model="quad", texture=tex_logo,
                               scale=(.84, .56), position=(0, .12), z=.5)
        else:
            Text(parent=self.raiz, text="GUARDIANES DEL ECLIPSE", origin=(0, 0),
                 position=(0, .12), scale=3.0, color=CLARO)

        self.aviso = Text(parent=self.raiz, text="pulsa cualquier tecla",
                          origin=(0, 0), position=(0, -.30), scale=1.0, color=CLARO)
        self._t = 0.0

    def actualizar(self, dt):
        """Parpadeo suave del aviso. Lo llama el bucle principal.

        Solo se toca el alfa del color, no el texto: reescribir .text obliga a
        regenerar la geometria y aqui pasaria 60 veces por segundo.
        """
        self._t = (self._t + dt) % self.CICLO_AVISO
        # Onda triangular entre 0 y 1, suavizada hacia los extremos.
        fase = self._t / self.CICLO_AVISO
        p = 1.0 - abs(2.0 * fase - 1.0)
        self.aviso.color = ucolor.rgba32(240, 238, 232, int(90 + 165 * p))


# ------------------------------------------------------------ MENU
class MenuPrincipal(Pantalla):

    def __init__(self, al_jugar, al_salir, al_calidad):
        super().__init__(fondo="menu.png")

        # El logo ya lleva el titulo dibujado, asi que sustituye al texto. Si
        # la imagen no esta, se cae al texto de siempre y el menu sigue
        # servible (mismo criterio que con los modelos que faltan).
        #
        # El emblema es 3:2 y ocupa la mitad superior: por eso los botones
        # bajan respecto al layout de solo texto, para no quedar debajo de el.
        tex_logo = cargar_ui("logo.png", max_lado=1024)
        if tex_logo is not None:
            self.logo = Entity(parent=self.raiz, model="quad", texture=tex_logo,
                               scale=(.60, .40), position=(0, .26), z=.5)
        else:
            Text(parent=self.raiz, text="GUARDIANES DEL ECLIPSE", origin=(0, 0),
                 position=(0, .30), scale=2.4, color=CLARO)
        Text(parent=self.raiz, text="un guardian queda en pie", origin=(0, 0),
             position=(0, .00), scale=.9, color=TENUE)

        self.btn_jugar = Button(parent=self.raiz, text="Jugar", scale=(.3, .07),
                                position=(0, -.10), color=PANEL)
        self.btn_jugar.on_click = al_jugar

        self.btn_calidad = Button(parent=self.raiz, text="Calidad: medio", scale=(.3, .07),
                                  position=(0, -.20), color=PANEL)
        self.btn_calidad.on_click = al_calidad

        self.btn_salir = Button(parent=self.raiz, text="Salir", scale=(.3, .07),
                                position=(0, -.30), color=PANEL)
        self.btn_salir.on_click = al_salir

        Text(parent=self.raiz, text="WASD moverse   ·   clic atacar   ·   espacio esquivar   ·   esc pausa",
             origin=(0, 0), position=(0, -.43), scale=.7, color=TENUE)

    def set_calidad(self, valor):
        self.btn_calidad.text = f"Calidad: {valor}"


# ---------------------------------------------------- INSTRUCCIONES
class Instrucciones(Pantalla):
    """Pantalla intermedia: explica premisa y controles antes del combate."""

    def __init__(self, al_comenzar):
        super().__init__(fondo="instrucciones.png")

        Text(parent=self.raiz, text="Como jugar", origin=(0, 0),
             position=(0, .42), scale=1.7, color=CLARO)
        Text(parent=self.raiz,
             text="Derrota a los guardianes corrompidos. Acercate a golpear con tu arma,\n"
                  "esquiva sus ataques y castiga desde lejos con hechizos.",
             origin=(0, 0), position=(0, .33), scale=.75, color=TENUE)

        # --- columna izquierda: movimiento y defensa ---
        Text(parent=self.raiz, text="MOVIMIENTO Y DEFENSA", origin=(-.5, 0),
             position=(-.6, .19), scale=.8, color=CLARO)
        Text(parent=self.raiz,
             text="WASD          moverse\n"
                  "Shift            correr (gasta estamina)\n"
                  "Espacio       esquivar / rodar (i-frames)\n"
                  "F                  fijar objetivo (lock-on)\n"
                  "Esc              pausa / menu",
             origin=(-.5, .5), position=(-.6, .13), scale=.72, color=CLARO)

        # --- columna derecha: combate ---
        Text(parent=self.raiz, text="COMBATE", origin=(-.5, 0),
             position=(.08, .19), scale=.8, color=CLARO)
        Text(parent=self.raiz,
             text="Clic izq        ataque ligero\n"
                  "Clic der       ataque pesado\n"
                  "Q                 lanzar hechizo (gasta FP)\n"
                  "E                  cambiar de hechizo\n"
                  "R                 beber frasco (curarse)\n"
                  "1 / 2 / 3       cambiar de arma",
             origin=(-.5, .5), position=(.08, .13), scale=.72, color=CLARO)

        # --- recursos ---
        Text(parent=self.raiz,
             text="Estamina (verde): esquivar y correr    ·    FP (azul): hechizos    ·    Frascos: curacion limitada",
             origin=(0, 0), position=(0, -.26), scale=.68, color=TENUE)

        self.btn = Button(parent=self.raiz, text="Comenzar", scale=(.3, .08),
                          position=(0, -.38), color=PANEL)
        self.btn.on_click = al_comenzar

        Text(parent=self.raiz, text="enter o espacio para comenzar",
             origin=(0, 0), position=(0, -.46), scale=.6, color=TENUE)


# ---------------------------------------------- SELECCION DE GUARDIAN
class SeleccionGuardian(Pantalla):

    def __init__(self, al_elegir, al_previsualizar=None):
        # La mitad derecha de la imagen es transparente: por ahi se ve el
        # modelo 3D del escaparate (camera.ui se dibuja sobre la escena).
        super().__init__(fondo="seleccion.png")
        Text(parent=self.raiz, text="Elige tu guardian", origin=(-.5, 0),
             position=(-.62, .40), scale=1.5, color=CLARO)

        self.al_elegir = al_elegir
        self.al_previsualizar = al_previsualizar
        self.claves = list(GUARDIANES.keys())
        self.botones = []
        self.indice = 0

        # Botones en una columna a la izquierda; el modelo 3D ocupa la derecha.
        for i, clave in enumerate(self.claves):
            b = Button(parent=self.raiz, text=GUARDIANES[clave]["nombre"].replace("Guardian ", "").replace("Guardiana ", ""),
                       scale=(.34, .075), color=PANEL,
                       position=(-.62, .26 - i * .095), origin=(-.5, 0))
            b.text_entity.scale *= .8
            b.on_click = self._hacer_callback(i)
            b.on_mouse_enter = self._hacer_hover(i)
            self.botones.append(b)

        self.info = Text(parent=self.raiz, text="", origin=(-.5, 0),
                         position=(-.62, -.32), scale=.85, color=CLARO)
        self.stats = Text(parent=self.raiz, text="", origin=(-.5, 0),
                          position=(-.62, -.40), scale=.7, color=TENUE)

        Text(parent=self.raiz, text="flechas / raton para ver  ·  enter, espacio o click para elegir",
             origin=(-.5, 0), position=(-.62, -.47), scale=.6, color=TENUE)

    # -- se llama al mostrar la pantalla: refresca resalte y previsualizacion
    def mostrar(self):
        super().mostrar()
        self._actualizar()

    def _hacer_callback(self, i):
        def _f():
            self.indice = i
            self.confirmar()
        return _f

    def _hacer_hover(self, i):
        def _f():
            self.indice = i
            self._actualizar()
        return _f

    # -- navegacion por teclado (la llama main.py con las flechas)
    def mover(self, delta):
        self.indice = (self.indice + delta) % len(self.claves)
        self._actualizar()

    def confirmar(self):
        self.al_elegir(self.claves[self.indice])

    def _actualizar(self):
        """Resalta el boton actual y refresca info, stats y modelo 3d."""
        for i, b in enumerate(self.botones):
            b.color = RESALTE if i == self.indice else PANEL

        clave = self.claves[self.indice]
        d = GUARDIANES[clave]
        self.info.text = d["descripcion"]
        self.stats.text = (f"vida {d['vida']}   dano {d['dano']}   "
                           f"velocidad {d['velocidad']}   cadencia {d['cadencia']}")
        if self.al_previsualizar:
            self.al_previsualizar(clave)


# ------------------------------------------------------------ TIENDA
class Tienda(Pantalla):

    def __init__(self, al_comprar, al_continuar):
        # Transparente por la izquierda: ahi aparece el mercader.
        super().__init__(fondo="tienda.png")
        # El modelo del mercader se muestra a la izquierda, asi que toda la
        # UI de la tienda vive en la mitad derecha. CX es el centro de columna.
        CX = .34
        Text(parent=self.raiz, text="Puesto del mercader", origin=(0, 0),
             position=(CX, .42), scale=1.3, color=CLARO)
        Text(parent=self.raiz, text='"Traigo cosas de lejos.\nEnsename que llevas."',
             origin=(0, 0), position=(CX, .34), scale=.7, color=TENUE)

        self.txt_frag = Text(parent=self.raiz, text="", origin=(0, 0),
                             position=(CX, .25), scale=.85, color=CLARO)

        self.botones = []
        for i, obj in enumerate(OBJETOS):
            b = Button(parent=self.raiz,
                       text=f"{obj['nombre']}  —  {obj['desc']}   [{obj['costo']}]",
                       scale=(.82, .07), position=(CX, .15 - i * .09), color=PANEL)
            b.text_entity.scale *= .5
            b.on_click = self._hacer_compra(al_comprar, obj)
            self.botones.append(b)

        self.btn_seguir = Button(parent=self.raiz, text="Continuar", scale=(.34, .075),
                                 position=(CX, -.36), color=PANEL)
        self.btn_seguir.on_click = al_continuar

    def _hacer_compra(self, al_comprar, obj):
        def _f():
            al_comprar(obj)
        return _f

    def refrescar(self, fragmentos, comprados):
        self.txt_frag.text = f"fragmentos: {fragmentos}"
        for b, obj in zip(self.botones, OBJETOS):
            agotado = obj["id"] in comprados and obj["efecto"] != "curar"
            caro = fragmentos < obj["costo"]
            b.disabled = agotado
            b.text_entity.color = TENUE if (agotado or caro) else CLARO


# ------------------------------------------------------- TRANSICIONES
class PantallaMensaje(Pantalla):
    """Sirve para transiciones, victoria y derrota: mismo layout."""

    def __init__(self, al_continuar):
        super().__init__()
        # Esta pantalla se reutiliza para dos momentos muy distintos, asi que
        # tiene dos fondos y enciende uno u otro en poner(). Se crean los dos
        # aqui para no cargar una imagen en mitad de la partida.
        self.fondos = {
            "transicion": self._poner_fondo("transicion.png"),
            "final": self._poner_fondo("final.png"),
        }
        self.titulo = Text(parent=self.raiz, text="", origin=(0, 0),
                           position=(0, .2), scale=2.0, color=CLARO)
        self.cuerpo = Text(parent=self.raiz, text="", origin=(0, 0),
                           position=(0, .04), scale=1.0, color=TENUE)
        self.btn = Button(parent=self.raiz, text="Continuar", scale=(.3, .075),
                          position=(0, -.2), color=PANEL)
        self.btn.on_click = al_continuar

    def poner(self, titulo, cuerpo, texto_boton="Continuar", fondo="transicion"):
        self.titulo.text = titulo
        self.cuerpo.text = cuerpo
        self.btn.text = texto_boton
        for clave, ent in self.fondos.items():
            if ent is not None:
                ent.enabled = (clave == fondo)
