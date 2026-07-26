"""
jefe.py — Guardianes corrompidos y jefe final.

Maquina de estados minima y explicita:

    PERSEGUIR -> TELEGRAFIAR -> ATACAR -> RECUPERAR -> PERSEGUIR

El telegrafiado es lo que hace legible el combate: el jefe cambia de color
y se detiene antes de golpear, dando al jugador la ventana para esquivar.
"""

from ursina import Entity, Vec3, color as ucolor
from math import radians, sin, cos, atan2, degrees
from recursos import crear_visual, animar
from jugador import LIMITE_ARENA
import sonido
import random

PERSEGUIR = 0
TELEGRAFIAR = 1
ATACAR = 2
RECUPERAR = 3

COLOR_AVISO = ucolor.rgb32(235, 120, 110)

# Los .glb estan exportados mirando hacia -z, asi que hay que girarlos 180
# grados para que "adelante" sea la direccion en la que avanzan (mismo motivo
# y mismo valor que FRENTE_MODELO en jugador.py). Sin esto el jefe caminaba
# de espaldas al acercarse al jugador.
FRENTE_MODELO = 180.0

# --- Sincronizacion entre animacion y desplazamiento real -------------------
# Los clips vienen con una cadencia fija (Walking dura 1.03 s y Running 0.63 s),
# asi que si se reproducen a velocidad 1.0 mientras el jefe avanza despacio los
# pies "patinan": se ve la zancada de una carrera avanzando como al caminar.
#
# VEL_REF_* es la velocidad de suelo a la que cada clip se ve natural sin
# alterar su ritmo. A partir de ahi:
#   * se elige el clip cuya referencia queda mas cerca de la velocidad actual
#     (el corte esta en la media geometrica de las dos referencias), y
#   * se ajusta el ritmo de reproduccion (play rate) proporcionalmente, para
#     que la zancada acompanie al avance real.
# Son valores a ojo (dependen de la longitud del paso de cada modelo): si
# alguna carrera sigue patinando, subir VEL_REF_CORRER; si se ve acelerada,
# bajarlo.
VEL_REF_CAMINAR = 1.9
VEL_REF_CORRER = 5.2
# Tope del ajuste: fuera de esta banda el clip se ve a camara lenta o acelerado.
PLAYRATE_MIN = 0.75
PLAYRATE_MAX = 1.60


