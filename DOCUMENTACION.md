# Guardianes del Eclipse

### Documentación del Proyecto Final — Integración de Modelos 3D en Videojuegos

| | |
|---|---|
| **Nombre del juego** | Guardianes del Eclipse |
| **Materia** | Graficación |
| **Grupo** | XC |
| **Docente** | Amairani Sarai Jimenez Arroyo |
| **Fecha de entrega** | *(completar: día de entrega)* |
| **Modalidad** | Opción A — Juego 3D |
| **Motor** | Ursina Engine (Python) sobre Panda3D |
| **Repositorio** | https://github.com/vesseldot/guardianes-del-eclipse |

### Integrantes del equipo

> ⚠️ **PENDIENTE DE COMPLETAR POR EL EQUIPO.** Se listan los usuarios de GitHub
> que han colaborado en el repositorio. Cada integrante debe sustituir su usuario
> por su **nombre completo y número de control**, y confirmar **qué personaje 3D
> creó** (esto vale el 35% de la rúbrica).

| Nombre completo | No. de control | Usuario de GitHub | Personaje 3D creado | Rol en el juego |
|---|---|---|---|---|
| *(completar)* | *(completar)* | `vesseldot` | *(completar)* | *(Player / NPC / Jefe)* |
| *(completar)* | *(completar)* | `AlexMau89` | *(completar)* | *(Player / NPC / Jefe)* |
| *(completar)* | *(completar)* | `danxklk` | *(completar)* | *(Player / NPC / Jefe)* |
| *(completar)* | *(completar)* | `HRHerson02` | *(completar)* | *(Player / NPC / Jefe)* |

---

## 1. Información sobre el juego

### 1.1 Descripción general

**Guardianes del Eclipse** es un juego de acción en tercera persona con estructura
de *boss-rush* (sucesión de combates contra jefes), inspirado en el sistema de
combate de la saga *Souls*. El jugador elige a uno de los seis Guardianes
elementales y debe enfrentarse, uno tras otro, al resto de Guardianes que han sido
corrompidos por una falla en el dispositivo que sostiene el equilibrio del mundo.

**Objetivo del juego:** derrotar a los cinco Guardianes corrompidos y, finalmente,
al Experimento, para restaurar el equilibrio. Entre combate y combate se visita al
Mercader, donde los *fragmentos* obtenidos permiten comprar mejoras permanentes.

**Género:** Acción / Boss-rush 3D
**Perspectiva:** Tercera persona con cámara orbital y fijado de objetivo (*lock-on*)

### 1.2 Premisa narrativa

El mundo se sostiene sobre un dispositivo que regula los ciclos naturales: el día y
la noche, las estaciones, el calor y el frío. Cada ciclo está a cargo de un
**Guardián**. Cuando el dispositivo empieza a fallar, los Guardianes son los
primeros en romperse: la corrupción los desborda y quedan atrapados en su propia
función, incapaces de detenerse.

El jugador es el único Guardián que resiste. No sale a matar a sus compañeros, sino
a **liberarlos**: cada combate termina con el Guardián derrotado devuelto a su
ciclo, no destruido. La Guardiana de la Luna acompaña al jugador entre combates,
comentando lo que ocurre.

El desenlace no plantea un villano: **El Experimento** es una fuga del propio
dispositivo, un error que nadie supo cerrar a tiempo. El final del juego es la
restauración del equilibrio, no una victoria sobre un enemigo.

> *"No es maldad. Es una fuga que nadie supo cerrar."* — intro del jefe final

### 1.3 Unificación del estilo visual (el reto del proyecto)

Cada integrante del equipo modeló su personaje con un estilo propio, por lo que el
juego necesita un marco que los haga convivir. La estrategia elegida combina dos de
las técnicas propuestas:

**a) Unificación por narrativa — "Guardianes de distintos ciclos".**
La premisa justifica la diferencia visual: cada Guardián encarna un ciclo distinto
del mundo (Sol, Fuego, Hielo, Naturaleza, Vacío, Luna). Que un Guardián sea más
realista y otro más estilizado se lee como parte de su naturaleza elemental, no
como una inconsistencia. La corrupción es el hilo que los une a todos.

**b) Unificación por entorno — "arena neutra".**
Todos los combates ocurren en la misma **arena circular de piedra**, con una
paleta deliberadamente apagada (gris-piedra) bajo un cielo nocturno. Este fondo
neutro y consistente actúa como el "hub central" que menciona la guía: hace que los
personajes destaquen por encima del escenario, sin competir entre sí.

