"""
proyectiles.py — Pool de proyectiles.

Crear y destruir entidades en cada disparo es la forma mas rapida de tirar
los FPS en Python: cada Entity nueva reserva memoria, registra colisiones
y despues obliga al recolector de basura a limpiarla.

Aqui las entidades se crean UNA vez al inicio y despues solo se activan y
desactivan. El coste por disparo pasa a ser practicamente cero.
"""

from ursina import Entity, Vec3, color as ucolor, time as utime
from config import Config


class Proyectil(Entity):
    """Un hechizo. Vive desactivado hasta que alguien lo pide al pool."""

    def __init__(self, **kwargs):
        super().__init__(
            model="sphere",
            scale=0.32,
            color=ucolor.white,
            collider=None,          # colision resuelta a mano: mas barato
            **kwargs
        )
        self.direccion = Vec3(0, 0, 1)
        self.velocidad = 22.0
        self.dano = 10
        self.vida_restante = 0.0
        self.de_jugador = True
        self.disable()

    def lanzar(self, origen, direccion, dano, de_jugador=True,
               col=ucolor.white, velocidad=22.0, duracion=2.2):
        self.position = origen
        self.direccion = direccion.normalized()
        self.dano = dano
        self.de_jugador = de_jugador
        self.velocidad = velocidad
        self.vida_restante = duracion
        self.color = col
        self.enable()

    def avanzar(self, dt):
        """Movimiento manual: evitamos un update() por entidad."""
        self.position += self.direccion * self.velocidad * dt
        self.vida_restante -= dt
        if self.vida_restante <= 0:
            self.disable()
            return False
        return True


class PoolProyectiles:
    """
    Contenedor de tamano fijo. El tamano lo define el preset de calidad,
    asi que en equipos modestos hay menos proyectiles simultaneos y por
    tanto menos trabajo por frame.
    """

    def __init__(self, tamano=None):
        tamano = tamano or Config.p("pool_proyectiles")
        self._items = [Proyectil() for _ in range(tamano)]
        self._siguiente = 0

    def pedir(self):
        """Devuelve un proyectil libre, o None si el pool esta lleno."""
        n = len(self._items)
        for _ in range(n):
            p = self._items[self._siguiente]
            self._siguiente = (self._siguiente + 1) % n
            if not p.enabled:
                return p
        return None

    def activos(self):
        for p in self._items:
            if p.enabled:
                yield p

    def limpiar(self):
        for p in self._items:
            p.disable()

    def redimensionar(self, tamano):
        """Se llama cuando el monitor de rendimiento cambia la calidad."""
        actual = len(self._items)
        if tamano > actual:
            self._items.extend(Proyectil() for _ in range(tamano - actual))
        elif tamano < actual:
            for p in self._items[tamano:]:
                p.disable()
                p.remove_node() if hasattr(p, "remove_node") else None
            self._items = self._items[:tamano]
        self._siguiente = 0
