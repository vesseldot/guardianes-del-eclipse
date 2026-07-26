"""
vitrina.py — Muestra un modelo 3D girando lentamente.

Se usa en la seleccion de guardian y en la tienda para presentar el modelo
del personaje. Reutiliza crear_visual, asi que si un modelo aun no existe
muestra su primitiva de respaldo, igual que en el combate.
"""

from ursina import Entity, destroy, color as ucolor


class Vitrina:

    def __init__(self, position=(0, 0, 0), velocidad_giro=35.0, con_soporte=True):
        self.raiz = Entity(position=position, enabled=False)
        self.velocidad_giro = velocidad_giro
        self.clave = None
        self._contenedor = None
        self._visual = None
        self._actor = None

        # Disco oscuro bajo el modelo para que no parezca flotar en el vacio.
        self.soporte = None
        if con_soporte:
            self.soporte = Entity(parent=self.raiz, model="circle", scale=2.6,
                                  rotation_x=90, position=(0, 0.01, 0),
                                  color=ucolor.rgb32(26, 26, 32))

    def mostrar(self, clave):
        """Muestra el modelo 'clave'. Si ya es el visible, no lo recarga."""
        # Importacion local para no crear un ciclo main -> vitrina -> recursos.
        from recursos import crear_visual

        if clave == self.clave and self.raiz.enabled:
            return
        self._limpiar()

        # El modelo cuelga de un contenedor propio para poder destruirlo
        # entero de una vez sin tocar el soporte.
        self._contenedor = Entity(parent=self.raiz)
        self._visual, self._actor = crear_visual(self._contenedor, clave)
        self.clave = clave
        self.raiz.rotation_y = 0
        self.raiz.enabled = True
        # Quieto a proposito: solo el escaparate gira (ver rotar()), el
        # modelo no camina ni en la seleccion de guardian ni en la tienda.

    def _limpiar(self):
        # Un Actor es un nodo de Panda (no una Entity de Ursina); conviene
        # cerrarlo antes de destruir su contenedor.
        if self._actor is not None:
            try:
                self._actor.cleanup()
            except Exception:
                pass
        if self._contenedor is not None:
            destroy(self._contenedor)
        self._contenedor = None
        self._visual = None
        self._actor = None
        self.clave = None

    def rotar(self, dt):
        if self.raiz.enabled:
            self.raiz.rotation_y += dt * self.velocidad_giro

    def ocultar(self):
        self.raiz.enabled = False
