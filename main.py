"""
main.py — Punto de entrada y maquina de estados del juego.

Ejecutar con:   python main.py

Decisiones de rendimiento tomadas aqui:

  * Un solo update() global en vez de un update() por entidad. Cada
    update() que Ursina descubre por reflexion tiene coste; centralizarlo
    reduce muchisimo la sobrecarga cuando hay decenas de objetos.
  * Colisiones resueltas con distancia al cuadrado, sin colisionadores
    fisicos y sin raiz cuadrada.
  * Una sola escena que se activa y desactiva por secciones; nunca se
    recarga el nivel completo.
  * Una unica luz direccional, sin sombras salvo en calidad alta.
  * Los modelos se cargan una vez y se reutilizan entre combates.
"""

from ursina import (Ursina, Entity, Vec3, camera, color as ucolor, window,
                    application, time as utime, scene, destroy, mouse)

from config import (Config, MonitorRendimiento, TITULO, VSYNC, MOSTRAR_FPS,
                   TEXTURA_PISO, PISO_TILES, TEXTURA_CIELO)
from entorno import cargar_textura, crear_cielo
from datos import JEFES, GUARDIANES, TRANSICIONES, MODELOS
from recursos import faltantes, crear_visual
from proyectiles import PoolProyectiles
from jugador import Jugador, LIMITE_ARENA, CAM_DIST_MAX
import sonido

# El plano de recorte lejano no debe cortar nunca al jefe ni esconderlo tras la
# cupula del cielo (cuyo radio es 0.9*lejano). Peor caso: jugador y jefe en
# extremos opuestos del arena (2*LIMITE) con la camara alejada al maximo con la
# rueda (CAM_DIST_MAX), mas un margen. Dividimos entre 0.9 para dejar al jefe
# dentro de la cupula incluso con el zoom-out a tope.
ALCANCE_MINIMO = (2 * LIMITE_ARENA + CAM_DIST_MAX + 15) / 0.9
from jefe import Jefe
from interfaz import (HUD, MenuPrincipal, SeleccionGuardian, Tienda,
                     PantallaMensaje, Instrucciones)
from vitrina import Vitrina

# --------------------------------------------------------------- estados
MENU = "menu"
SELECCION = "seleccion"
INSTRUCCIONES = "instrucciones"
COMBATE = "combate"
TIENDA = "tienda"
TRANSICION = "transicion"
FIN = "fin"