Técnicamente esta unificación se refuerza con:

- **Iluminación común:** todos los modelos se sombrean con el mismo pipeline PBR
  (`simplepbr`) y el mismo esquema de tres luces (principal, ambiental y relleno),
  lo que homogeneiza el aspecto de materiales creados por separado.
- **Interfaz de una sola pieza:** las siete pantallas comparten paleta, tipografía
  y un arte de fondo generado con el mismo prompt de estilo (ver `ARTE_UI.md`), de
  modo que el marco alrededor de los personajes siempre es el mismo.
- **Escala normalizada:** cada modelo tiene un factor de `escala` en `datos.py` para
  que las proporciones sean coherentes sin importar cómo se exportó cada uno. En el
  juego un Guardián mide ~1.7 unidades, un jefe ~4 y un fantasma ~1.3.
- **Sincronización de animación y movimiento:** los clips vienen con cadencia fija,
  así que su ritmo de reproducción se ajusta a la velocidad real de cada personaje
  para que ninguno "patine" (ver §2.5).

### 1.4 Personajes

#### Guardianes jugables

Los seis Guardianes son seleccionables al inicio. Sus estadísticas están definidas
en `datos.py` (diccionario `GUARDIANES`):

| Guardián | Elemento | Vida | Daño | Velocidad | Perfil de juego |
|---|---|---|---|---|---|
| Guardián del Sol | Luz | 110 | 12 | 7.0 | Equilibrado. Buen punto de partida |
| Guardián del Fuego | Fuego | 90 | 15 | 8.0 | Rápido y frágil. Premia la agresividad |
| Guardián del Hielo | Hielo | 140 | 10 | 5.8 | Resistente y lento. Aguanta errores |
| Guardián de la Naturaleza | Naturaleza | 125 | 11 | 6.5 | Sólido en todo, sin picos |
| Guardián del Vacío | Vacío | 95 | 14 | 7.5 | Alto daño, poco margen de error |
| Guardiana de la Luna | Luna | 105 | 12 | 7.2 | Versátil. Recupera vida al cambiar de fase |

**Historia de cada Guardián:**

- **Guardián del Sol.** Encargado del ciclo del día. Fue el primero en apagarse
  cuando el dispositivo falló, y por eso es también el primer combate de la
  campaña. Su corrupción lo dejó atrapado embistiendo hacia adelante, sin poder
  detenerse.
- **Guardián del Fuego.** El más impulsivo del grupo; según la Guardiana de la
  Luna, *"siempre fue el que menos escuchaba"*. Corrompido, ataca en ráfagas
  hasta agotarse, dejando una ventana de respiro entre andanadas.
- **Guardián del Hielo.** El más lento y resistente. Su corrupción congela el
  suelo de la arena: contra él importa más el control del terreno que la velocidad
  de reacción.
- **Guardián de la Naturaleza.** Responsable del bosque, que *"estaba enfermo mucho
  antes de todo esto"*. Fragmenta la arena con raíces, obligando al jugador a no
  quedarse quieto.
- **Guardián del Vacío.** El más inquietante: percibe unos segundos hacia el
  futuro. Su patrón de parpadeo hace que perseguirlo con la vista sea inútil.
- **Guardiana de la Luna.** La única que conserva la lucidez. Acompaña al jugador
  entre combates con los diálogos de transición y actúa como guía narrativa.

#### Jefes (orden de la campaña)

Definidos en `datos.py` (lista `JEFES`), en este orden:

| # | Jefe | Vida | Daño | Fases | Patrón de ataque | Fragmentos |
|---|---|---|---|---|---|---|
| 1 | Guardián del Sol | 260 | 14 | 2 | Embestida | 45 |
| 2 | Guardián del Fuego | 300 | 12 | 2 | Ráfaga | 50 |
| 3 | Guardián del Hielo | 420 | 18 | 3 | Área | 60 |
| 4 | Guardián de la Naturaleza | 380 | 16 | 3 | Mixto | 65 |
| 5 | Guardián del Vacío | 440 | 17 | 3 | Parpadeo | 80 |
| 6 | **El Experimento** (final) | 620 | 19 | 5 | Final | — |

#### Enemigos menores — los Fantasmas

Implementados en `fantasma.py`. Son el **enjambre que invoca el jefe final**: no
aparecen en ningún otro combate.

| Vida | Daño | Velocidad | Rango de golpe |
|---|---|---|---|
| 18 | 6 | 3.6 | 1.7 |

