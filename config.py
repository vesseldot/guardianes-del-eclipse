"""
config.py — Configuracion global, presets de calidad y monitor de rendimiento.

La idea central de este archivo: el juego debe correr en cualquier equipo.
Para eso hay tres presets de calidad y un monitor que baja la calidad solo
si detecta que los FPS se mantienen por debajo del umbral.
"""

from pathlib import Path

# ---------------------------------------------------------------- rutas
RAIZ = Path(__file__).parent
MODELOS = RAIZ / "modelos"
TEXTURAS = RAIZ / "texturas"
SONIDOS = RAIZ / "sonidos"

# Textura del suelo del arena (color base del set PBR de roca). Si el archivo
# no existe, el suelo usa su color liso de respaldo.
TEXTURA_PISO = RAIZ / "rock_wall_16_4k.blend" / "textures" / "rock_wall_16_diff_4k.jpg"
PISO_TILES = 6    # cuantas veces se repite la textura a lo largo del arena

# Cielo: HDRI de cielo nocturno, version tonemapeada a JPG (equirectangular).
# Usamos el JPG y no el .exr HDR porque el pipeline no hace tonemapping propio
# y el JPG ya viene con el rango comprimido, listo para mostrarse. Si falta,
# el fondo liso de la ventana queda como respaldo.
TEXTURA_CIELO = RAIZ / "NightSkyHDRI016B_1K" / "NightSkyHDRI016B_1K_TONEMAPPED.jpg"

# ---------------------------------------------------------------- ventana
TITULO = "Guardianes del Eclipse"
VSYNC = True              # limita a la tasa del monitor y evita quemar GPU
MOSTRAR_FPS = False       # activar solo al depurar: el contador cuesta unos ms

# ---------------------------------------------------------------- presets
# Cada preset controla lo caro: sombras dinamicas, particulas, niebla,
# distancia de dibujado y cuantos proyectiles pueden existir a la vez.
PRESETS = {
    "bajo": dict(
        sombras=False,
        particulas=False,
        max_particulas=0,
        distancia_vista=45,
        pool_proyectiles=14,
        detalle_suelo=1,      # subdivisiones del plano del arena
        suavizado=False,
    ),
    "medio": dict(
        sombras=False,
        particulas=True,
        max_particulas=24,
        distancia_vista=80,
        pool_proyectiles=24,
        detalle_suelo=2,
        suavizado=False,
    ),
    "alto": dict(
        sombras=True,
        particulas=True,
        max_particulas=60,
        distancia_vista=140,
        pool_proyectiles=40,
        detalle_suelo=4,
        suavizado=True,
    ),
}

CALIDAD_INICIAL = "medio"


class Config:
    """Estado mutable de configuracion. Se lee desde cualquier modulo."""

    calidad = CALIDAD_INICIAL
    auto_calidad = True       # permitir que el monitor baje la calidad solo
    volumen = 0.6
    sensibilidad = 1.0

    @classmethod
    def p(cls, clave):
        """Atajo para leer un valor del preset activo."""
        return PRESETS[cls.calidad][clave]


class MonitorRendimiento:
    """
    Vigila los FPS y baja la calidad automaticamente si el equipo no da.

    No usa listas ni asignaciones por frame: solo acumula un promedio movil,
    porque cualquier basura que generemos en update() se paga 60 veces por
    segundo.
    """

    UMBRAL_BAJAR = 28.0       # si el promedio cae de aqui, se baja un nivel
    VENTANA = 2.5             # segundos de observacion antes de decidir
    ORDEN = ("alto", "medio", "bajo")

    def __init__(self, al_cambiar=None):
        self.al_cambiar = al_cambiar
        self._acumulado = 0.0
        self._frames = 0
        self._enfriamiento = 3.0   # margen inicial para que cargue la escena

    def actualizar(self, dt):
        if not Config.auto_calidad or dt <= 0:
            return

        if self._enfriamiento > 0:
            self._enfriamiento -= dt
            return

        self._acumulado += dt
        self._frames += 1

        if self._acumulado < self.VENTANA:
            return

        fps = self._frames / self._acumulado
        self._acumulado = 0.0
        self._frames = 0

        if fps < self.UMBRAL_BAJAR:
            idx = self.ORDEN.index(Config.calidad)
            if idx < len(self.ORDEN) - 1:
                Config.calidad = self.ORDEN[idx + 1]
                self._enfriamiento = 5.0   # deja respirar tras el cambio
                if self.al_cambiar:
                    self.al_cambiar(Config.calidad)