class Juego:

    def __init__(self, pbr_pipeline=None):
        # Pipeline PBR de simplepbr (o None si no se inicializo). Lo guardamos
        # para ajustar sus parametros (MSAA, normal maps, luces) al cambiar de
        # preset de calidad sin reiniciar el juego.
        self.pbr_pipeline = pbr_pipeline
        self.estado = MENU
        self.jugador = None
        self.jefe = None
        self.indice_jefe = 0
        self.fragmentos = 0
        self.comprados = set()

        self._construir_escenario()
        self.pool = PoolProyectiles()
        self._construir_ui()

        self.monitor = MonitorRendimiento(al_cambiar=self._calidad_cambio)
        self._aplicar_calidad()
        self._ir_a(MENU)

        # Aviso util durante el desarrollo: que modelos faltan por exportar.
        pendientes = faltantes()
        if pendientes:
            print("[modelos] usando primitivas de respaldo para:", ", ".join(pendientes))

    # ------------------------------------------------------- escenario
    def _construir_escenario(self):
        """Un solo suelo y un anillo. Nada mas: cada malla extra cuesta."""
        # Colores oscuros a proposito: con simplepbr la luz principal ilumina
        # el suelo, asi que partimos de un valor bajo para conservar la
        # atmosfera sombria en vez de un gris lavado.
        # El suelo se extiende mucho mas alla del arena para que el horizonte
        # quede LEJOS. Antes el plano terminaba justo tras el enemigo: su borde
        # cercano hacia de horizonte y cortaba al modelo, y mas alla asomaba la
        # mitad inferior (oscura) del HDRI del cielo. Con un suelo grande, el
        # suelo tapa esa parte baja del cielo y el enemigo queda siempre sobre
        # roca, sin costura visible.
        piso_escala = LIMITE_ARENA * 12
        # Tamano en unidades de mundo de una repeticion de la textura. Lo
        # mantenemos constante para que las piedras midan igual en el suelo y en
        # el disco del arena, sin importar la escala de cada malla.
        tile_mundo = (LIMITE_ARENA * 2.4) / PISO_TILES

        self.suelo = Entity(
            model="plane",
            scale=piso_escala,
            color=ucolor.rgb32(20, 20, 24),
            position=(0, 0, 0),
        )
        # Textura de roca en el suelo. simplepbr ignora texturas sueltas en
        # primitivas, asi que al suelo le damos un shader propio de Ursina.
        tex_piso = cargar_textura(TEXTURA_PISO,
                                  anisotropico=Config.p("anisotropico"),
                                  max_lado=Config.p("tex_suelo_max"))
        if tex_piso is not None:
            from ursina.shaders import unlit_shader
            # Shader unlit: muestra la roca de forma pareja sin depender de la
            # luz tenue del combate (que esta ajustada para los modelos PBR).
            # El tinte la mantiene algo oscura para no romper la atmosfera.
            self.suelo.shader = unlit_shader
            self.suelo.texture = tex_piso
            reps = piso_escala / tile_mundo
            self.suelo.texture_scale = (reps, reps)
            self.suelo.color = ucolor.rgb32(155, 150, 145)

        # Disco del arena. Antes era un gris liso OPACO que tapaba la roca
        # dentro de la zona de combate (la textura solo asomaba fuera). Ahora
        # lleva la misma roca, apenas mas oscura, para que el limite del arena
        # se note de forma sutil pero el suelo se vea texturado por dentro.
        self.borde = Entity(
            model="circle",
            scale=LIMITE_ARENA * 2,
            rotation_x=90,
            position=(0, 0.02, 0),
            color=ucolor.rgb32(120, 116, 110),
        )
        if tex_piso is not None:
            from ursina.shaders import unlit_shader
            self.borde.shader = unlit_shader
            self.borde.texture = tex_piso
            reps_borde = (LIMITE_ARENA * 2) / tile_mundo
            self.borde.texture_scale = (reps_borde, reps_borde)

        # Cielo nocturno (HDRI equirectangular). Si falta el archivo,
        # crear_cielo devuelve None y queda el fondo liso de la ventana.
        self.cielo = crear_cielo(TEXTURA_CIELO)
        if self.cielo is not None:
            # Lo atenuamos para no lavar la atmosfera sombria de la arena.
            self.cielo.color = ucolor.rgb32(120, 120, 135)

        from ursina import DirectionalLight, AmbientLight

        # Luz principal (key light): marca el volumen y, en calidad alta,
        # proyecta las sombras.
        self.luz = DirectionalLight(shadows=False)
        self.luz.look_at(Vec3(1, -1.4, -0.6))

        # Luz ambiental: sube el nivel base de toda la escena para que las
        # caras que no reciben la luz principal no queden en negro puro.
        # Con simplepbr activo, un valor bajo basta: subirlo mas lava el
        # suelo y el fondo y se pierde la atmosfera oscura.
        self.ambiente = AmbientLight(color=ucolor.rgb32(44, 46, 54))

        # Luz de relleno: una direccional tenue desde el lado opuesto a la
        # principal. Suaviza el contraste sin borrar el modelado. No proyecta
        # sombras (seria doble coste y ademas se cancelarian entre si).
        self.relleno = DirectionalLight(shadows=False)
        self.relleno.color = ucolor.rgb32(40, 42, 52)
        self.relleno.look_at(Vec3(-1, -0.8, 0.6))

        self.escenario = [self.suelo, self.borde]
        if self.cielo is not None:
            self.escenario.append(self.cielo)

    def _construir_ui(self):
        self.hud = HUD()
        self.menu = MenuPrincipal(self._pulsar_jugar, application.quit, self._ciclar_calidad)
        self.seleccion = SeleccionGuardian(self._elegir_guardian, self._previsualizar_guardian)
        self.instrucciones = Instrucciones(self._comenzar_combate)
        self.tienda = Tienda(self._comprar, self._salir_tienda)
        self.mensaje = PantallaMensaje(self._continuar_mensaje)
        self.pantallas = (self.hud, self.menu, self.seleccion, self.instrucciones,
                          self.tienda, self.mensaje)

        # Escaparate 3D para la seleccion de guardian y la tienda.
        self.vitrina = Vitrina(position=(0, 0, 0))
        self.guardian_previsualizado = next(iter(GUARDIANES))

    # -------------------------------------------------------- calidad
    def _aplicar_calidad(self):
        self.luz.shadows = Config.p("sombras")
        # Nunca por debajo de ALCANCE_MINIMO: aunque un preset use poca
        # distancia de dibujado por rendimiento, el jefe debe seguir visible
        # (y dentro de la cupula del cielo) por lejos que este el jugador.
        camera.clip_plane_far = max(Config.p("distancia_vista"), ALCANCE_MINIMO)
        self.pool.redimensionar(Config.p("pool_proyectiles"))
        self.menu.set_calidad(Config.calidad)

        # --- Escalado de GPU por preset (lo que de verdad pesa en gama baja) ---
        # Luz de relleno: en 'bajo' se apaga (2 luces en vez de 3). Menos luces
        # = menos trabajo por pixel del shader PBR.
        self.relleno.enabled = Config.p("luz_relleno")

        # Filtrado anisotropico del suelo en vivo (el suelo y el borde comparten
        # la misma textura, asi que una llamada basta).
        from entorno import set_anisotropico
        set_anisotropico(self.suelo, Config.p("anisotropico"))

        # Pipeline PBR: ajusta MSAA, normal/occlusion maps y tope de luces en
        # caliente (simplepbr recompila el shader al asignar estos atributos).
        # Es el mayor ahorro de GPU: MSAA 4 -> 0 y sin normal maps aligeran
        # muchisimo el sombreado de los modelos en graficos integrados.
        if self.pbr_pipeline is not None:
            self.pbr_pipeline.msaa_samples = Config.p("pbr_msaa")
            self.pbr_pipeline.use_normal_maps = Config.p("pbr_normal_maps")
            self.pbr_pipeline.use_occlusion_maps = Config.p("pbr_normal_maps")
            self.pbr_pipeline.use_emission_maps = Config.p("pbr_normal_maps")
            self.pbr_pipeline.max_lights = Config.p("pbr_max_luces")

    def _calidad_cambio(self, nueva):
        print(f"[rendimiento] calidad ajustada automaticamente a '{nueva}'")
        self._aplicar_calidad()

    def _ciclar_calidad(self):
        orden = ["bajo", "medio", "alto"]
        i = (orden.index(Config.calidad) + 1) % len(orden)
        Config.calidad = orden[i]
        Config.auto_calidad = False   # si el usuario elige, respetamos su eleccion
        self._aplicar_calidad()

    # -------------------------------------------------------- estados
    def _ir_a(self, estado):
        self.estado = estado
        sonido.musica_para_estado(estado, self.indice_jefe, len(JEFES))
        for p in self.pantallas:
            p.ocultar()

        mostrar_mundo = estado in (COMBATE,)
        # El raton se bloquea (oculto y centrado) solo en combate, que es
        # cuando controla la camara. En menus y tienda debe estar libre para
        # poder pulsar los botones.
        mouse.locked = mostrar_mundo
        for e in self.escenario:
            e.enabled = mostrar_mundo
        if self.jugador:
            self.jugador.enabled = mostrar_mundo
        if self.jefe:
            self.jefe.enabled = mostrar_mundo

        # Por defecto ocultamos el escaparate; los estados que lo usan lo
        # vuelven a encender abajo.
        self.vitrina.ocultar()

        if estado == MENU:
            self.menu.mostrar()
        elif estado == SELECCION:
            self._enfocar_vitrina(hacia_derecha=1.7, distancia=5.6)
            # mostrar() dispara la previsualizacion, que a su vez coloca el
            # modelo en el escaparate a traves de _previsualizar_guardian.
            self.seleccion.mostrar()
        elif estado == INSTRUCCIONES:
            self.instrucciones.mostrar()
        elif estado == COMBATE:
            self.hud.mostrar()
        elif estado == TIENDA:
            self.vitrina.mostrar("mercader")
            self._enfocar_vitrina(hacia_derecha=-2.0, distancia=6.8)
            self.tienda.refrescar(self.fragmentos, self.comprados)
            self.tienda.mostrar()
        elif estado in (TRANSICION, FIN):
            self.mensaje.mostrar()

    def _enfocar_vitrina(self, hacia_derecha=0.0, distancia=5.6):
        """
        Coloca la camara mirando al escaparate. 'hacia_derecha' (en unidades
        de mundo) desplaza el modelo hacia la derecha de la pantalla; con
        valor negativo lo manda a la izquierda. 'distancia' aleja la camara
        (modelos mas altos necesitan mas para no cortarse). Asi la UI y el
        modelo no se pisan: botones a un lado, modelo al otro.
        """
        objetivo = Vec3(-hacia_derecha, 1.2, 0)
        camera.position = objetivo + Vec3(0, 0.3, -distancia)
        camera.look_at(objetivo)
        camera.fov = 45

    def _pulsar_jugar(self):
        self._ir_a(SELECCION)

    def _previsualizar_guardian(self, clave):
        """Al pasar el raton por un guardian, mostramos su modelo en el escaparate."""
        self.guardian_previsualizado = clave
        if self.estado == SELECCION:
            self.vitrina.mostrar(clave)

    def _elegir_guardian(self, clave):
        if self.jugador:
            destroy(self.jugador)
        self.jugador = Jugador(clave, position=(0, 0, -8))
        self.indice_jefe = 0
        self.fragmentos = 0
        self.comprados.clear()
        # Pantalla intermedia con los controles antes del primer combate.
        self._ir_a(INSTRUCCIONES)

    def _comenzar_combate(self):
        self._iniciar_combate()

    def _iniciar_combate(self):
        definicion = JEFES[self.indice_jefe]
        if self.jefe:
            destroy(self.jefe)
        self.jefe = Jefe(definicion, self.pool, position=(0, 0, 10))
        self.pool.limpiar()
        self.jugador.position = Vec3(0, 0, -10)
        self.jugador.vivo = True
        # Recursos al maximo y jefe fijado (lock-on) al empezar cada combate.
        self.jugador.reponer_recursos()
        self.jugador.fijado = True
        self._ir_a(COMBATE)

    def _terminar_combate(self, victoria):
        self.pool.limpiar()
        if victoria:
            sonido.reproducir_sfx("victoria")
            self.fragmentos += JEFES[self.indice_jefe]["fragmentos"]
            if self.indice_jefe >= len(JEFES) - 1:
                sonido.reproducir_sfx("a_bodoque")
                self.mensaje.poner(
                    "EQUILIBRIO RESTAURADO",
                    "El dispositivo se estabiliza. Nadie tuvo que romperse del todo.",
                    "Volver al menu")
                self._ir_a(FIN)
            else:
                texto = TRANSICIONES[min(self.indice_jefe, len(TRANSICIONES) - 1)]
                self.mensaje.poner("Guardian liberado", texto, "Ir al puesto")
                self._ir_a(TRANSICION)
        else:
            sonido.reproducir_sfx("defeat")
            self.mensaje.poner(
                "HAS CAIDO",
                "La corrupcion sigue avanzando. Vuelve a intentarlo.",
                "Reintentar")
            self._ir_a(FIN)

    def _continuar_mensaje(self):
        if self.estado == TRANSICION:
            self._ir_a(TIENDA)
        else:
            if self.jugador and not self.jugador.vivo:
                # Reintentar el mismo jefe, conservando mejoras.
                self.jugador.vida = self.jugador.vida_max
                self.jugador.vivo = True
                self._iniciar_combate()
            else:
                self._ir_a(MENU)

    # --------------------------------------------------------- tienda
    def _comprar(self, objeto):
        if self.fragmentos < objeto["costo"]:
            return
        if objeto["id"] in self.comprados and objeto["efecto"] != "curar":
            return
        self.fragmentos -= objeto["costo"]
        self.comprados.add(objeto["id"])
        self.jugador.aplicar_objeto(objeto)
        sonido.reproducir_sfx("button")
        self.tienda.refrescar(self.fragmentos, self.comprados)

    def _salir_tienda(self):
        self.indice_jefe += 1
        self.jugador.curar(int(self.jugador.vida_max * 0.5))
        self._iniciar_combate()

    # ---------------------------------------------------------- bucle
    def actualizar(self, dt):
        sonido.actualizar(dt)
        self.monitor.actualizar(dt)

        # El escaparate gira en la seleccion y en la tienda.
        if self.estado in (SELECCION, TIENDA):
            self.vitrina.rotar(dt)

        if self.estado != COMBATE:
            return

        self.jugador.actualizar(dt, self.jefe)
        self.jefe.actualizar(dt, self.jugador)

        self._mover_proyectiles(dt)
        self.hud.actualizar(self.jugador, self.jefe, self.fragmentos)

        if not self.jefe.vivo:
            self._terminar_combate(True)
        elif not self.jugador.vivo:
            self._terminar_combate(False)

    def _mover_proyectiles(self, dt):
        """
        Colision por distancia al cuadrado: sin raiz cuadrada y sin
        colisionadores de Panda3D. Con pocos proyectiles es el metodo
        mas barato que existe.
        """
        jugador = self.jugador
        jefe = self.jefe
        r_jugador = 1.1 ** 2
        r_jefe = (1.6 * jefe.definicion.get("escala", 1.0)) ** 2 + 1.5

        for p in self.pool.activos():
            if not p.avanzar(dt):
                continue

            if abs(p.x) > LIMITE_ARENA + 6 or abs(p.z) > LIMITE_ARENA + 6:
                p.disable()
                continue

            if p.de_jugador:
                dx = p.x - jefe.x
                dz = p.z - jefe.z
                if dx * dx + dz * dz < r_jefe:
                    jefe.recibir_dano(p.dano)
                    p.disable()
            else:
                dx = p.x - jugador.x
                dz = p.z - jugador.z
                if dx * dx + dz * dz < r_jugador:
                    jugador.recibir_dano(p.dano)
                    p.disable()

    def tecla(self, key):
        if self.estado == SELECCION:
            if key in ("up arrow", "left arrow"):
                self.seleccion.mover(-1)
            elif key in ("down arrow", "right arrow"):
                self.seleccion.mover(1)
            elif key in ("enter", "space"):
                self.seleccion.confirmar()
            elif key == "escape":
                self._ir_a(MENU)
            return

        if self.estado == INSTRUCCIONES:
            if key in ("enter", "space"):
                self._comenzar_combate()
            elif key == "escape":
                self._ir_a(SELECCION)
            return

        if self.estado == COMBATE:
            if key == "escape":
                self._ir_a(MENU)
            elif key == "scroll up" and self.jugador:
                self.jugador.zoom_camara(-1)     # acercar
            elif key == "scroll down" and self.jugador:
                self.jugador.zoom_camara(1)      # alejar
            else:
                self._entrada_combate(key)
            return

        if key == "escape" and self.estado == MENU:
            application.quit()

    def _entrada_combate(self, key):
        """Controles de combate estilo Souls."""
        j = self.jugador
        if j is None or not j.vivo:
            return
        if key == "left mouse down":
            j.atacar(pesado=False)          # ataque ligero
        elif key == "right mouse down":
            j.atacar(pesado=True)           # ataque pesado
        elif key == "space":
            j.esquivar()                    # rodar (i-frames)
        elif key == "q":
            j.lanzar_hechizo(self.pool, self.jefe, MODELOS[j.clave]["color"])
        elif key == "e":
            j.cambiar_hechizo(1)            # cambiar de hechizo
        elif key == "r":
            j.curar_frasco()                # beber frasco
        elif key == "f":
            j.alternar_fijado(self.jefe)    # fijar / soltar objetivo
        elif key in ("1", "2", "3"):
            j.elegir_arma(int(key) - 1)     # cambiar de arma


