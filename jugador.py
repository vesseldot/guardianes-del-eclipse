"""
jugador.py — Guardian controlado por el jugador (combate estilo Souls/Elden Ring).

Mecanicas:
  * Estamina: se gasta al esquivar (rodar con i-frames) y al correr (sprint);
    se regenera sola tras una breve pausa.
  * Melee: ataque ligero (clic izq) y pesado (clic der) con el arma equipada.
  * Hechizos: a distancia, gastan FP y tienen recarga.
  * Frascos: curaciones limitadas (estilo Estus).
  * Camara con FIJADO de objetivo (lock-on): con el jefe fijado la camara lo
    mantiene encuadrado y el jugador siempre lo encara; sin fijar, orbita
    libre con el raton.
"""

from ursina import Entity, Vec3, held_keys, camera, lerp, clamp, mouse
from recursos import crear_visual, animar
from datos import GUARDIANES, ARMAS, HECHIZOS
from config import Config
from movimientos_personaje import MovimientoPersonaje, ARMAS_GLB
import sonido

LIMITE_ARENA = 24.0   # radio del arena; evita que el jugador se salga

# ------------------------------------------------------ ajustes de camara
CAM_FOV = 85.0             # campo de vision amplio: se ve mas arena de golpe.
                           # Pensando en la vista tipo "coliseo" a futuro; subir
                           # este valor abre mas el plano (ojo: >100 distorsiona).
CAM_SENSIBILIDAD = 42.0    # cuanto gira la camara por unidad de raton
CAM_DISTANCIA = 20.0       # distancia inicial de la camara al jugador
CAM_DIST_MIN = 6.0         # acercamiento maximo con la rueda del raton
CAM_DIST_MAX = 30.0        # alejamiento maximo con la rueda del raton
CAM_ZOOM_PASO = 2.0        # cuanto acerca/aleja cada muesca de la rueda
CAM_PITCH_INICIAL = 32.0   # inclinacion de partida (menor = mas horizontal)
CAM_PITCH_MIN = 12.0       # no dejar que la camara baje al ras del suelo
CAM_PITCH_MAX = 72.0       # ni que suba a vista cenital total
CAM_SUAVIZADO = 8.0        # cuanto persigue la camara al jugador (mayor = mas firme)
CAM_SUAVIZADO_GIRO = 7.0   # amortigua el giro del raton (menor = mas pesado/estable)
CAM_ALTURA_MIRADA = 1.3    # a que altura del jugador mira la camara (aprox. pecho)

# Los modelos .glb estan exportados mirando hacia -z (hacia el visor), asi que
# hay que girarlos 180 grados para que "adelante" sea hacia donde avanzan.
FRENTE_MODELO = 180.0

# ------------------------------------------------- combate estilo Souls
ESTAMINA_MAX = 100.0
ESTAMINA_REGEN = 30.0       # estamina por segundo
ESTAMINA_ESPERA = 0.45      # pausa de regen tras gastar estamina
COSTO_RODAR = 34.0          # estamina que cuesta esquivar
SPRINT_DRENAJE = 22.0       # estamina por segundo al correr
SPRINT_MULT = 1.7           # multiplicador de velocidad al correr
RODAR_DUR = 0.40            # cuanto dura el rodado
RODAR_IFRAMES = 0.28        # invulnerabilidad dentro del rodado
RODAR_VEL = 15.0            # velocidad del desplazamiento del rodado

FP_MAX = 100.0
FP_REGEN = 5.0              # el FP se recupera despacio

FRASCOS_MAX = 4
FRASCO_CURA = 0.45          # fraccion de vida_max que cura cada frasco
BEBER_DUR = 0.65            # tiempo bebiendo (rooteado y vulnerable)


