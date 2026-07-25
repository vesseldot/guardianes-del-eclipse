"""
sonido.py - Musica y efectos del juego.

El cargador por nombre de Ursina puede fallar con rutas que contienen espacios
o acentos, asi que los audios se cargan desde rutas absolutas convertidas al
formato de Panda3D. Si algo falta o falla, se omite el sonido y la partida
continua.
"""

from pathlib import Path

from panda3d.core import Filename
from ursina import Audio, Entity, application

from config import Config


RAIZ = Path(__file__).parent
DIR_MUSICA = RAIZ / "assets" / "music"
DIR_SFX = RAIZ / "assets" / "sounds"

MUSICA_VOLUMEN = 0.5
SFX_VOLUMEN = 0.8

MUSICA_PANTALLA = "menu"
PISTAS_COMBATE = ("battle1", "battle2", "battle3")

PISTAS = {
    "menu": "menu_inicio.wav",
    "tienda": "tienda_dino.wav",
    "battle1": "battle1.mp3",
    "battle2": "battle2.mp3",
    "battle3": "battle3.ogg",
    "final": "final battle.mp3",
}

SFX = {
    "a_bodoque": "a-bodoque.mp3",
    "muere_bodoque": "muere-bodoque.mp3",
    "curarse": "curarse.wav",
    "spell_attack": "spell_attack.wav",
    "enemy_attack": "enemy_attack.wav",
    "sword_attack": "sword_attack.mp3",
    "hammer_attack": "hammer_attack.wav",
    "dagger_attack": "dagger_attack.wav",
    "defeat": "defeat.flac",
    "victoria": "victroy.flac",
    "dash": "dash.wav",
    "empty_jar": "empty_jar.wav",
    "button": "button.wav",
}

SFX_ARMAS = {
    "Espada": "sword_attack",
    "Martillo": "hammer_attack",
    "Dagas": "dagger_attack",
}


def _ruta_panda(ruta):
    return Filename.from_os_specific(str(ruta)).get_fullpath()


def _cargar_clip(ruta):
    if not ruta.exists():
        return None
    try:
        return application.base.loader.loadSfx(_ruta_panda(ruta))
    except Exception:
        return None


def _volumen(base):
    return base * Config.volumen


class GestorSonido(Entity):
    """Manager centralizado: una musica activa y SFX solapables."""

    def __init__(self):
        super().__init__(ignore_paused=True)
        self.pistas = {}
        self._pista_actual = None
        self._tiempo_musica = 0.0
        self._duracion_musica = 0.0
        self._precargar_musica()

    def _precargar_musica(self):
        for clave, archivo in PISTAS.items():
            clip = _cargar_clip(DIR_MUSICA / archivo)
            if clip is None:
                continue
            self.pistas[clave] = Audio(
                clip,
                volume=_volumen(MUSICA_VOLUMEN),
                loop=False,
                autoplay=False,
                ignore_paused=True,
            )

    def actualizar(self, dt):
        if not self._pista_actual or dt <= 0:
            return

        audio = self.pistas.get(self._pista_actual)
        if audio is None or not audio.clip:
            return

        self._tiempo_musica += dt
        if self._duracion_musica <= 0:
            if not audio.playing:
                audio.play(0)
            return

        if self._tiempo_musica >= max(0.0, self._duracion_musica - 0.05):
            audio.play(0)
            self._tiempo_musica = 0.0

    def reproducir_musica(self, clave):
        audio = self.pistas.get(clave)
        if self._pista_actual == clave:
            if audio is not None:
                audio.volume = _volumen(MUSICA_VOLUMEN)
                if not audio.playing:
                    audio.play(0)
                    self._tiempo_musica = 0.0
            return

        if self._pista_actual:
            actual = self.pistas.get(self._pista_actual)
            if actual is not None:
                actual.stop(destroy=False)

        self._pista_actual = clave
        self._tiempo_musica = 0.0
        self._duracion_musica = 0.0

        if audio is None:
            return

        audio.volume = _volumen(MUSICA_VOLUMEN)
        audio.play(0)
        self._duracion_musica = audio.length

    def reproducir_sfx(self, clave):
        archivo = SFX.get(clave)
        if archivo is None:
            return

        clip = _cargar_clip(DIR_SFX / archivo)
        if clip is None:
            return

        try:
            Audio(
                clip,
                volume=_volumen(SFX_VOLUMEN),
                autoplay=True,
                auto_destroy=True,
                ignore_paused=True,
            )
        except Exception:
            return

    def reproducir_ataque_arma(self, nombre_arma):
        clave = SFX_ARMAS.get(nombre_arma)
        if clave is not None:
            self.reproducir_sfx(clave)


_gestor = None


def obtener_gestor():
    global _gestor
    if _gestor is None:
        try:
            _gestor = GestorSonido()
        except Exception:
            return None
    return _gestor


def actualizar(dt):
    gestor = obtener_gestor()
    if gestor is not None:
        gestor.actualizar(dt)


def musica_para_estado(estado, indice_jefe=0, total_jefes=0):
    if estado in ("menu", "seleccion", "instrucciones", "transicion", "fin"):
        clave = MUSICA_PANTALLA
    elif estado == "tienda":
        clave = "tienda"
    elif estado == "combate":
        if total_jefes and indice_jefe == total_jefes - 1:
            clave = "final"
        else:
            clave = PISTAS_COMBATE[indice_jefe % len(PISTAS_COMBATE)]
    else:
        clave = MUSICA_PANTALLA

    gestor = obtener_gestor()
    if gestor is not None:
        gestor.reproducir_musica(clave)


def reproducir_sfx(clave):
    gestor = obtener_gestor()
    if gestor is not None:
        gestor.reproducir_sfx(clave)


def reproducir_ataque_arma(nombre_arma):
    gestor = obtener_gestor()
    if gestor is not None:
        gestor.reproducir_ataque_arma(nombre_arma)