Tienen su propia máquina de estados, más simple que la de un jefe
(`PERSEGUIR → TELEGRAFIAR → RECUPERAR`): corren hacia el jugador y muerden de
cerca. El Experimento invoca **2 oleadas de 2 fantasmas**; al despejar la primera,
vuelve a conjurar (ver §1.5).

#### NPCs

- **El Mercader.** Comerciante que aparece entre combates. Vende cinco mejoras
  permanentes a cambio de los fragmentos obtenidos al liberar a cada Guardián.
- **El Experimento.** Jefe final. No es un enemigo con voluntad propia, sino la
  fuga del dispositivo hecha forma.

### 1.5 Mecánicas de juego

El combate sigue el modelo *Souls*: recursos limitados, ataques con tiempo de
recuperación y lectura de los avisos del enemigo.

**Recursos del jugador**
- **Vida:** depende del Guardián elegido.
- **Estamina:** se gasta al rodar (34) y al correr (22/s); se regenera tras una
  pausa de 0.45 s.
- **FP (puntos de foco):** consumidos por los hechizos; se regeneran lentamente (5/s).
- **Frascos:** 4 curaciones por combate, cada una restaura el 45 % de la vida
  máxima. Beber deja al jugador vulnerable 0.65 s.

**Acciones**
- **Ataque ligero / pesado** con el arma equipada. El pesado tarda más pero
  multiplica el daño. El gesto del brazo dura exactamente lo que el arma bloquea
  al personaje, así que el martillo golpea despacio y la espada rápido.
- **Rodar (esquiva)** con 0.28 s de invulnerabilidad real (*i-frames*).
- **Hechizos a distancia**, con coste de FP y recarga.
- **Fijado de objetivo (*lock-on*)**: la cámara encuadra al jefe y el personaje lo
  encara automáticamente.

**Armas** (se cambian con `1` `2` `3`)

Cada arma tiene su propio modelo 3D, que se cuelga de la mano derecha del
personaje al equiparla (ver §2.4).

| Arma | Daño | Alcance | Recuperación | Multiplicador pesado |
|---|---|---|---|---|
| Espada | 20 | 3.2 | 0.42 s | ×1.8 |
| Martillo | 32 | 3.4 | 0.72 s | ×2.1 |
| Hacha | 26 | 3.0 | 0.58 s | ×1.9 |

**Hechizos** (se cambian con `E`)

| Hechizo | Daño | Coste FP | Recarga | Velocidad |
|---|---|---|---|---|
| Proyectil | 24 | 14 | 0.8 s | 26 |
| Estallido | 46 | 34 | 2.4 s | 30 |

**Tienda del Mercader**

| Objeto | Costo | Efecto |
|---|---|---|
| Reliquia de brasa | 40 | +4 de daño en cada hechizo |
| Corteza viva | 35 | +25 de vida máxima |
| Farol de bolsillo | 50 | Recupera 60 de vida al entrar a cada combate |
| Astilla de vacío | 60 | +1.2 de velocidad de movimiento |
| Pulso estabilizador | 55 | Reduce el tiempo de recarga de hechizos |

**Ciclo de combate del jefe.** Cada jefe recorre una máquina de estados diseñada
para que el combate sea **legible**:

```
PERSEGUIR → TELEGRAFIAR → ATACAR → RECUPERAR → (vuelta a PERSEGUIR)
```

El estado `TELEGRAFIAR` es la clave del diseño: el jefe se detiene y **cambia de
color** antes de golpear, dando al jugador la ventana para esquivar. A medida que
pierde vida, el jefe **sube de fase**: gana un 15 % de velocidad y reduce sus
tiempos de aviso y recuperación, endureciendo el combate progresivamente. El estado
`ATACAR` dura lo que dura el clip de animación, para que el golpe se vea completo.

El jefe final añade un quinto estado, **`INVOCANDO`**: se queda quieto ejecutando su
animación de conjuro (`Charged_Spell_Cast`) y, al 60 % del gesto, aparecen los
fantasmas. Es la ventana en la que el jugador ve venir la oleada.

### 1.6 Controles

| Tecla / Ratón | Acción |
|---|---|
| *(cualquier tecla)* | Entrar desde la pantalla de título |
| `WASD` | Moverse (relativo a la cámara) |
| `Shift` | Correr (gasta estamina) |
| `Ratón` | Orbitar la cámara |
| `Rueda del ratón` | Acercar / alejar la cámara |
| `Clic izq.` | Ataque ligero |
| `Clic der.` | Ataque pesado |
| `Espacio` | Rodar / esquivar (*i-frames*) |
| `Q` | Lanzar hechizo |
| `E` | Cambiar de hechizo |
| `R` | Beber frasco |
| `F` | Fijar / soltar objetivo (*lock-on*) |
| `1` `2` `3` | Cambiar de arma |
| `Esc` | Pausar el combate / volver atrás en los menús |

