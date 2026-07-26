"""
movimientos_personaje.py — Animaciones y golpe de los personajes.

Calcado de la clase Guardian en "Guardian Naturaleza.py" (la prueba original
en Prueba1, donde el movimiento y el golpe ya estaban resueltos y probados):
mismo brazo derecho controlado a mano para sostener el arma, mismo golpe con
anticipo/impacto/recuperacion, mismos nombres de animacion (Walking/Running).
Se generaliza para que sirva para los 6 guardianes (sol, fuego, hielo,
naturaleza, vacio, luna) y sus jefes, no solo para el de naturaleza.

Que hace y que NO hace:
  * SI decide que animacion mostrar (Walking/Running al moverse, quieto si
    no) y anima el brazo derecho a mano para el golpe cuerpo a cuerpo.
  * NO lee teclado ni raton, NO mueve al personaje por el mundo, NO toca
    estamina/vida/camara. Eso lo sigue manejando jugador.py (y jefe.py),
    que son los "controles" de Guardianes del Eclipse: ese codigo se deja
    tal cual. Este modulo solo decide como SE VE el personaje, no que HACE.

Uso (ver jugador.py):
    self.movimiento = MovimientoPersonaje(self.actor)
    self.movimiento.equipar_arma("martillo")
    ...
    self.movimiento.atacar()
    ...
    def actualizar(self, dt):
        self.movimiento.actualizar(dt, moviendo=self.moving, corriendo=self.running)
"""

from ursina import Entity, lerp, application
from panda3d.core import Filename
from config import MODELOS as DIR_MODELOS

# Armas sueltas (no forman parte del rig de ningun personaje: se cuelgan
# aparte de RightHand con equipar_arma). Cada una trae su propio pivote de
# modelado, asi que ademas de la ruta cada entrada calibra a mano su
# posicion/rotacion/escala en la mano (ver equipar_arma). El punto de
# partida (posicion, rotacion) es el que ya traia Guardian Naturaleza.py
# para el martillo; espada y hacha se ajustaron desde ahi.
ARMAS_GLB = {
    "espada":   dict(archivo=DIR_MODELOS / "armas" / "espada.glb",
                      pos=(0, 0, 0), rot=(80, 0, 0), escala=9),
    "martillo": dict(archivo=DIR_MODELOS / "armas" / "martillo.glb",
                      pos=(0, 0, 0), rot=(80, 0, 0), escala=9),
    "hacha":    dict(archivo=DIR_MODELOS / "armas" / "hacha.glb",
                      pos=(0, 0, 0), rot=(80, 0, 0), escala=9),
}

# ---- lo de aqui abajo es literalmente lo que ya habia en
# ---- Guardian Naturaleza.py, solo que ahora vive en una clase reutilizable
# ---- en vez de estar clavado en el Entity Guardian de un solo personaje.

RIGHT_ARM_REST = (-10, 10, 70)
RIGHT_FOREARM_REST = (0, 0, 15)
RIGHT_HAND_REST = (0, 0, 0)

ATTACK_WINDUP = 0.15
ATTACK_STRIKE = 0.12
ATTACK_RECOVER = 0.25


def _ruta_panda(ruta):
    """Ruta de sistema (con espacios/acentos) al formato que acepta Panda3D."""
    return Filename.from_os_specific(str(ruta)).get_fullpath()