class Jugador(Entity):

    def __init__(self, clave_guardian, **kwargs):
        super().__init__(**kwargs)
        datos = GUARDIANES[clave_guardian]

        self.clave = clave_guardian
        self.nombre = datos["nombre"]
        self.vida_max = datos["vida"]
        self.vida = self.vida_max
        self.dano = datos["dano"]           # poder base: se suma a armas y hechizos
        self.velocidad = datos["velocidad"]
        self.cadencia = datos["cadencia"]   # (compat) ya no controla auto-fuego

        self.invulnerable = 0.0
        self.vivo = True

        # -------- recursos estilo Souls --------
        self.estamina = ESTAMINA_MAX
        self.estamina_max = ESTAMINA_MAX
        self.fp = FP_MAX
        self.fp_max = FP_MAX
        self.frascos = FRASCOS_MAX
        self.frascos_max = FRASCOS_MAX
        self.recarga_mult = 1.0             # rebajado por mejoras de la tienda

        self.arma_idx = 0
        self.hechizo_idx = 0
        self.fijado = False                 # lock-on al jefe
        self._objetivo = None
        self._otros_objetivos = ()          # enemigos extra golpeables (ver actualizar)

        # temporizadores de accion (0 = libre)
        self._t_rodar = 0.0
        self._t_ataque = 0.0
        self._t_beber = 0.0
        self._cd_hechizo = 0.0
        self._espera_est = 0.0
        self._impacto_t = 0.0
        self._impacto_activo = False
        self._ataque_pesado = False
        self._dir_rodar = Vec3(0, 0, 1)

        self.visual, self.actor = crear_visual(self, clave_guardian)

        # El caminar/correr/golpear del modelo lo decide movimientos_personaje.py
        # (calcado de Guardian Naturaleza.py); aqui solo se crea y se le cuelga
        # el arma equipada.
        self.movimiento = MovimientoPersonaje(self.actor)
        # Todas las armas de una vez: asi el primer cambio de arma en combate
        # no provoca un tiron por cargar su .glb (ver precargar_armas).
        self.movimiento.precargar_armas(
            [a["modelo"] for a in ARMAS if a.get("modelo")])
        self._equipar_arma_actual()

        # Camara: angulos "objetivo" que mueve el raton y angulos "reales" que
        # los persiguen con amortiguacion (da la sensacion pesada y estable).
        self.cam_yaw = 0.0
        self.cam_pitch = CAM_PITCH_INICIAL
        self.cam_yaw_obj = 0.0
        self.cam_pitch_obj = CAM_PITCH_INICIAL
        self.cam_dist = CAM_DISTANCIA
        camera.fov = CAM_FOV

    # ---------------------------------------------------------- accesores
    @property
    def arma(self):
        return ARMAS[self.arma_idx]

    @property
    def hechizo(self):
        return HECHIZOS[self.hechizo_idx]

    def ocupado(self):
        """True si esta en medio de una accion que bloquea a las demas."""
        return self._t_rodar > 0 or self._t_ataque > 0 or self._t_beber > 0

    def reponer_recursos(self):
        """Al empezar un combate: estamina, FP y frascos al maximo."""
        self.estamina = self.estamina_max
        self.fp = self.fp_max
        self.frascos = self.frascos_max
        self._t_rodar = self._t_ataque = self._t_beber = 0.0
        self._cd_hechizo = self._espera_est = 0.0
        self._impacto_activo = False
        self.movimiento.attacking = False

    def _equipar_arma_actual(self):
        """Cuelga en la mano el .glb del arma equipada, si existe (ver ARMAS['modelo'])."""
        modelo = self.arma.get("modelo")
        if modelo and modelo in ARMAS_GLB:
            self.movimiento.equipar_arma(modelo)
        else:
            self.movimiento.quitar_arma()

    # --------------------------------------------------------------- vida
    def recibir_dano(self, cantidad):
        if self.invulnerable > 0 or not self.vivo:
            return
        self.vida -= cantidad
        self.invulnerable = 0.5        # ventana de gracia tras el golpe
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False

    def curar(self, cantidad):
        self.vida = min(self.vida_max, self.vida + cantidad)

    # ---------------------------------------------------------- acciones
    def esquivar(self):
        """Rodar: gasta estamina y da invulnerabilidad breve (i-frames)."""
        if not self.vivo or self.ocupado() or self.estamina < COSTO_RODAR:
            return
        self._gastar_estamina(COSTO_RODAR)
        sonido.reproducir_sfx("dash")
        self._t_rodar = RODAR_DUR
        self.invulnerable = max(self.invulnerable, RODAR_IFRAMES)
        self._dir_rodar = self._direccion_input() or self._hacia_camara()
        animar(self.actor, "Roll", en_bucle=False)

    def atacar(self, pesado=False):
        """Ataque melee. Ligero (rapido) o pesado (lento, mas dano)."""
        if not self.vivo or self.ocupado() or self._t_ataque > 0:
            return
        self._ataque_pesado = pesado
        self._t_ataque = self.arma["recuperacion"] * (1.7 if pesado else 1.0)
        # El golpe conecta a mitad del gesto (justo cuando el arma baja), no a
        # un tiempo fijo: con el martillo el dano entraba mucho antes de que el
        # arma llegara abajo.
        self._impacto_t = self._t_ataque * 0.45
        self._impacto_activo = True
        if self.fijado and self._obj_valido():
            self._mirar_instant(self._objetivo)       # encara al jefe al golpear
        sonido.reproducir_ataque_arma(self.arma["nombre"])
        # El gesto dura lo mismo que el bloqueo del arma, asi se ve completo.
        self.movimiento.atacar(self._t_ataque)

    def lanzar_hechizo(self, pool, objetivo, col):
        """Hechizo a distancia: gasta FP y entra en recarga."""
        if not self.vivo or self.ocupado():
            return False
        h = self.hechizo
        if self._cd_hechizo > 0 or self.fp < h["costo_fp"]:
            return False
        self.fp -= h["costo_fp"]
        self._cd_hechizo = h["recarga"] * self.recarga_mult

        if objetivo is not None and objetivo.vivo:
            direccion = Vec3(objetivo.x - self.x, 0, objetivo.z - self.z)
            if direccion.length() < 0.01:
                direccion = self._hacia_adelante()
        else:
            direccion = self._hacia_adelante()

        p = pool.pedir()
        if p is None:
            return False
        p.lanzar(origen=self.world_position + Vec3(0, 1.2, 0),
                 direccion=direccion, dano=h["dano"] + self.dano,
                 de_jugador=True, col=col, velocidad=h["velocidad"])
        sonido.reproducir_sfx("spell_attack")
        animar(self.actor, "Cast", en_bucle=False)
        return True

    def curar_frasco(self):
        """Bebe un frasco: cura y deja al jugador vulnerable un instante."""
        if not self.vivo or self.ocupado():
            return
        if self.frascos <= 0:
            sonido.reproducir_sfx("empty_jar")
            return
        self.frascos -= 1
        self._t_beber = BEBER_DUR
        self.curar(self.vida_max * FRASCO_CURA)
        sonido.reproducir_sfx("curarse")
        animar(self.actor, "Drink", en_bucle=False)

    def alternar_fijado(self, objetivo):
        self.fijado = (not self.fijado) if (objetivo and objetivo.vivo) else False

    def elegir_arma(self, indice):
        if 0 <= indice < len(ARMAS):
            self.arma_idx = indice
            self._equipar_arma_actual()

    def cambiar_hechizo(self, delta=1):
        self.hechizo_idx = (self.hechizo_idx + delta) % len(HECHIZOS)

    def zoom_camara(self, direccion):
        """Rueda del raton: acerca (direccion<0) o aleja (direccion>0) la camara."""
        self.cam_dist = clamp(self.cam_dist + direccion * CAM_ZOOM_PASO,
                              CAM_DIST_MIN, CAM_DIST_MAX)

    # --------------------------------------------------------- bucle vida
    def actualizar(self, dt, objetivo=None, otros_objetivos=None):
        """Se llama desde el bucle principal (un solo punto de actualizacion).

        'otros_objetivos' son enemigos golpeables ademas del jefe fijado
        (por ahora, los fantasmas que invoca el conejo): cualquiera con
        '.vivo', '.x'/'.z' y 'recibir_dano()' sirve.
        """
        if not self.vivo:
            return

        self._objetivo = objetivo
        self._otros_objetivos = otros_objetivos or ()

        # -- temporizadores --
        self.invulnerable = max(0.0, self.invulnerable - dt)
        self._t_ataque = max(0.0, self._t_ataque - dt)
        self._t_beber = max(0.0, self._t_beber - dt)
        self._cd_hechizo = max(0.0, self._cd_hechizo - dt)
        self._espera_est = max(0.0, self._espera_est - dt)

        # -- golpe de melee con retardo de windup --
        if self._impacto_activo:
            self._impacto_t -= dt
            if self._impacto_t <= 0:
                self._impacto_activo = False
                self._resolver_melee(objetivo)

        # -- rodado: tiene prioridad y mueve por si mismo --
        if self._t_rodar > 0:
            self._t_rodar -= dt
            self.position += self._dir_rodar * RODAR_VEL * dt
            self._limitar_arena()
            self.rotation_y = self._angulo(self._dir_rodar) + FRENTE_MODELO
            self._regenerar(dt, corriendo=False)
            self._orbitar_camara(dt)
            self.movimiento.actualizar(dt, moviendo=True, corriendo=True)
            return

        # -- bebiendo o en recuperacion de ataque: rooteado --
        bloqueado = self._t_beber > 0 or self._t_ataque > 0
        corriendo = False

        dx = held_keys["d"] - held_keys["a"]
        dz = held_keys["w"] - held_keys["s"]
        moviendo = not bloqueado and bool(dx or dz)

        if moviendo:
            direccion = self._direccion_input()
            vel = self.velocidad
            if self._quiere_sprint() and self.estamina > 0:
                vel *= SPRINT_MULT
                corriendo = True
                self._gastar_estamina(SPRINT_DRENAJE * dt)

            self.position += direccion * vel * dt
            self._limitar_arena()

            if self.fijado and self._obj_valido():
                self._mirar_a(objetivo, dt)          # encara siempre al jefe
            else:
                ang = self._angulo(direccion) + FRENTE_MODELO
                self.rotation_y = self._lerp_ang(self.rotation_y, ang, 12 * dt)
        else:
            if self.fijado and self._obj_valido():
                self._mirar_a(objetivo, dt)

        self.movimiento.actualizar(dt, moviendo=moviendo, corriendo=corriendo)
        self._regenerar(dt, corriendo)
        self._orbitar_camara(dt)

    # ------------------------------------------------------ utilidades
    def _obj_valido(self):
        return self._objetivo is not None and self._objetivo.vivo

    def _quiere_sprint(self):
        return held_keys["left shift"] or held_keys["right shift"]

    def _gastar_estamina(self, cantidad):
        self.estamina = max(0.0, self.estamina - cantidad)
        self._espera_est = ESTAMINA_ESPERA

    def _regenerar(self, dt, corriendo):
        if not corriendo and self._espera_est <= 0:
            self.estamina = min(self.estamina_max, self.estamina + ESTAMINA_REGEN * dt)
        self.fp = min(self.fp_max, self.fp + FP_REGEN * dt)

    def _limitar_arena(self):
        plano = Vec3(self.x, 0, self.z)
        if plano.length() > LIMITE_ARENA:
            plano = plano.normalized() * LIMITE_ARENA
            self.x, self.z = plano.x, plano.z

    def _direccion_input(self):
        """Direccion de movimiento relativa a la camara, o None si no hay input."""
        dx = held_keys["d"] - held_keys["a"]
        dz = held_keys["w"] - held_keys["s"]
        if not (dx or dz):
            return None
        from math import radians, sin, cos
        yw = radians(self.cam_yaw)
        adelante = Vec3(sin(yw), 0, cos(yw))
        derecha = Vec3(cos(yw), 0, -sin(yw))
        return (adelante * dz + derecha * dx).normalized()

    def _hacia_camara(self):
        """Vector que apunta hacia la camara (para el retroceso sin input)."""
        from math import radians, sin, cos
        yw = radians(self.cam_yaw)
        return -Vec3(sin(yw), 0, cos(yw))

    def _hacia_adelante(self):
        """Hacia donde mira visualmente el personaje."""
        from math import radians, sin, cos
        a = radians(self.rotation_y - FRENTE_MODELO)
        return Vec3(sin(a), 0, cos(a))

    def _resolver_melee(self, objetivo):
        dano = self.arma["dano"] + self.dano
        if self._ataque_pesado:
            dano *= self.arma["pesado"]

        if objetivo is not None and objetivo.vivo:
            dx = objetivo.x - self.x
            dz = objetivo.z - self.z
            dist = (dx * dx + dz * dz) ** 0.5
            radio = 1.6 * objetivo.definicion.get("escala", 1.0)
            if dist <= self.arma["alcance"] + radio:
                objetivo.recibir_dano(dano)

        # Enemigos extra (p.ej. los fantasmas que invoca el conejo): mismo
        # alcance del arma, radio de golpe generico porque no traen
        # 'definicion' con escala como los jefes.
        for otro in self._otros_objetivos:
            if otro is None or not otro.vivo:
                continue
            dx = otro.x - self.x
            dz = otro.z - self.z
            dist = (dx * dx + dz * dz) ** 0.5
            if dist <= self.arma["alcance"] + 1.0:
                otro.recibir_dano(dano)

    def _mirar_a(self, objetivo, dt):
        ang = self._angulo(Vec3(objetivo.x - self.x, 0, objetivo.z - self.z)) + FRENTE_MODELO
        self.rotation_y = self._lerp_ang(self.rotation_y, ang, 14 * dt)

    def _mirar_instant(self, objetivo):
        self.rotation_y = self._angulo(Vec3(objetivo.x - self.x, 0, objetivo.z - self.z)) + FRENTE_MODELO

    @staticmethod
    def _angulo(direccion):
        from math import atan2, degrees
        return degrees(atan2(direccion.x, direccion.z))

    @staticmethod
    def _lerp_ang(a, b, t):
        """Interpolacion angular por el camino corto (evita giros de 360)."""
        d = (b - a + 180) % 360 - 180
        return a + d * t

    # ------------------------------------------------------------ camara
    def _orbitar_camara(self, dt):
        from math import radians, sin, cos

        # Los menus (tienda/seleccion) bajan el fov a 45 para el escaparate;
        # aqui lo devolvemos al de combate para que al volver no quede cerrado.
        if camera.fov != CAM_FOV:
            camera.fov = CAM_FOV

        sens = CAM_SENSIBILIDAD * Config.sensibilidad
        if self.fijado and self._obj_valido():
            # Lock-on: el yaw sigue automaticamente la direccion jugador->jefe;
            # el raton solo ajusta la inclinacion.
            dir_obj = Vec3(self._objetivo.x - self.x, 0, self._objetivo.z - self.z)
            self.cam_yaw_obj = self._acercar_yaw(self.cam_yaw_obj, self._angulo(dir_obj))
            self.cam_pitch_obj -= mouse.velocity[1] * sens
        else:
            self.cam_yaw_obj += mouse.velocity[0] * sens
            self.cam_pitch_obj -= mouse.velocity[1] * sens
        self.cam_pitch_obj = clamp(self.cam_pitch_obj, CAM_PITCH_MIN, CAM_PITCH_MAX)

        # Los angulos reales persiguen al objetivo con amortiguacion.
        t = clamp(CAM_SUAVIZADO_GIRO * dt, 0, 1)
        self.cam_yaw = self._lerp_ang(self.cam_yaw, self.cam_yaw_obj, t)
        self.cam_pitch = lerp(self.cam_pitch, self.cam_pitch_obj, t)

        # Orbitamos alrededor del punto al que mira la camara (pecho).
        centro = self.world_position + Vec3(0, CAM_ALTURA_MIRADA, 0)
        yw = radians(self.cam_yaw)
        pt = radians(self.cam_pitch)
        horiz = cos(pt) * self.cam_dist
        altura = sin(pt) * self.cam_dist
        offset = Vec3(-sin(yw) * horiz, altura, -cos(yw) * horiz)

        # Rotacion fijada por angulos: rotation_z = 0 mantiene el horizonte
        # nivelado siempre (nada de balanceo).
        camera.position = lerp(camera.position, centro + offset,
                               clamp(CAM_SUAVIZADO * dt, 0, 1))
        camera.rotation = Vec3(self.cam_pitch, self.cam_yaw, 0)

    @staticmethod
    def _acercar_yaw(actual, objetivo):
        """Expresa 'objetivo' como el valor continuo mas cercano a 'actual'."""
        d = (objetivo - actual + 180) % 360 - 180
        return actual + d

    # ----------------------------------------------------- mejoras tienda
    def aplicar_objeto(self, objeto):
        efecto, valor = objeto["efecto"], objeto["valor"]
        if efecto == "dano":
            self.dano += valor
        elif efecto == "vida_max":
            self.vida_max += valor
            self.vida += valor
        elif efecto == "velocidad":
            self.velocidad += valor
        elif efecto == "cadencia":
            # ahora rebaja la recarga de los hechizos
            self.recarga_mult = max(0.4, self.recarga_mult - valor)
        elif efecto == "curar":
            self.curar(valor)
