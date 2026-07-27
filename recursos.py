"""
recursos.py — Carga de modelos con respaldo automatico.

Punto clave del proyecto: el juego NO debe romperse si un modelo todavia
no esta exportado desde Blender. Si el .glb existe se carga como Actor
(con animaciones); si no, se dibuja una primitiva del color del personaje.

Asi el equipo puede programar y probar hoy, e ir sustituyendo modelos
conforme salen de Blender, sin tocar una sola linea de logica.
"""

from ursina import Entity, Vec3, color as ucolor
from panda3d.core import Filename
from config import MODELOS as DIR_MODELOS, Config
from datos import MODELOS
from entorno import reducir_texturas

# Panda3D expone Actor para modelos con animacion. Si el entorno no lo
# tiene disponible, seguimos funcionando en modo estatico.
try:
    from direct.actor.Actor import Actor
    ACTOR_DISPONIBLE = True
except Exception:
    Actor = None
    ACTOR_DISPONIBLE = False


def _ruta_panda(ruta):
    """
    Convierte una ruta del sistema (Windows: 'c:\\...\\sol.glb') al formato
    que entiende Panda3D ('/c/.../sol.glb'). Sin esto, el loader interpreta
    mal la unidad y los espacios/acentos de la ruta y no encuentra el .glb,
    cayendo por error al respaldo aunque el archivo exista.
    """
    return Filename.from_os_specific(str(ruta)).get_fullpath()


def _asentar_en_suelo(nodo, padre):
    """
    Sube el modelo para que su punto mas bajo quede en y=0 del padre.

    Los .glb suelen tener el origen en el centro del personaje, asi que al
    colocarlos en y=0 quedan medio enterrados. Medimos sus limites reales
    (ya con la escala aplicada) y lo elevamos justo lo necesario, sea cual
    sea la altura del modelo.
    """
    limites = nodo.getTightBounds(padre)
    if not limites:
        return
    min_y = limites[0][1]                 # punto mas bajo en el eje vertical
    pos = nodo.getPos(padre)
    nodo.setPos(padre, pos[0], pos[1] - min_y, pos[2])


# Cache de rutas ya comprobadas: evita golpear el disco en cada spawn.
_cache_rutas = {}

# Rutas que ya fallaron al cargarse como Actor: no se reintentan.
_sin_actor = set()


def ruta_modelo(clave):
    """Devuelve la ruta del .glb si existe, o None."""
    if clave in _cache_rutas:
        return _cache_rutas[clave]

    spec = MODELOS.get(clave)
    ruta = None
    if spec:
        candidata = DIR_MODELOS / spec["carpeta"] / spec["archivo"]
        if candidata.exists():
            ruta = candidata

    _cache_rutas[clave] = ruta
    return ruta


def _cargar_sin_esqueleto(ruta_p):
    """Carga un .glb descartando su skinning. Devuelve el nodo, o None.

    Por que hace falta: panda3d-gltf guarda el indice de mezcla de huesos de
    cada vertice en una columna de 16 bits, asi que un modelo con mas de 65535
    combinaciones distintas de huesos y pesos revienta al cargarlo
    (AssertionError en combine_mesh_skin). Le pasa al fantasma.

    Como esos modelos aqui no necesitan animacion esqueletica, se anula el paso
    que falla y la malla se carga estatica. Ojo: ese paso tambien aplicaba la
    transformacion del nodo padre, asi que el modelo sale con la escala en
    bruto del archivo y hay que compensarla con 'escala' en datos.MODELOS.
    """
    try:
        import gltf._converter as conv
    except Exception:
        return None
    original = conv.Converter.combine_mesh_skin
    conv.Converter.combine_mesh_skin = lambda self, geom_node, charinfo: None
    try:
        from ursina import application
        # Con cache: el .glb del fantasma pesa 34 MB y en el combate final
        # salen cuatro. La version con esqueleto nunca llega a cachearse
        # porque falla, asi que no hay riesgo de mezclar las dos.
        return application.base.loader.loadModel(ruta_p)
    except Exception as e:
        print(f"[recursos] tampoco cargo sin esqueleto: {e}")
        return None
    finally:
        conv.Converter.combine_mesh_skin = original


