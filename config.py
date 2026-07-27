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
# Pantalla completa a la resolucion nativa del monitor. Se aplica al crear la
# ventana, ANTES de construir la interfaz: los fondos se escalan una sola vez
# con la relacion de aspecto final. Ponerlo en False deja ventana.
PANTALLA_COMPLETA = True

# ---------------------------------------------------------------- presets
# Cada preset controla lo caro: sombras dinamicas, particulas, niebla,
# distancia de dibujado y cuantos proyectiles pueden existir a la vez.
# Claves de GPU (las que de verdad pesan en gama baja):
#   pbr              -> inicializar el pipeline PBR de simplepbr (decision de
#                       ARRANQUE; si es False los modelos salen unlit, mas
#                       barato pero mas planos).
#   pbr_msaa         -> muestras de MSAA del pipeline PBR (0 = sin, lo mas
#                       barato; 4 = suave pero caro en iGPU). Se ajusta en vivo.
#   pbr_normal_maps  -> normal/occlusion maps en los modelos. Se ajusta en vivo.
#   pbr_max_luces    -> tope de luces que evalua el shader PBR por pixel.
#   anisotropico     -> filtrado anisotropico del suelo (1 = ninguno; 16 = maximo
#                       nitido en angulo rasante, pero cuesta ancho de banda).
#   tex_suelo_max    -> lado maximo (px) al que se reescala la textura del suelo
#                       al cargarla (0 = sin reescalar, 4K original). Reduce VRAM.
#   tex_modelo_max   -> lado maximo (px) de las texturas de los .glb. Es la
#                       palanca de VRAM mas importante del juego: los modelos
#                       traen mapas de 8192x8192 (~340 MB cada uno) y en combate
#                       hay jugador + arma + jefe a la vez. Ver
#                       entorno.reducir_texturas. Nunca se deja en 0: 8K no se
#                       justifica en ninguna GPU para personajes de este tamano
#                       en pantalla.
#   luz_relleno      -> encender la 3a luz (relleno). En bajo se apaga: 2 luces.
PRESETS = {
    "bajo": dict(
        sombras=False,
        particulas=False,
        max_particulas=0,
        distancia_vista=45,
        pool_proyectiles=14,
        detalle_suelo=1,      # subdivisiones del plano del arena
        suavizado=False,
        pbr=True,             # PBR minimo (ver pbr_msaa/normal_maps abajo)
        pbr_msaa=0,
        pbr_normal_maps=False,
        pbr_max_luces=2,
        anisotropico=1,
        tex_suelo_max=1024,   # suelo a 1K en iGPU
        tex_modelo_max=512,   # personajes/armas a 512 px en iGPU
        luz_relleno=False,
    ),
    "medio": dict(
        sombras=False,
        particulas=True,
        max_particulas=24,
        distancia_vista=80,
        pool_proyectiles=24,
        detalle_suelo=2,
        suavizado=False,
        pbr=True,
        pbr_msaa=0,
        pbr_normal_maps=False,
        pbr_max_luces=3,
        anisotropico=4,
        tex_suelo_max=2048,   # suelo a 2K
        tex_modelo_max=1024,  # personajes/armas a 1K
        luz_relleno=True,
    ),
    "alto": dict(
        sombras=True,
        particulas=True,
        max_particulas=60,
        distancia_vista=140,
        pool_proyectiles=40,
        detalle_suelo=4,
        suavizado=True,
        pbr=True,
        pbr_msaa=4,
        pbr_normal_maps=True,
        pbr_max_luces=4,
        anisotropico=16,
        tex_suelo_max=0,      # 4K original, sin reescalar
        tex_modelo_max=2048,  # personajes/armas a 2K (nunca 8K)
        luz_relleno=True,
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