---

## 2. Descripción técnica

### 2.1 Tecnologías utilizadas

| Componente | Tecnología | Función |
|---|---|---|
| Motor | **Ursina Engine** | Capa de alto nivel: entidades, escena, entrada |
| Base gráfica | **Panda3D** | Renderizado, carga de modelos, `Actor` para animación |
| Pipeline de materiales | **simplepbr** | Iluminación PBR de los modelos `.glb` |
| Carga de modelos | **panda3d-gltf** | Importación de archivos glTF/GLB |
| Lenguaje | **Python 3.11** | — |
| Control de versiones | **Git + GitHub** | Trabajo colaborativo del equipo |

Instalación y ejecución:

```bash
pip install ursina panda3d-gltf simplepbr
python main.py
```

El juego arranca en **pantalla completa** a la resolución nativa del monitor. Para
desarrollar en ventana basta con poner `PANTALLA_COMPLETA = False` en `config.py`.

### 2.2 Arquitectura del código

El proyecto está **modularizado por responsabilidad**: cada archivo resuelve un
aspecto del juego y puede modificarse sin tocar los demás. Esta separación permitió
que varios integrantes trabajaran en paralelo sobre el mismo repositorio.

```
guardianes/
├── main.py                    → Punto de entrada y máquina de estados del juego
├── config.py                  → Presets de calidad y monitor de rendimiento
├── datos.py                   → Estadísticas de guardianes, jefes, armas y objetos
├── recursos.py                → Carga de modelos 3D con respaldo automático
├── entorno.py                 → Texturas del entorno y reducción de texturas
├── jugador.py                 → Guardián controlable, combate y cámara
├── jefe.py                    → IA de los jefes (máquina de estados)
├── fantasma.py                → Enemigo menor invocado por el jefe final
├── movimientos_personaje.py   → Animación de locomoción, golpe y armas equipables
├── sonido.py                  → Música por estado y efectos de sonido
├── proyectiles.py             → Pool de proyectiles (hechizos)
├── interfaz.py                → HUD y las siete pantallas de UI
├── vitrina.py                 → Escaparate 3D giratorio para los modelos
├── modelos/                   → Modelos 3D .glb (personajes y armas)
├── texturas/                  → Suelo de la arena y cielo nocturno
└── assets/
    ├── music/                 → 6 pistas
    ├── sounds/                → 13 efectos
    └── ui/                    → Fondos y logo de las pantallas
```

**Diagrama de dependencias** (las flechas indican "usa a"):

```
                            main.py
     ┌─────────┬─────────┬─────┼──────┬──────────┬───────────┐
     ▼         ▼         ▼     ▼      ▼          ▼           ▼
 jugador.py  jefe.py  fantasma  interfaz  vitrina  proyectiles  sonido
     │         │         │        │         │          │         │
     ▼         │         │        │         │          │         │
movimientos ───┴─────────┴────────┼─────────┴──────────┘         │
     │                            │                              │
     └──────────┬─────────────────┴──────────────┬───────────────┘
                ▼                                ▼
           recursos.py ─────► entorno.py     datos.py
                │                 │              │
                └─────────────────┴──────────────┴──► config.py
```

`datos.py` y `config.py` son las **hojas** del árbol: no dependen de nadie, por lo
que balancear el juego o ajustar el rendimiento nunca rompe la lógica.

### 2.3 Clases principales

#### `Juego` (`main.py`)

Clase central que orquesta todo. Implementa una **máquina de estados** con nueve
estados: `TITULO`, `MENU`, `SELECCION`, `INSTRUCCIONES`, `COMBATE`, `PAUSA`,
`TIENDA`, `TRANSICION` y `FIN`.

| Método | Responsabilidad |
|---|---|
| `_construir_escenario()` | Crea suelo, borde, cielo y las tres luces |
| `_aplicar_calidad()` | Aplica el preset de calidad (sombras, PBR, texturas, luces) |
| `_ir_a(estado)` | Transición de estado: activa/desactiva pantallas y mundo |
| `actualizar(dt)` | **Único bucle de actualización** de todo el juego |
| `_mover_proyectiles(dt)` | Movimiento y colisión de todos los proyectiles activos |
| `_empezar_oleada()` | Lanza el conjuro del jefe final que invoca fantasmas |
| `_pausar()` / `_reanudar()` | Congela y reanuda el combate sin destruir su estado |
| `tecla(key)` | Enruta la entrada según el estado activo |

