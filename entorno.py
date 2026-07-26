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
from panda3d.core import (Filename, Texture as PandaTexture, SamplerState,
                          PNMImage)


def _reducir_textura(ptex, max_lado):
    """Reescala el Texture de Panda a lo sumo 'max_lado' px por lado.

    Una textura 4K ocupa ~45 MB de VRAM y se muestrea mas caro; en gama baja
    conviene bajarla a 1K/2K. max_lado<=0 la deja intacta.
    """
    if max_lado <= 0:
        return
    x, y = ptex.getXSize(), ptex.getYSize()
    if max(x, y) <= max_lado:
        return
    escala = max_lado / max(x, y)
    img = PNMImage()
    if not ptex.store(img):        # vuelca la imagen en RAM a un PNMImage
        return
    pequena = PNMImage(max(1, int(x * escala)), max(1, int(y * escala)),
                       img.getNumChannels())
    pequena.quick_filter_from(img)  # remuestreo con box filter (barato)
    ptex.load(pequena)


def reducir_texturas(nodo, max_lado):
    """Reescala todas las texturas de un nodo cargado (modelo .glb) a lo sumo
    'max_lado' px por lado. Devuelve cuantas redujo.

    Por que hace falta: los .glb exportados por Meshy traen texturas de
    8192x8192, que son ~340 MB de VRAM CADA UNA. Un personaje con dos mapas
    son 681 MB, y en combate hay jugador + arma + jefe a la vez: mas de 1.5 GB.
    En una GPU integrada (512 MB) el driver aborta con "requested more GPU
    memory than is available". A 1024 px la misma textura ocupa ~5.5 MB.

    No se puede resolver con la configuracion de Panda ('max-texture-dimension'
    o 'texture-scale'): el cargador de glTF construye las texturas directamente
    desde los buffers embebidos y no pasa por el camino que respeta esas
    variables (comprobado). Hay que reescalarlas despues de cargar, y hacerlo
    ANTES del primer dibujado: la VRAM se reserva al renderizar, asi que la
    version de 8K nunca llega a la tarjeta.
    """
    if max_lado <= 0 or nodo is None:
        return 0
    n = 0
    try:
        for ptex in nodo.findAllTextures():
            antes = max(ptex.getXSize(), ptex.getYSize())
            _reducir_textura(ptex, max_lado)
            if max(ptex.getXSize(), ptex.getYSize()) < antes:
                n += 1
    except Exception as e:
        print(f"[entorno] no se pudieron reducir texturas: {e}")
    return n


def cargar_textura(ruta, repetir=True, anisotropico=16, max_lado=0):
    """Devuelve un Texture de Ursina desde una ruta del sistema, o None.

    Aplica mipmaps y filtrado anisotropico: sin esto, una textura vista en
    angulo rasante (como el suelo con la camara casi a ras) se ve borrosa y
    con parpadeo (aliasing). Los mipmaps la suavizan a distancia y el filtro
    anisotropico recupera la nitidez en los angulos oblicuos.

    'max_lado' reescala la textura al cargarla (ver _reducir_textura), y
    'anisotropico' fija el grado de filtrado; ambos vienen del preset de
    calidad para aligerar la GPU en equipos modestos.
    """
    if ruta is None:
        return None
    ruta = str(ruta)
    try:
        from ursina import application  # loader global de Panda
        p = Filename.from_os_specific(ruta).get_fullpath()
        ptex = application.base.loader.loadTexture(p)
        # Reducir ANTES de fijar los filtros: load() reinicia el muestreo.
        _reducir_textura(ptex, max_lado)
        wrap = PandaTexture.WM_repeat if repetir else PandaTexture.WM_clamp
        ptex.setWrapU(wrap)
        ptex.setWrapV(wrap)
        # Mipmaps + anisotropico para nitidez en angulos rasantes.
        ptex.setMinfilter(SamplerState.FT_linear_mipmap_linear)
        ptex.setMagfilter(SamplerState.FT_linear)
        ptex.setAnisotropicDegree(max(1, anisotropico))
        return Texture(ptex)
    except Exception as e:
        print(f"[entorno] no se pudo cargar textura {ruta}: {e}")
        return None


def set_anisotropico(entidad, grado):
    """Cambia en vivo el grado anisotropico de la textura de una entidad.

    Se usa al cambiar de preset de calidad sin recargar la textura: baja el
    coste de muestreo del suelo en equipos modestos.
    """
    tex = getattr(entidad, "texture", None)
    ptex = getattr(tex, "_texture", None)   # Texture de Panda subyacente
    if ptex is not None:
        ptex.setAnisotropicDegree(max(1, grado))


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
