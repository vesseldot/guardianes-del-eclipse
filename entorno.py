"""
entorno.py — Carga de texturas del entorno (piso, cielo) con respaldo.

Por que este modulo existe:

  * simplepbr (el pipeline PBR de los personajes) IGNORA las texturas sueltas
    aplicadas a primitivas. Para texturar el suelo hay que darle un shader
    propio de Ursina y asignar la textura por 'entity.texture'.
  * La ruta del proyecto tiene acentos ('Graficacion') y el cargador por
    nombre de Ursina falla con ella. Cargamos la textura con el loader de
    Panda (que si acepta la ruta) y la envolvemos en un Texture de Ursina.

Si el archivo no existe, se devuelve None y el llamador usa su color liso,
igual que el resto del juego con los modelos que faltan.
"""

from ursina import Texture, color as ucolor
from panda3d.core import Filename, Texture as PandaTexture, SamplerState


def cargar_textura(ruta, repetir=True, anisotropico=16):
    """Devuelve un Texture de Ursina desde una ruta del sistema, o None.

    Aplica mipmaps y filtrado anisotropico: sin esto, una textura vista en
    angulo rasante (como el suelo con la camara casi a ras) se ve borrosa y
    con parpadeo (aliasing). Los mipmaps la suavizan a distancia y el filtro
    anisotropico recupera la nitidez en los angulos oblicuos.
    """
    if ruta is None:
        return None
    ruta = str(ruta)
    try:
        from ursina import application  # loader global de Panda
        p = Filename.from_os_specific(ruta).get_fullpath()
        ptex = application.base.loader.loadTexture(p)
        if repetir:
            ptex.setWrapU(PandaTexture.WM_repeat)
            ptex.setWrapV(PandaTexture.WM_repeat)
        else:
            ptex.setWrapU(PandaTexture.WM_clamp)
            ptex.setWrapV(PandaTexture.WM_clamp)
        # Mipmaps + anisotropico para nitidez en angulos rasantes.
        ptex.setMinfilter(SamplerState.FT_linear_mipmap_linear)
        ptex.setMagfilter(SamplerState.FT_linear)
        if anisotropico > 1:
            ptex.setAnisotropicDegree(anisotropico)
        return Texture(ptex)
    except Exception as e:
        print(f"[entorno] no se pudo cargar textura {ruta}: {e}")
        return None


def crear_cielo(ruta_textura):
    """Crea una cupula de cielo con la textura equirectangular dada.

    Ursina busca sus texturas por nombre y falla con rutas acentuadas, asi
    que cargamos el HDRI tonemapeado con el loader de Panda (via cargar_textura)
    y se lo asignamos a un Sky ya construido. El cielo no se repite: es una
    proyeccion 360, por eso 'repetir=False'.

    Devuelve el Sky, o None si la textura no existe (el fondo liso de la
    ventana queda como respaldo).
    """
    tex = cargar_textura(ruta_textura, repetir=False)
    if tex is None:
        return None
    from ursina.prefabs.sky import Sky
    cielo = Sky()
    cielo.texture = tex
    return cielo
