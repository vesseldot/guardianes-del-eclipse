"""
fantasma.py — Enemigo invocado: poca vida, persigue y muerde de cerca.

Lo invoca el conejo (patron "final" en jefe.py, ver Jefe._atacar_final). A
diferencia de Jefe, no tiene fases ni hechizos: solo tres estados propios
(perseguir / telegrafiar / recuperar) igual de explicitos que los de jefe.py
pero mucho mas simples, porque un fantasma no es un jefe, es un enjambre.
"""

from ursina import Entity, Vec3
from math import atan2, degrees
from recursos import crear_visual, animar

# Mismo motivo que en jefe.py: el .glb mira hacia -z al exportarse.
FRENTE_MODELO = 180.0

VIDA = 18
DANO = 6
VELOCIDAD = 3.6

# El modelo trae 'Running' y 'Walking'. Los fantasmas van a por el jugador en
# enjambre, asi que corren. El ritmo se ajusta a su velocidad real con la misma
# referencia que usa jefe.py, para que la zancada no patine.
ANIM_CORRER = "Running"
VEL_REF_CORRER = 5.2
RITMO_CORRER = min(1.6, max(0.75, VELOCIDAD / VEL_REF_CORRER))
RANGO_GOLPE = 1.7
TELEGRAFIADO = 0.3
RECUPERACION = 0.45

PERSEGUIR = 0
TELEGRAFIAR = 1
RECUPERAR = 2


class Fantasma(Entity):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.vida_max = VIDA
        self.vida = VIDA
        self.dano = DANO
        self.velocidad = VELOCIDAD
        self.vivo = True

        self.estado = PERSEGUIR
        self.temporizador = 0.0
        self._anim_actual = None

        self.visual, self.actor = crear_visual(self, "fantasma")

    @property
    def vida_pct(self):
        return self.vida / self.vida_max if self.vida_max else 0

    def recibir_dano(self, cantidad):
        if not self.vivo:
            return
        self.vida -= cantidad
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False
            self._cambiar_anim(None)

    def _cambiar_anim(self, nombre, en_bucle=True, ritmo=1.0):
        if nombre == self._anim_actual:
            return
        self._anim_actual = nombre
        if nombre is None:
            if self.actor is not None:
                self.actor.stop()
            return
        if self.actor is not None:
            # El ritmo se fija antes de arrancar: cambiarlo con el clip en
            # marcha lo reinicia y se ve un salto.
            try:
                self.actor.setPlayRate(ritmo, nombre)
            except Exception:
                pass
        animar(self.actor, nombre, en_bucle=en_bucle)

    def actualizar(self, dt, jugador):
        if not self.vivo or jugador is None or not jugador.vivo:
            return

        hacia = Vec3(jugador.x - self.x, 0, jugador.z - self.z)
        dist = hacia.length()

        if self.estado == PERSEGUIR:
            if dist > RANGO_GOLPE:
                if dist > 0.01:
                    direccion = hacia / dist
                    self.position += direccion * self.velocidad * dt
                    objetivo_ang = degrees(atan2(direccion.x, direccion.z)) + FRENTE_MODELO
                    delta = (objetivo_ang - self.rotation_y + 180) % 360 - 180
                    self.rotation_y += delta * min(1.0, 8 * dt)
                self._cambiar_anim(ANIM_CORRER, ritmo=RITMO_CORRER)
            else:
                self.estado = TELEGRAFIAR
                self.temporizador = TELEGRAFIADO
                self._cambiar_anim("Attack", en_bucle=False)

        elif self.estado == TELEGRAFIAR:
            self.temporizador -= dt
            if self.temporizador <= 0:
                if dist <= RANGO_GOLPE + 0.6:
                    jugador.recibir_dano(self.dano)
                self.estado = RECUPERAR
                self.temporizador = RECUPERACION

        elif self.estado == RECUPERAR:
            self.temporizador -= dt
            if self.temporizador <= 0:
                self.estado = PERSEGUIR
                self._cambiar_anim(None)