def crear_visual(padre, clave, escala_extra=1.0):
    """
    Adjunta la parte visible de un personaje a 'padre'.

    Devuelve (visual, actor). 'actor' es None si se uso el respaldo,
    lo que permite al codigo llamador saber si puede pedir animaciones.
    """
    spec = MODELOS.get(clave, dict(escala=1.0, respaldo="cube", color=ucolor.gray))
    escala = spec.get("escala", 1.0) * escala_extra
    ruta = ruta_modelo(clave)
    ruta_p = _ruta_panda(ruta) if ruta else None

    # Los modelos que ya se sabe que no cargan como Actor no se reintentan: el
    # fallo escupe un traceback y releer un .glb de decenas de MB para volver a
    # fallar cuesta, y en el combate final salen cuatro fantasmas de golpe.
    if ruta and ACTOR_DISPONIBLE and ruta_p not in _sin_actor:
        try:
            # Los .glb se cargan como Actor: es la forma que respeta sus
            # materiales/texturas PBR. El sombreado real lo aporta simplepbr
            # (se inicializa en main.py); sin el, estos modelos saldrian
            # planos y blancos.
            actor = Actor(ruta_p)
            # Reducir las texturas ANTES de que el modelo se dibuje por primera
            # vez: los .glb traen mapas de 8K (~340 MB de VRAM cada uno) y en
            # una GPU integrada el driver aborta. Ver entorno.reducir_texturas.
            reducir_texturas(actor, Config.p("tex_modelo_max"))
            actor.reparent_to(padre)
            actor.setScale(escala)
            _asentar_en_suelo(actor, padre)
            return actor, actor
        except Exception as e:
            # Un modelo mal exportado no debe tumbar la partida.
            _sin_actor.add(ruta_p)
            print(f"[recursos] {clave}: no carga como Actor, se usara estatico ({e})")

    if ruta:
        # Modelo sin animacion: mas barato que un Actor.
        try:
            visual = Entity(parent=padre, model=ruta_p, scale=escala)
        except Exception:
            visual = None
        if visual is None or visual.model is None:
            # Ultimo intento antes de rendirse a la primitiva: sin skinning.
            nodo = _cargar_sin_esqueleto(ruta_p)
            if nodo is None:
                return _respaldo(padre, spec, escala)
            visual = Entity(parent=padre, model=nodo, scale=escala)
        reducir_texturas(visual, Config.p("tex_modelo_max"))
        _asentar_en_suelo(visual, padre)
        return visual, None

    return _respaldo(padre, spec, escala)


def _respaldo(padre, spec, escala):
    """Primitiva del color del personaje, para cuando no hay modelo cargable."""
    visual = Entity(
        parent=padre,
        model=spec.get("respaldo", "cube"),
        color=spec.get("color", ucolor.gray),
        scale=Vec3(0.9, 1.4, 0.9) * escala,
        origin_y=-0.5,
    )
    return visual, None



def animar(actor, nombre, en_bucle=True):
    """
    Reproduce una animacion si el actor existe y la tiene.

    Los nombres de animacion que exporta Blender no siempre coinciden con
    los que se veian en el editor, por eso se consulta getAnimNames().
    """
    if actor is None or not hasattr(actor, "getAnimNames"):
        return False
    try:
        disponibles = actor.getAnimNames()
        if nombre not in disponibles:
            return False
        actor.loop(nombre) if en_bucle else actor.play(nombre)
        return True
    except Exception:
        return False


def listar_animaciones(clave):
    """Utilidad de depuracion: imprime las animaciones de un modelo."""
    ruta = ruta_modelo(clave)
    if not ruta or not ACTOR_DISPONIBLE:
        print(f"[recursos] {clave}: sin modelo cargable")
        return []
    try:
        a = Actor(_ruta_panda(ruta))
        nombres = a.getAnimNames()
        a.cleanup()
        print(f"[recursos] {clave}: {nombres}")
        return nombres
    except Exception as e:
        print(f"[recursos] {clave}: error {e}")
        return []


def faltantes():
    """Lista de claves cuyo modelo todavia no esta exportado."""
    return [k for k in MODELOS if ruta_modelo(k) is None]