#### `Jugador(Entity)` (`jugador.py`)

Hereda de `Entity` de Ursina. Encapsula el personaje controlable: recursos de
combate, acciones y la cámara en tercera persona.

| Método | Responsabilidad |
|---|---|
| `actualizar(dt, objetivo, otros_objetivos)` | Movimiento, temporizadores, animación y cámara |
| `atacar(pesado)` | Ataque melee con retardo de impacto (*windup*) |
| `esquivar()` | Rodar con *i-frames*; consume estamina |
| `lanzar_hechizo(...)` | Pide un proyectil al pool; consume FP |
| `curar_frasco()` | Consume un frasco y restaura vida |
| `elegir_arma(i)` | Cambia de arma y recoloca su modelo 3D en la mano |
| `_orbitar_camara(dt)` | Cámara orbital amortiguada, con *lock-on* y zoom |
| `aplicar_objeto(objeto)` | Aplica una mejora comprada en la tienda |

#### `Jefe(Entity)` (`jefe.py`)

Hereda de `Entity`. Implementa la IA mediante la máquina de estados descrita
en §1.5.

| Método | Responsabilidad |
|---|---|
| `actualizar(dt, jugador)` | Ejecuta el estado actual de la IA |
| `_perseguir(...)` | Avanza hacia el jugador y lo encara |
| `_telegrafiar(...)` | Se detiene y cambia de color: aviso al jugador |
| `_atacar(...)` | Ejecuta golpe de área, ráfaga de proyectiles o combo |
| `invocar()` | Conjuro del jefe final que hace aparecer una oleada |
| `_anim_desplazamiento()` | Elige clip y ritmo según la velocidad real |
| `recibir_dano(cantidad)` | Aplica daño y comprueba el cambio de fase |
| `_subir_fase(nueva)` | Aumenta velocidad y reduce tiempos de aviso |

#### `Fantasma(Entity)` (`fantasma.py`)

Enemigo menor con tres estados propios. No tiene fases ni hechizos: persigue
corriendo y muerde de cerca. El jugador puede golpearlo con el arma equipada
(`Jugador.actualizar` recibe la lista en `otros_objetivos`).

#### `MovimientoPersonaje` (`movimientos_personaje.py`)

Decide **cómo se ve** un personaje, sin tocar su lógica. Reproduce `Walking` o
`Running` según se mueva, y anima a mano el brazo derecho para el golpe cuerpo a
cuerpo controlando los huesos `RightArm`, `RightForeArm` y `RightHand`. También
cuelga de la mano el `.glb` del arma equipada.

Si el modelo no trae esos huesos, la clase queda desactivada y todos sus métodos
no hacen nada: nunca rompe al llamador.

#### `GestorSonido` (`sonido.py`)

Gestor centralizado de audio: **una música activa** que cambia según el estado del
juego (menú, tienda, tres pistas de combate y una para el jefe final) y **efectos
solapables** para ataques, esquiva, curación y muerte. Las pistas se precargan al
inicio para no leer disco en mitad del combate.

#### `Proyectil(Entity)` y `PoolProyectiles` (`proyectiles.py`)

Sistema de **Object Pooling**. Los proyectiles se crean una sola vez al inicio y
después solo se activan y desactivan, evitando por completo la creación y
destrucción de entidades durante el combate.

| Método | Responsabilidad |
|---|---|
| `PoolProyectiles.pedir()` | Devuelve un proyectil libre (o `None` si no hay) |
| `PoolProyectiles.activos()` | Generador de los proyectiles en uso |
| `PoolProyectiles.redimensionar(n)` | Ajusta el tamaño del pool según la calidad |
| `Proyectil.lanzar(...)` | Reinicia y activa un proyectil |
| `Proyectil.avanzar(dt)` | Movimiento manual, sin `update()` propio |

#### `Config` y `MonitorRendimiento` (`config.py`)

`Config` guarda el estado de configuración y expone los presets de calidad.
`MonitorRendimiento` vigila los FPS y **baja la calidad automáticamente** si el
promedio cae por debajo de 28 FPS durante 2.5 segundos, respetando la elección del
usuario si este la fijó manualmente.

#### Clases de interfaz (`interfaz.py`)