class Jefe(Entity):

    def __init__(self, definicion, pool, **kwargs):
        super().__init__(**kwargs)
        self.definicion = definicion
        self.nombre = definicion["nombre"]
        self.vida_max = definicion["vida"]
        self.vida = self.vida_max
        self.dano = definicion["dano"]
        self.velocidad = definicion["velocidad"]
        self.velocidad_base = definicion["velocidad"]  # para saber si ya viene mas rapido por fase
        self.t_telegrafiado = definicion["telegrafiado"]
        self.t_recuperacion = definicion["recuperacion"]
        self.total_fases = definicion["fases"]
        self.patron = definicion["patron"]

        self.fase = 1
        self.estado = PERSEGUIR
        self.temporizador = 1.2
        self.vivo = True
        self._disparos_pendientes = 0
        self._cadencia_rafaga = 0.0
        self._tercio_vida_sonido = min(2, int(self.vida_pct * 3))

        # Solo lo usa el patron "final" (el conejo): alterna entre golpe
        # cuerpo a cuerpo y hechizo. Ver _preparar_ataque / _atacar_final.
        # Los fantasmas ya no salen de un ataque: aparecen todos juntos al
        # empezar el combate (ver Juego._iniciar_combate).
        self._sub_patron_final = None
        self._ataques_final = 0
        self._cadencia_combo = 0.22   # lo recalcula _preparar_ataque_final

        self.pool = pool
        self.visual, self.actor = crear_visual(self, definicion["clave"])
        self._color_base = getattr(self.visual, "color", ucolor.white)
        self._anim_actual = None

    # ------------------------------------------------------------- vida
    @property
    def vida_pct(self):
        return self.vida / self.vida_max if self.vida_max else 0

    def recibir_dano(self, cantidad):
        if not self.vivo:
            return
        self.vida -= cantidad
        tercio_vida = max(0, min(2, int(self.vida_pct * 3)))
        if self.definicion["clave"] == "conejo" and tercio_vida < self._tercio_vida_sonido:
            sonido.reproducir_sfx("muere_bodoque")
        self._tercio_vida_sonido = tercio_vida

        # Cambio de fase: mas rapido y mas agresivo en cada tramo.
        fase_esperada = self.total_fases - int(self.vida_pct * self.total_fases)
        fase_esperada = max(1, min(self.total_fases, fase_esperada + 1))
        if fase_esperada > self.fase:
            self._subir_fase(fase_esperada)

        if self.vida <= 0:
            self.vida = 0
            self.vivo = False

    def _subir_fase(self, nueva):
        self.fase = nueva
        self.velocidad *= 1.15
        self.t_telegrafiado = max(0.35, self.t_telegrafiado * 0.88)
        self.t_recuperacion = max(0.4, self.t_recuperacion * 0.9)
        self.estado = RECUPERAR
        self.temporizador = 0.8      # pausa breve al cambiar de fase

    # ------------------------------------------------------------ logica
    def actualizar(self, dt, jugador):
        if not self.vivo or jugador is None or not jugador.vivo:
            return

        self.temporizador -= dt
        hacia = Vec3(jugador.x - self.x, 0, jugador.z - self.z)
        dist = hacia.length()

        if self.estado == PERSEGUIR:
            self._perseguir(dt, hacia, dist)
        elif self.estado == TELEGRAFIAR:
            self._telegrafiar(hacia)
        elif self.estado == ATACAR:
            self._atacar(dt, jugador, hacia, dist)
        elif self.estado == RECUPERAR:
            if self.temporizador <= 0:
                self._entrar(PERSEGUIR, 0.4)

    def _entrar(self, estado, duracion):
        self.estado = estado
        self.temporizador = duracion
        if hasattr(self.visual, "color"):
            self.visual.color = COLOR_AVISO if estado == TELEGRAFIAR else self._color_base
        if estado == ATACAR:
            # Solo los patrones con el clip propio lo muestran; si el
            # modelo no lo trae, animar() no hace nada (ver recursos.py).
            self._cambiar_anim(self._anim_ataque(), en_bucle=False)
        elif estado != PERSEGUIR:
            self._cambiar_anim(None)

    def _anim_ataque(self):
        """Nombre del clip de ataque. El conejo usa su propio combo cuerpo
        a cuerpo (ver datos exportados)."""
        if self.patron == "final":
            return "Weapon_Combo"
        return "Attack"

    def _cambiar_anim(self, nombre, en_bucle=True, ritmo=1.0):
        if nombre == self._anim_actual:
            return
        self._anim_actual = nombre
        if nombre is None:
            if self.actor is not None:
                self.actor.stop()
            return
        if self.actor is not None:
            # El ritmo se fija ANTES de arrancar el clip: si se cambia con la
            # animacion ya en marcha, Panda la reinicia y se ve un salto.
            try:
                self.actor.setPlayRate(ritmo, nombre)
            except Exception:
                pass
        animar(self.actor, nombre, en_bucle=en_bucle)

    def _anim_desplazamiento(self):
        """Clip de avance y su ritmo, acordes a la velocidad real del jefe.

        Devuelve (nombre, ritmo). Ver VEL_REF_* arriba: se elige el clip cuya
        velocidad de referencia queda mas cerca de la actual y se ajusta el
        ritmo para que la zancada no patine.
        """
        v = max(0.01, self.velocidad)
        # Solo corre cuando la carrera puede reproducirse a un ritmo dentro de
        # la banda permitida. Por debajo de ese punto el clip de correr habria
        # que frenarlo hasta el tope (camara lenta, se ve peor que un paso
        # rapido), asi que se camina acelerando la zancada.
        corte = VEL_REF_CORRER * PLAYRATE_MIN
        if v >= corte:
            nombre, referencia = "Running", VEL_REF_CORRER
        else:
            nombre, referencia = "Walking", VEL_REF_CAMINAR
        ritmo = min(PLAYRATE_MAX, max(PLAYRATE_MIN, v / referencia))
        return nombre, ritmo

    def _duracion_anim(self, nombre, respaldo):
        """Duracion real del clip, o 'respaldo' si el modelo no lo trae.

        Se usa para que el estado ATACAR dure lo que dura la animacion: con el
        valor fijo de 0.9 s que habia antes, el clip de ataque (2.80 s) y el
        combo del conejo (3.70 s) se cortaban a un tercio, y el golpe se veia
        interrumpido antes de que el arma llegara al suelo.
        """
        if self.actor is None:
            return respaldo
        try:
            d = self.actor.getDuration(nombre)
        except Exception:
            return respaldo
        return d if d and d > 0 else respaldo

    def _limitar_arena(self):
        """Mismo tope que jugador.py: sin esto, al perseguir el jefe se
        puede salir del area de combate (jugador.py si se clampeaba, el
        jefe nunca lo hizo)."""
        plano = Vec3(self.x, 0, self.z)
        if plano.length() > LIMITE_ARENA:
            plano = plano.normalized() * LIMITE_ARENA
            self.x, self.z = plano.x, plano.z

    def _perseguir(self, dt, hacia, dist):
        if dist > 0.01:
            direccion = hacia / dist
            self.position += direccion * self.velocidad * dt
            self._limitar_arena()
            # +FRENTE_MODELO para que encare hacia donde avanza. Giro por el
            # camino corto (delta en [-180, 180]) para no dar una vuelta
            # completa al cruzar el limite de +-180 grados.
            objetivo_ang = degrees(atan2(direccion.x, direccion.z)) + FRENTE_MODELO
            delta = (objetivo_ang - self.rotation_y + 180) % 360 - 180
            self.rotation_y += delta * min(1.0, 6 * dt)
            # El clip (caminar/correr) y su ritmo salen de la velocidad REAL,
            # no de la fase: asi la zancada acompana al avance en vez de
            # patinar. Al subir de fase la velocidad crece un 15%, asi que los
            # jefes rapidos pasan a correr solos, y los lentos siguen
            # caminando (pero mas rapido) porque es lo que se ve coherente.
            nombre, ritmo = self._anim_desplazamiento()
            self._cambiar_anim(nombre, ritmo=ritmo)
        else:
            self._cambiar_anim(None)

        cuerpo_a_cuerpo = self.patron in ("embestida", "area", "mixto", "final")
        rango = 4.0 if cuerpo_a_cuerpo else 16.0
        # Los patrones cuerpo a cuerpo solo conectan el golpe si de verdad
        # esta cerca (ver _atacar: 'dist < 5.0'). Cortar la persecucion por
        # tiempo, igual que con los patrones a distancia, lo dejaba
        # telegrafiando y atacando al aire desde lejos una y otra vez sin
        # llegar nunca a alcanzar al jugador -- con un temporizador de
        # persecucion tan corto (1.2s la primera vez, 0.4s despues) contra
        # una velocidad de jefe baja y un arena grande, la distancia nunca
        # alcanzaba a bajar de 'rango' antes de que el tiempo lo cortara.
        if dist < rango or (not cuerpo_a_cuerpo and self.temporizador <= 0):
            self._entrar(TELEGRAFIAR, self.t_telegrafiado)

    def _telegrafiar(self, hacia):
        # Se queda quieto y avisa. Aqui es donde el jugador reacciona.
        if self.temporizador <= 0:
            self._preparar_ataque()
            # El estado dura lo que dura el clip, para que el golpe se vea
            # completo (antes: 0.9 s fijos y la animacion se cortaba).
            self._entrar(ATACAR, self._duracion_anim(self._anim_ataque(), 0.9))

    def _preparar_ataque(self):
        if self.patron == "final":
            self._preparar_ataque_final()
        elif self.patron == "rafaga":
            self._disparos_pendientes = 3 + self.fase
        elif self.patron == "parpadeo":
            self._disparos_pendientes = 2 + self.fase
        else:
            self._disparos_pendientes = 1
        self._cadencia_rafaga = 0.0

    def _preparar_ataque_final(self):
        """El conejo: solo golpe cuerpo a cuerpo (Weapon_Combo)."""
        self._ataques_final += 1
        self._sub_patron_final = "combo"
        self._disparos_pendientes = 3
        # Los 3 golpes se reparten a lo largo del clip. Antes iban fijos a
        # 0.22 s, asi que con el combo de 3.70 s los tres caian en el primer
        # medio segundo y el resto de la animacion no golpeaba nada.
        duracion = self._duracion_anim("Weapon_Combo", 0.9)
        self._cadencia_combo = duracion / (self._disparos_pendientes + 1)

    def _atacar(self, dt, jugador, hacia, dist):
        if self.patron == "final":
            self._atacar_final(dt, jugador, hacia, dist)
        elif self.patron in ("embestida", "area", "mixto") and self._disparos_pendientes:
            # Golpe de area: dano si el jugador sigue cerca al conectar.
            if self.temporizador <= 0.5:
                if dist < 5.0:
                    jugador.recibir_dano(self.dano)
                self._disparos_pendientes = 0
        else:
            self._cadencia_rafaga -= dt
            if self._disparos_pendientes and self._cadencia_rafaga <= 0:
                self._lanzar_hechizo(hacia, dist)
                self._disparos_pendientes -= 1
                self._cadencia_rafaga = 0.18

        if self.temporizador <= 0:
            self._entrar(RECUPERAR, self.t_recuperacion)

    def _atacar_final(self, dt, jugador, hacia, dist):
        # 3 golpes repartidos a lo largo del combo; solo conectan si el jugador
        # sigue cerca (no se embiste como "embestida": el combo es en el sitio).
        self._cadencia_rafaga -= dt
        if self._disparos_pendientes and self._cadencia_rafaga <= 0:
            if dist < 4.5:
                jugador.recibir_dano(self.dano * 0.6)
            self._disparos_pendientes -= 1
            self._cadencia_rafaga = self._cadencia_combo

    def _lanzar_hechizo(self, hacia, dist):
        p = self.pool.pedir()
        if p is None:
            return
        direccion = hacia / dist if dist > 0.01 else Vec3(0, 0, 1)
        p.lanzar(
            origen=self.world_position + Vec3(0, 1.4, 0),
            direccion=direccion,
            dano=self.dano,
            de_jugador=False,
            col=COLOR_AVISO,
            velocidad=14.0,
        )
        sonido.reproducir_sfx("enemy_attack")
