"""
datos.py — Datos del juego en un solo lugar: guardianes, jefes y objetos.

Separar los datos del codigo permite balancear el juego editando numeros
sin tocar la logica. En el dia 4 (balanceo) solo se toca este archivo.
"""

from ursina import color


# ---------------------------------------------------------------------
# REGISTRO DE MODELOS
# ---------------------------------------------------------------------
# 'carpeta' es la subcarpeta dentro de modelos/ y 'archivo' el .glb.
# Mientras no exista el archivo, el juego usa la primitiva de respaldo.
# Asi el proyecto corre desde el dia 1, sin esperar a los modelos.
MODELOS = {
    "sol":        dict(carpeta="sol",        archivo="sol.glb",        escala=1.0, respaldo="sphere", color=color.rgb32(230, 190, 90)),
    "fuego":      dict(carpeta="fuego",      archivo="fuego.glb",      escala=1.0, respaldo="sphere", color=color.rgb32(220, 110, 80)),
    "hielo":      dict(carpeta="hielo",      archivo="hielo.glb",      escala=1.0, respaldo="sphere", color=color.rgb32(150, 190, 215)),
    "naturaleza": dict(carpeta="naturaleza", archivo="naturaleza.glb", escala=1.0, respaldo="sphere", color=color.rgb32(130, 165, 100)),
    "vacio":      dict(carpeta="vacio",      archivo="vacio.glb",      escala=1.0, respaldo="sphere", color=color.rgb32(130, 115, 175)),
    "luna":       dict(carpeta="luna",       archivo="luna.glb",       escala=1.0, respaldo="sphere", color=color.rgb32(220, 220, 235)),

    "sol_jefe":        dict(carpeta="sol_jefe",        archivo="sol_jefe.glb",        escala=2.2, respaldo="cube", color=color.rgb32(200, 160, 70)),
    "fuego_jefe":      dict(carpeta="fuego_jefe",      archivo="fuego_jefe.glb",      escala=2.2, respaldo="cube", color=color.rgb32(190, 85, 60)),
    "hielo_jefe":      dict(carpeta="hielo_jefe",      archivo="hielo_jefe.glb",      escala=2.4, respaldo="cube", color=color.rgb32(120, 160, 190)),
    "naturaleza_jefe": dict(carpeta="naturaleza_jefe", archivo="naturaleza_jefe.glb", escala=2.4, respaldo="cube", color=color.rgb32(100, 135, 75)),
    "vacio_jefe":      dict(carpeta="vacio_jefe",      archivo="vacio_jefe.glb",      escala=2.6, respaldo="cube", color=color.rgb32(95, 80, 150)),

    "conejo":   dict(carpeta="conejo",   archivo="conejo.glb",   escala=2.0, respaldo="cube",   color=color.rgb32(190, 60, 60)),
    "mercader": dict(carpeta="mercader", archivo="mercader.glb", escala=1.2, respaldo="cube",   color=color.rgb32(150, 165, 110)),
    "fantasma": dict(carpeta="fantasma", archivo="fantasma.glb", escala=0.8, respaldo="sphere", color=color.rgb32(235, 235, 235)),
}


# ---------------------------------------------------------------------
# GUARDIANES JUGABLES
# ---------------------------------------------------------------------
GUARDIANES = {
    "sol": dict(
        nombre="Guardian del Sol", elemento="Luz",
        vida=110, dano=12, velocidad=7.0, cadencia=0.42,
        descripcion="Equilibrado. Buen punto de partida.",
    ),
    "fuego": dict(
        nombre="Guardian del Fuego", elemento="Fuego",
        vida=90, dano=15, velocidad=8.0, cadencia=0.30,
        descripcion="Rapido y fragil. Premia la agresividad.",
    ),
    "hielo": dict(
        nombre="Guardian del Hielo", elemento="Hielo",
        vida=140, dano=10, velocidad=5.8, cadencia=0.55,
        descripcion="Resistente y lento. Aguanta errores.",
    ),
    "naturaleza": dict(
        nombre="Guardian de la Naturaleza", elemento="Naturaleza",
        vida=125, dano=11, velocidad=6.5, cadencia=0.48,
        descripcion="Solido en todo, sin picos.",
    ),
    "vacio": dict(
        nombre="Guardian del Vacio", elemento="Vacio",
        vida=95, dano=14, velocidad=7.5, cadencia=0.36,
        descripcion="Alto dano, poco margen de error.",
    ),
    "luna": dict(
        nombre="Guardiana de la Luna", elemento="Luna",
        vida=105, dano=12, velocidad=7.2, cadencia=0.40,
        descripcion="Versatil. Recupera vida al cambiar de fase.",
    ),
}