Todas heredan de una clase base `Pantalla` y siguen el mismo contrato
(`mostrar()` / `ocultar()`), lo que permite a `Juego._ir_a()` gestionarlas de forma
uniforme:

| Clase | Pantalla |
|---|---|
| `PantallaTitulo` | Portada con el emblema y "pulsa cualquier tecla" |
| `MenuPrincipal` | Jugar, Calidad y Salir |
| `SeleccionGuardian` | Elección de personaje, con el modelo en la vitrina |
| `Instrucciones` | Resumen de controles antes del primer combate |
| `HUD` | Barras y textos durante el combate |
| `PantallaPausa` | Combate congelado: Continuar, Calidad y Abandonar |
| `Tienda` | Compra de mejoras entre combates |
| `PantallaMensaje` | Transiciones narrativas, victoria y derrota |

Cada pantalla lleva su propia imagen de fondo a pantalla completa. Como la capa de
UI se dibuja **encima** de la escena 3D, las pantallas que muestran un modelo
(selección y tienda) usan imágenes con **media zona transparente** para que el
personaje se vea por detrás.

#### `Vitrina` (`vitrina.py`)

Escaparate 3D que muestra el modelo del personaje girando lentamente en la pantalla
de selección y en la tienda. Cumple el requisito de **Avatar / Selector** de la
rúbrica: cada personaje del equipo aparece con su modelo 3D en el menú.

### 2.4 Integración de los modelos 3D

Los modelos se exportan desde Blender / Meshy.ai en formato **`.glb`** (geometría +
texturas + animaciones en un solo archivo) y se registran en el diccionario
`MODELOS` de `datos.py`:

```python
"sol": dict(carpeta="sol", archivo="sol.glb", escala=1.0,
            respaldo="sphere", color=color.rgb32(230, 190, 90)),
```

**Decisión técnica clave — sistema de respaldo automático.**
`recursos.py` implementa una carga tolerante a fallos en cascada:

1. Se intenta cargar como `Actor` de Panda3D, que conserva las animaciones.
2. Si falla, se reintenta con el **skinning simplificado** (ver más abajo).
3. Si vuelve a fallar, se carga como malla estática, sin esqueleto.
4. Como último recurso, se dibuja una **primitiva del color del personaje**.

Esto permitió al equipo programar y probar el juego **desde el primer día**, sin
esperar a que el modelado estuviera terminado.

**Armas equipables.** Las tres armas son modelos aparte que no pertenecen al rig de
ningún personaje. `MovimientoPersonaje` las cuelga del hueso `RightHand`, con
posición, rotación y escala calibradas por arma. Se precargan al crear el personaje
y quedan en caché, de modo que cambiar de arma en combate solo enciende una entidad
y apaga otra.

**Problemas resueltos durante la integración:**

| Problema | Solución aplicada |
|---|---|
| Rutas con acentos (`Graficación`) rompían el cargador | Conversión con `Filename.from_os_specific()` |
| Modelos medio enterrados en el suelo | `_asentar_en_suelo()` mide los límites reales y eleva el modelo |
| Modelos caminando de espaldas | Constante `FRENTE_MODELO = 180°`: los `.glb` se exportan mirando a −Z |
| Nombres de animación distintos a los de Blender | `animar()` consulta `getAnimNames()` antes de reproducir |
| Modelos planos y blancos | Inicialización de `simplepbr` para el sombreado PBR |
| Un modelo denso no cargaba (`AssertionError`) | Skinning simplificado: ver abajo |
| Las animaciones de ataque se cortaban a un tercio | El estado `ATACAR` dura lo que dura el clip, medido con `getDuration()` |
| Los personajes "patinaban" al correr | El ritmo del clip se ajusta a la velocidad real de cada uno |

**El caso del Fantasma — límite de mezclas de huesos.**
`panda3d-gltf` guarda el índice de mezcla de huesos de cada vértice en una columna
de **16 bits**. El modelo del fantasma tiene **158 798 vértices** con pesos en coma
flotante, así que prácticamente cada vértice generaba una mezcla distinta y se
superaba el límite de 65 535, abortando la carga.

La solución fue **redondear los pesos a 64 escalones** y renormalizarlos antes de
construir la tabla: miles de vértices pasan a compartir la misma mezcla, la tabla
baja del límite y el modelo conserva su esqueleto y sus animaciones. La deformación
pierde algo de precisión, inapreciable al tamaño en que se ve en pantalla.

### 2.5 Optimización (calidad técnica de assets)

El proyecto se diseñó para correr en equipos de gama baja, incluidos los de
gráficos integrados.

