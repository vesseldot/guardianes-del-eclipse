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
from config import MODELOS as DIR_MODELOS, Config
from entorno import reducir_texturas

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

# Reparto del gesto de golpe: anticipo (levanta), impacto (baja) y recuperacion
# (vuelve al reposo). Son PROPORCIONES: atacar(duracion) las reescala para que
# el gesto dure exactamente lo que el arma bloquea al personaje, en vez de los
# 0.52 s fijos de antes -- con el martillo (1.22 s de bloqueo) el brazo ya
# habia vuelto al reposo mucho antes de poder soltar el arma, y el golpe se
# veia cortado a media bajada.
ATTACK_WINDUP = 0.15
ATTACK_STRIKE = 0.12
ATTACK_RECOVER = 0.25
ATTACK_TOTAL = ATTACK_WINDUP + ATTACK_STRIKE + ATTACK_RECOVER

# Amplitud del arco, en grados sobre el eje de giro del brazo. El impacto baja
# hasta ARCO_IMPACTO desde el reposo: con los +60 que habia antes el arma se
# quedaba a media altura y no llegaba a bajar del todo. Subir este valor baja
# mas el arma; bajarlo la deja mas arriba.
ARCO_ANTICIPO = -28.0     # cuanto se levanta antes de golpear
ARCO_IMPACTO = 115.0      # cuanto baja en el golpe
ARCO_ANTEBRAZO_ANT = -35.0
ARCO_ANTEBRAZO_IMP = 45.0


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
        self._escala_ataque = 1.0     # lo fija atacar(duracion)
        self.arma = None
        # clave -> Entity ya cargada y colgada de la mano (ver precargar_armas).
        self._cache_armas = {}

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
    def _crear_arma(self, clave_arma):
        """Carga el .glb del arma y lo cuelga (desactivado) de la mano.

        Se carga con el loader de Panda (application.base.loader), no con
        Entity(model='ruta'): ese segundo camino busca el nombre como un
        archivo DENTRO de application.asset_folder (ver Entity.model_setter
        en ursina/entity.py) y con una ruta absoluta fuera de esa carpeta
        simplemente no lo encuentra.
        """
        datos_arma = ARMAS_GLB[clave_arma]
        nodo = application.base.loader.loadModel(_ruta_panda(datos_arma["archivo"]))
        # Las armas tambien traen texturas de 8K (espada.glb son ~511 MB de
        # VRAM sin reducir). Igual que en recursos.crear_visual.
        reducir_texturas(nodo, Config.p("tex_modelo_max"))
        e = Entity(model=nodo, parent=self.hand, enabled=False)
        e.position = datos_arma["pos"]
        e.rotation = datos_arma["rot"]
        e.world_scale = datos_arma["escala"]
        self._cache_armas[clave_arma] = e
        return e

    def precargar_armas(self, claves=None):
        """Carga de golpe todas las armas y las deja listas y ocultas.

        Se llama al crear el personaje: sin esto, la PRIMERA vez que se cambia
        a un arma habia un tiron perceptible en pleno combate, porque en ese
        momento se leia su .glb (45-57 MB) y se reescalaban sus texturas de 8K.
        Precargando, ese coste se paga una sola vez al entrar al combate y los
        cambios de arma pasan a ser instantaneos.
        """
        if not self.disponible:
            return
        for clave in (claves if claves is not None else ARMAS_GLB):
            if clave in ARMAS_GLB and clave not in self._cache_armas:
                try:
                    self._crear_arma(clave)
                except Exception as e:
                    print(f"[movimientos] no se pudo precargar el arma {clave}: {e}")

    def equipar_arma(self, clave_arma):
        """Muestra en la mano derecha el arma registrada en ARMAS_GLB (por
        clave: 'espada'/'martillo'/'hacha'). Sin llamarlo, el golpe es a
        mano limpia.

        Las armas se reutilizan desde la cache: cambiar de arma solo apaga una
        entidad y enciende otra, sin tocar el disco.
        """
        if not self.disponible or clave_arma not in ARMAS_GLB:
            return
        self.quitar_arma()
        e = self._cache_armas.get(clave_arma)
        if e is None:
            try:
                e = self._crear_arma(clave_arma)
            except Exception as err:
                print(f"[movimientos] no se pudo cargar el arma {clave_arma}: {err}")
                return
        e.enabled = True
        self.arma = e

    def quitar_arma(self):
        """Oculta el arma en mano. No la destruye: queda en cache para volver
        a equiparla sin recargarla."""
        if self.arma is not None:
            self.arma.enabled = False
            self.arma = None

    # ---------------------------------------------------------- el golpe
    def atacar(self, duracion=None):
        """Dispara el gesto si el brazo esta libre. No hace nada si ya esta golpeando.

        'duracion' (segundos) estira o comprime el gesto completo para que
        coincida con el tiempo que el arma deja bloqueado al personaje: el
        martillo golpea despacio y las dagas rapido, con el mismo arco.
        """
        if not self.disponible or self.attacking:
            return
        self.attacking = True
        self.attack_timer = 0.0
        self._escala_ataque = (duracion / ATTACK_TOTAL
                               if duracion and duracion > 0 else 1.0)

    def _animar_ataque(self, dt):
        self.attack_timer += dt
        t = self.attack_timer
        base_h, base_p, base_r = RIGHT_ARM_REST
        base_fr = RIGHT_FOREARM_REST[2]

        # Fases reescaladas a la duracion pedida en atacar().
        k = self._escala_ataque
        t_ant = ATTACK_WINDUP * k
        t_imp = ATTACK_STRIKE * k
        t_rec = ATTACK_RECOVER * k

        if t < t_ant:
            p = t / t_ant
            self.right_arm_hpr = [base_h, base_p, lerp(base_r, base_r + ARCO_ANTICIPO, p)]
            self.right_forearm_hpr = [0, 0, lerp(base_fr, base_fr + ARCO_ANTEBRAZO_ANT, p)]

        elif t < t_ant + t_imp:
            p = (t - t_ant) / t_imp
            self.right_arm_hpr = [base_h, base_p,
                                  lerp(base_r + ARCO_ANTICIPO, base_r + ARCO_IMPACTO, p)]
            self.right_forearm_hpr = [0, 0,
                                      lerp(base_fr + ARCO_ANTEBRAZO_ANT, base_fr + ARCO_ANTEBRAZO_IMP, p)]

        elif t < t_ant + t_imp + t_rec:
            p = (t - t_ant - t_imp) / t_rec
            self.right_arm_hpr = [base_h, base_p, lerp(base_r + ARCO_IMPACTO, base_r, p)]
            self.right_forearm_hpr = [0, 0, lerp(base_fr + ARCO_ANTEBRAZO_IMP, base_fr, p)]

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