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
import sonido

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


class Jefe(Entity):

    def __init__(self, definicion, pool, **kwargs):
        super().__init__(**kwargs)
        self.definicion = definicion
        self.nombre = definicion["nombre"]
        self.vida_max = definicion["vida"]
        self.vida = self.vida_max
        self.dano = definicion["dano"]
        self.velocidad = definicion["velocidad"]
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

        self.pool = pool
        self.visual, self.actor = crear_visual(self, definicion["clave"])
        self._color_base = getattr(self.visual, "color", ucolor.white)
        animar(self.actor, "Idle")

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

    def _perseguir(self, dt, hacia, dist):
        if dist > 0.01:
            direccion = hacia / dist
            self.position += direccion * self.velocidad * dt
            # +FRENTE_MODELO para que encare hacia donde avanza. Giro por el
            # camino corto (delta en [-180, 180]) para no dar una vuelta
            # completa al cruzar el limite de +-180 grados.
            objetivo_ang = degrees(atan2(direccion.x, direccion.z)) + FRENTE_MODELO
            delta = (objetivo_ang - self.rotation_y + 180) % 360 - 180
            self.rotation_y += delta * min(1.0, 6 * dt)

        rango = 4.0 if self.patron in ("embestida", "area", "mixto") else 16.0
        if dist < rango or self.temporizador <= 0:
            self._entrar(TELEGRAFIAR, self.t_telegrafiado)

    def _telegrafiar(self, hacia):
        # Se queda quieto y avisa. Aqui es donde el jugador reacciona.
        if self.temporizador <= 0:
            self._preparar_ataque()
            self._entrar(ATACAR, 0.9)

    def _preparar_ataque(self):
        if self.patron == "rafaga":
            self._disparos_pendientes = 3 + self.fase
        elif self.patron in ("parpadeo", "final"):
            self._disparos_pendientes = 2 + self.fase
        else:
            self._disparos_pendientes = 1
        self._cadencia_rafaga = 0.0

    def _atacar(self, dt, jugador, hacia, dist):
        if self.patron in ("embestida", "area", "mixto") and self._disparos_pendientes:
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