**Optimización de CPU**
- **Object Pooling** de proyectiles: cero asignaciones de memoria por disparo.
- **Un único `update()` global** en vez de uno por entidad: Ursina descubre los
  `update()` por reflexión y cada uno tiene un coste fijo por fotograma.
- **Colisiones por distancia al cuadrado**, sin colisionadores físicos de Panda3D y
  sin raíz cuadrada. Es más barato que un `collider` primitivo.
- **HUD con comprobación de cambios**: los textos solo se reescriben cuando su
  valor cambia, porque asignar `.text` regenera la geometría del texto.
- **Una sola escena** que se activa y desactiva por secciones; el nivel nunca se
  recarga.
- **Modelos y armas en caché**: se cargan una vez y se reutilizan entre combates.

**El cuello de botella real: las texturas de 8K**

Los modelos exportados desde Meshy traen mapas de **8192 × 8192 píxeles**, que
ocupan **~340 MB de VRAM cada uno**. En combate hay jugador, arma y jefe a la vez:
más de **1.9 GB**, con lo que una tarjeta integrada de 512 MB abortaba con
*"requested more GPU memory than is available"*.

No se puede resolver con la configuración de Panda3D (`max-texture-dimension`,
`texture-scale`): el cargador de glTF construye las texturas directamente desde los
buffers embebidos y se salta ese camino. La solución fue **reescalarlas al cargar el
modelo y antes del primer dibujado**, que es cuando se reserva la VRAM.

| Escenario de combate | VRAM antes | VRAM después |
|---|---|---|
| Preset bajo | ~1.9 GB | **13 MB** |
| Preset medio | ~1.9 GB | **53 MB** |
| Preset alto | ~1.9 GB | **213 MB** |

**Escalado de GPU por preset**

Tres presets (`bajo`, `medio`, `alto`) que escalan los costes reales de la tarjeta:

| Parámetro | bajo | medio | alto |
|---|---|---|---|
| Resolución de texturas de los modelos | 512 px | 1024 px | 2048 px |
| Resolución textura del suelo | 1K | 2K | 4K |
| MSAA del pipeline PBR | 0 | 0 | 4 |
| Normal / occlusion maps | ✗ | ✗ | ✓ |
| Máximo de luces (PBR) | 2 | 3 | 4 |
| Filtrado anisotrópico | 1× | 4× | 16× |
| Sombras dinámicas | ✗ | ✗ | ✓ |
| Luz de relleno | ✗ | ✓ | ✓ |
| Tamaño del pool de proyectiles | 14 | 24 | 40 |
| Distancia de dibujado | 45 | 80 | 140 |

El MSAA, los *normal maps*, el número de luces y el filtrado anisotrópico se
ajustan **en caliente** al cambiar de calidad, sin reiniciar el juego.

**Calidad adaptativa.** Si los FPS promedio caen por debajo de 28 durante 2.5
segundos, el juego baja un nivel de calidad automáticamente. Si el usuario elige la
calidad manualmente desde el menú, se respeta su elección.

**Nota sobre equipos con gráficos híbridos.** En portátiles con GPU integrada y
dedicada, Windows puede ejecutar el juego en la integrada. Como Panda3D usa OpenGL,
la forma fiable de forzar la dedicada es el Panel de Control de NVIDIA →
*Administrar configuración 3D* → *Configuración de programa* → añadir `python.exe`
→ *Procesador NVIDIA de alto rendimiento*.

### 2.6 Trabajo colaborativo

El proyecto se gestionó con **Git y GitHub**, con los cuatro integrantes como
colaboradores del repositorio. La modularización descrita en §2.2 fue lo que
permitió trabajar en paralelo minimizando conflictos: los archivos de datos
(`datos.py`), audio (`assets/`) y lógica están separados.

> **Nota sobre el repositorio.** Los modelos `.glb` (~2.6 GB en total) no se
> versionan en GitHub porque varios superan el límite de 100 MB por archivo. Se
> entregan dentro del proyecto comprimido. Gracias al sistema de respaldo
> automático (§2.4), el repositorio sigue siendo ejecutable sin ellos.

---

## 3. Capturas de pantalla del juego

> ⚠️ **PENDIENTE DE COMPLETAR POR EL EQUIPO.** Insertar las capturas reales y
> ajustar las descripciones. Se propone la siguiente selección, que cubre todas las
> pantallas del juego y **demuestra que los personajes de todos los integrantes
> aparecen** (35% de la rúbrica).

### 3.1 Pantalla de título

