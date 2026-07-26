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

    def _cambiar_anim(self, nombre, en_bucle=True):
        if nombre == self._anim_actual:
            return
        self._anim_actual = nombre
        if nombre is None:
            if self.actor is not None:
                self.actor.stop()
        else:
            animar(self.actor, nombre, en_bucle=en_bucle)

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
            # A partir de la fase 2 (_subir_fase ya subio la velocidad un
            # 15% por fase) el jefe corre en vez de caminar: se nota que
            # viene mas agresivo, no solo en los numeros.
            self._cambiar_anim("Running" if self.velocidad > self.velocidad_base * 1.05 else "Walking")
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
            self._entrar(ATACAR, 0.9)

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
        # 3 golpes espaciados; solo conectan si el jugador sigue cerca (no
        # se embiste como "embestida": el combo es corto y en el sitio).
        self._cadencia_rafaga -= dt
        if self._disparos_pendientes and self._cadencia_rafaga <= 0:
            if dist < 4.5:
                jugador.recibir_dano(self.dano * 0.6)
            self._disparos_pendientes -= 1
            self._cadencia_rafaga = 0.22

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