# ---------------------------------------------------------------------
# JEFES  (orden de la campana)
# ---------------------------------------------------------------------
JEFES = [
    dict(clave="sol_jefe", nombre="Guardian del Sol", vida=260, dano=14,
         velocidad=3.2, telegrafiado=1.05, recuperacion=1.1, fases=2,
         patron="embestida", fragmentos=45,
         intro="El sol se apago primero. Devuelvelo a su ciclo."),
    dict(clave="fuego_jefe", nombre="Guardian del Fuego", vida=300, dano=12,
         velocidad=4.4, telegrafiado=0.70, recuperacion=1.5, fases=2,
         patron="rafaga", fragmentos=50,
         intro="Ataca en rafagas y se agota. Espera su respiro."),
    dict(clave="hielo_jefe", nombre="Guardian del Hielo", vida=420, dano=18,
         velocidad=2.4, telegrafiado=1.35, recuperacion=0.9, fases=3,
         patron="area", fragmentos=60,
         intro="Congela el suelo. El terreno importa mas que el reflejo."),
    dict(clave="naturaleza_jefe", nombre="Guardian de la Naturaleza", vida=380, dano=16,
         velocidad=3.0, telegrafiado=1.0, recuperacion=1.0, fases=3,
         patron="mixto", fragmentos=65,
         intro="Fragmenta el arena con raices. No dejes de moverte."),
    dict(clave="vacio_jefe", nombre="Guardian del Vacio", vida=440, dano=17,
         velocidad=3.8, telegrafiado=0.62, recuperacion=0.85, fases=3,
         patron="parpadeo", fragmentos=80,
         intro="Ve unos segundos hacia adelante. No lo mires: escuchalo."),
    dict(clave="conejo", nombre="El Experimento", vida=620, dano=19,
         velocidad=4.2, telegrafiado=0.75, recuperacion=0.8, fases=5,
         patron="final", fragmentos=0,
         intro="No es maldad. Es una fuga que nadie supo cerrar."),
]


# ---------------------------------------------------------------------
# OBJETOS DE LA TIENDA DEL MERCADER
# ---------------------------------------------------------------------
OBJETOS = [
    dict(id="brasa",   nombre="Reliquia de brasa",  costo=40, efecto="dano",     valor=4,
         desc="+4 de dano en cada hechizo"),
    dict(id="corteza", nombre="Corteza viva",       costo=35, efecto="vida_max", valor=25,
         desc="+25 de vida maxima"),
    dict(id="farol",   nombre="Farol de bolsillo",  costo=50, efecto="curar",    valor=60,
         desc="Recupera 60 de vida al entrar a cada combate"),
    dict(id="astilla", nombre="Astilla de vacio",   costo=60, efecto="velocidad", valor=1.2,
         desc="+1.2 de velocidad de movimiento"),
    dict(id="pulso",   nombre="Pulso estabilizador", costo=55, efecto="cadencia", valor=0.08,
         desc="Reduce el tiempo de recarga de hechizos"),
]


# ---------------------------------------------------------------------
# ARMAS CUERPO A CUERPO  (se cambian en combate con 1 / 2 / 3)
# ---------------------------------------------------------------------
# 'alcance'      = distancia a la que llega el golpe
# 'recuperacion' = segundos de bloqueo tras atacar (mayor = mas lento)
# 'pesado'       = multiplicador de dano del ataque pesado (clic derecho)
ARMAS = [
    dict(nombre="Espada",   dano=20, alcance=3.2, recuperacion=0.42, pesado=1.8),
    dict(nombre="Martillo", dano=32, alcance=3.4, recuperacion=0.72, pesado=2.1),
    dict(nombre="Dagas",    dano=13, alcance=2.4, recuperacion=0.26, pesado=1.6),
]


# ---------------------------------------------------------------------
# HECHIZOS A DISTANCIA  (gastan FP y tienen recarga; se cambian con 'e')
# ---------------------------------------------------------------------
# 'costo_fp' = FP que consume cada lanzamiento
# 'recarga'  = segundos hasta poder volver a lanzarlo
HECHIZOS = [
    dict(nombre="Proyectil", dano=24, costo_fp=14, recarga=0.8, velocidad=26),
    dict(nombre="Estallido", dano=46, costo_fp=34, recarga=2.4, velocidad=30),
]


# ---------------------------------------------------------------------
# DIALOGOS DE LA GUARDIANA DE LA LUNA (transiciones)
# ---------------------------------------------------------------------
TRANSICIONES = [
    "Uno menos. Todavia respira, solo esta cansado.",
    "El fuego siempre fue el que menos escuchaba. No lo persigas.",
    "El hielo tardara en descongelarse. Dale tiempo.",
    "El bosque estaba enfermo mucho antes de todo esto.",
    "El que sigue ya sabe que vas. Eso no lo hace mas fuerte.",
]