# ------------------------------------------------------------ arranque
if __name__ == "__main__":
    app = Ursina(
        title=TITULO,
        borderless=False,
        vsync=VSYNC,
        development_mode=False,   # desactiva recargas en caliente: mas rapido
    )
    window.fps_counter.enabled = MOSTRAR_FPS
    window.exit_button.visible = False
    window.color = ucolor.rgb32(30, 30, 34)

    # Pipeline PBR: sin esto los .glb (que usan materiales metal/rugosidad y
    # texturas) se dibujan planos y blancos. simplepbr aplica su iluminacion
    # correcta. Si no estuviera instalado, seguimos sin el (modelos planos)
    # en vez de tumbar el juego.
    #
    # Se inicializa con los parametros del preset inicial (MSAA, normal maps,
    # tope de luces). El nivel PBR se ajusta luego en vivo desde
    # _aplicar_calidad; lo que NO se puede cambiar en caliente es iniciarlo o
    # no, por eso ese interruptor (pbr=False) es una decision de arranque.
    pbr_pipeline = None
    try:
        import simplepbr
        if Config.p("pbr"):
            pbr_pipeline = simplepbr.init(
                msaa_samples=Config.p("pbr_msaa"),
                use_normal_maps=Config.p("pbr_normal_maps"),
                use_occlusion_maps=Config.p("pbr_normal_maps"),
                use_emission_maps=Config.p("pbr_normal_maps"),
                max_lights=Config.p("pbr_max_luces"),
            )
    except Exception as e:
        print(f"[render] simplepbr no disponible ({e}); modelos sin PBR")

    juego = Juego(pbr_pipeline=pbr_pipeline)

    def update():
        juego.actualizar(utime.dt)

    def input(key):
        juego.tecla(key)

    app.run()