`(insertar captura)`

**Descripción:** Portada con el emblema del eclipse sobre el coliseo en ruinas, y el
aviso de "pulsa cualquier tecla" que late suavemente. Es la primera pantalla al
ejecutar el juego.

### 3.2 Menú principal

`(insertar captura)`

**Descripción:** Opciones de Jugar, Calidad y Salir sobre el mismo arte de fondo. El
botón de calidad permite alternar manualmente entre los presets `bajo`, `medio` y
`alto` descritos en §2.5.

### 3.3 Selección de Guardián

`(insertar captura)`

**Descripción:** Pantalla donde se elige el Guardián jugable. Al situar el cursor
sobre cada nombre, la **Vitrina 3D** (§2.3) muestra el modelo del personaje girando
sobre su eje, junto con sus estadísticas. Aquí se aprecian los modelos creados por
cada integrante del equipo, cumpliendo el requisito de *Avatar / Selector*.

### 3.4 Combate contra un jefe

`(insertar captura)`

**Descripción:** Vista principal de juego. Se observan el HUD del jugador (barras
de vida, estamina y FP, frascos, arma y hechizo equipados), la barra de vida del
jefe en la parte inferior y el indicador de objetivo fijado. El escenario es la
arena circular de piedra bajo el cielo nocturno descrita en §1.3.

### 3.5 Aviso de ataque del jefe (telegrafiado)

`(insertar captura)`

**Descripción:** Momento en que el jefe entra en el estado `TELEGRAFIAR`: se
detiene y **cambia de color** para avisar del ataque inminente. Esta es la ventana
de reacción que hace legible el combate (§1.5).

### 3.6 Pantalla de pausa

`(insertar captura)`

**Descripción:** Con `Esc` el combate se congela tras un velo oscuro, sin perder la
partida: se puede continuar, cambiar la calidad o abandonar. La escena sigue
visible por detrás.

### 3.7 Tienda del Mercader

`(insertar captura)`

**Descripción:** Entre combates, el jugador visita al Mercader (NPC) para gastar
los fragmentos obtenidos en mejoras permanentes. El modelo del Mercader se muestra
en la Vitrina 3D junto al listado de objetos disponibles.

### 3.8 Transición narrativa

`(insertar captura)`

**Descripción:** Pantalla de diálogo tras liberar a un Guardián, con los comentarios
de la Guardiana de la Luna que hilan la narrativa entre combates.

### 3.9 Jefe final — El Experimento y su oleada

`(insertar captura)`

**Descripción:** Combate final contra El Experimento, el jefe con más vida (620) y
más fases (5). Conviene capturar el momento en que ejecuta su conjuro y aparecen
los fantasmas a su alrededor.

### 3.10 Capturas del proceso

`(insertar capturas del modelado en Blender / Meshy.ai)`

**Descripción:** *(completar: proceso de modelado, texturizado y exportación de los
personajes a `.glb`)*

---

## 4. Conclusiones individuales

> ⚠️ **PENDIENTE DE COMPLETAR POR CADA INTEGRANTE.** Cada uno debe escribir su
> propia conclusión (se sugieren 100–150 palabras). Puntos que conviene tocar: qué
> parte del proyecto desarrollaste, qué dificultad técnica enfrentaste y cómo la
> resolviste, y qué aprendiste sobre integración de modelos 3D en un motor.

### *(Nombre del integrante 1)*

*(completar)*

### *(Nombre del integrante 2)*

*(completar)*

### *(Nombre del integrante 3)*

*(completar)*

### *(Nombre del integrante 4)*

*(completar)*

---

## Anexo: verificación de la rúbrica

| Criterio | Valor | Dónde se cubre | Estado |
|---|---|---|---|
| Integración de personajes del equipo | 35% | §1.4 personajes, §3.3 selector, §2.4 integración | ⚠️ Falta asignar cada personaje a su autor |
| Calidad técnica de assets | 25% | §2.4 integración, §2.5 optimización | ✅ Documentado |
| Gameplay y mecánicas | 25% | §1.1 objetivo, §1.5 mecánicas, §1.6 controles | ✅ Documentado |
| Documentación y proceso | 15% | Documento completo, §2 decisiones técnicas | ⚠️ Faltan capturas y conclusiones |

**Entregables:**
- [ ] Documentación en PDF (exportar este documento)
- [ ] Proyecto comprimido (incluir la carpeta `modelos/` con los `.glb`, y
      **excluir** la carpeta oculta `.git/`)
- [ ] Subida por **un solo** integrante del equipo