class MovimientoPersonaje:
    """Walking/Running + golpe de brazo derecho, para un Actor biped.

    Si 'actor' es None (personaje sin .glb todavia, mostrando su primitiva
    de respaldo) o no tiene los huesos esperados, queda 'disponible=False' y
    todos sus metodos son no-ops: nunca rompe al llamador, igual que el
    resto de recursos.py.
    """

    def __init__(self, actor):
        self.actor = actor
        self.disponible = actor is not None and hasattr(actor, "controlJoint")

        self.moving = False
        self.running = False
        self.attacking = False
        self.attack_timer = 0.0
        self.arma = None

        if not self.disponible:
            return

        try:
            self.j_right_arm, self.pos_right_arm = self._control_joint("RightArm")
            self.j_right_forearm, self.pos_right_forearm = self._control_joint("RightForeArm")
            self.j_right_hand, self.pos_right_hand = self._control_joint("RightHand")
            self.hand = actor.exposeJoint(None, "modelRoot", "RightHand")
        except Exception:
            # Rig sin esos huesos (modelo no biped o mal exportado): se
            # desactiva en vez de tumbar la partida, igual que recursos.py.
            self.disponible = False
            return

        self.right_arm_hpr = list(RIGHT_ARM_REST)
        self.right_forearm_hpr = list(RIGHT_FOREARM_REST)
        self.right_hand_hpr = list(RIGHT_HAND_REST)
        self._apply_right_arm()

    def _control_joint(self, joint_name):
        node = self.actor.controlJoint(None, "modelRoot", joint_name)
        return node, node.getPos()

    def _apply_right_arm(self):
        self.j_right_arm.setPos(self.pos_right_arm)
        self.j_right_arm.setHpr(*self.right_arm_hpr)
        self.j_right_forearm.setPos(self.pos_right_forearm)
        self.j_right_forearm.setHpr(*self.right_forearm_hpr)
        self.j_right_hand.setPos(self.pos_right_hand)
        self.j_right_hand.setHpr(*self.right_hand_hpr)

    # ------------------------------------------------------------- arma
    def equipar_arma(self, clave_arma):
        """Cuelga en la mano derecha el arma registrada en ARMAS_GLB (por
        clave: 'espada'/'martillo'/'hacha'). Sin llamarlo, el golpe es a
        mano limpia.

        Se carga con el loader de Panda (application.base.loader), no con
        Entity(model='ruta'): ese segundo camino busca el nombre como un
        archivo DENTRO de application.asset_folder (ver Entity.model_setter
        en ursina/entity.py) y con una ruta absoluta fuera de esa carpeta
        simplemente no lo encuentra.
        """
        datos_arma = ARMAS_GLB.get(clave_arma)
        if not self.disponible or not datos_arma:
            return
        self.quitar_arma()
        nodo = application.base.loader.loadModel(_ruta_panda(datos_arma["archivo"]))
        self.arma = Entity(model=nodo, parent=self.hand)
        self.arma.position = datos_arma["pos"]
        self.arma.rotation = datos_arma["rot"]
        self.arma.world_scale = datos_arma["escala"]

    def quitar_arma(self):
        if self.arma is not None:
            self.arma.disable()
            self.arma = None

    # ---------------------------------------------------------- el golpe
    def atacar(self):
        """Dispara el gesto si el brazo esta libre. No hace nada si ya esta golpeando."""
        if not self.disponible or self.attacking:
            return
        self.attacking = True
        self.attack_timer = 0.0

    def _animar_ataque(self, dt):
        self.attack_timer += dt
        t = self.attack_timer
        base_h, base_p, base_r = RIGHT_ARM_REST
        base_fr = RIGHT_FOREARM_REST[2]

        if t < ATTACK_WINDUP:
            p = t / ATTACK_WINDUP
            self.right_arm_hpr = [base_h, base_p, lerp(base_r, base_r - 20, p)]
            self.right_forearm_hpr = [0, 0, lerp(base_fr, base_fr - 30, p)]

        elif t < ATTACK_WINDUP + ATTACK_STRIKE:
            p = (t - ATTACK_WINDUP) / ATTACK_STRIKE
            self.right_arm_hpr = [base_h, base_p, lerp(base_r - 20, base_r + 60, p)]
            self.right_forearm_hpr = [0, 0, lerp(base_fr - 30, base_fr + 20, p)]

        elif t < ATTACK_WINDUP + ATTACK_STRIKE + ATTACK_RECOVER:
            p = (t - ATTACK_WINDUP - ATTACK_STRIKE) / ATTACK_RECOVER
            self.right_arm_hpr = [base_h, base_p, lerp(base_r + 60, base_r, p)]
            self.right_forearm_hpr = [0, 0, lerp(base_fr + 20, base_fr, p)]

        else:
            self.attacking = False
            self.right_arm_hpr = list(RIGHT_ARM_REST)
            self.right_forearm_hpr = list(RIGHT_FOREARM_REST)
            self.right_hand_hpr = list(RIGHT_HAND_REST)

        self._apply_right_arm()

    # ------------------------------------------------------- por frame
    def actualizar(self, dt, moviendo, corriendo):
        """Llamar una vez por frame desde jugador.py / jefe.py."""
        if not self.disponible:
            return

        was_moving = self.moving
        was_running = self.running
        self.moving = moviendo
        self.running = corriendo and moviendo

        if self.moving:
            anim_name = "Running" if self.running else "Walking"
            if not was_moving or (self.running != was_running):
                self.actor.loop(anim_name)
        else:
            if was_moving:
                self.actor.stop()

        if self.attacking:
            self._animar_ataque(dt)
        else:
            self.right_arm_hpr = list(RIGHT_ARM_REST)
            self.right_forearm_hpr = list(RIGHT_FOREARM_REST)
            self.right_hand_hpr = list(RIGHT_HAND_REST)
            self._apply_right_arm()