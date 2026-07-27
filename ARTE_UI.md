# Arte de la interfaz — instrucciones de generación

> **Qué es este documento.** El registro de las **instrucciones (prompts) que se
> usaron para generar el arte de las pantallas del juego** con IA generativa
> (Gemini), junto con las especificaciones técnicas que ese arte tenía que
> cumplir para encajar en el motor.
>
> Las imágenes resultantes están en `assets/ui/` y son las que se ven en el
> juego. Se conserva este documento para dejar constancia del proceso y para
> poder regenerar o ampliar el arte manteniendo el mismo estilo.

Estilo de referencia: **dark fantasy sobrio** al estilo *Elden Ring* / *Dark
Souls* — dorado envejecido sobre negro, filigrana heráldica, viñeteado fuerte,
paleta desaturada, pintura al óleo digital.

**Imágenes generadas y en uso:**

| Archivo | Pantalla |
|---|---|
| `logo.png` | Emblema del título |
| `menu.png` | Portada y menú principal |
| `instrucciones.png` | Pantalla de controles |
| `seleccion.png` | Selección de guardián |
| `tienda.png` | Puesto del mercader |
| `transicion.png` | Diálogos entre combates |
| `final.png` | Pantalla de victoria y derrota |

---

## 1. Especificaciones técnicas (las que tuvo que cumplir el arte)

El juego usa Ursina. Su capa de interfaz (`camera.ui`) se dibuja **encima** de
la escena 3D, con estas coordenadas:

- Alto: de `y = -0.5` (abajo) a `y = +0.5` (arriba)
- Ancho: de `x = -0.889` (izquierda) a `x = +0.889` (derecha)
- Relación de aspecto: **16:9**

Consecuencia importante: **un fondo opaco a pantalla completa tapa los modelos
3D**. En Selección y Tienda el modelo del personaje se muestra en el escaparate
3D, así que ahí la imagen debe llevar **zona transparente**.

| Pantalla | Tipo de imagen | Formato | Tamaño | Zona que debe quedar libre |
|---|---|---|---|---|
| Menú principal | Fondo completo | JPG | 1920×1080 | Franja central (texto y botones en `x≈0`) |
| Instrucciones | Fondo completo | JPG | 1920×1080 | Centro (dos columnas de texto) |
| Selección de guardián | Fondo + marco | **PNG** | 1920×1080 | **Mitad derecha transparente** (modelo 3D) |
| Tienda del mercader | Fondo + marco | **PNG** | 1920×1080 | **Mitad izquierda transparente** (modelo 3D) |
| Transición / Final | Fondo completo | JPG | 1920×1080 | Centro (título y párrafo) |
| HUD (marco de combate) | Superposición | **PNG** | 1920×1080 | **Todo el centro transparente** |
| Logo del título | Emblema suelto | **PNG** | 1400×700 | Fondo totalmente transparente |
| Pausa (pendiente) | Fondo oscurecido | **PNG** | 1920×1080 | Centro (botones) |

### Reglas que ahorran problemas

1. **Sin texto en las imágenes.** El juego ya dibuja los títulos y botones con
   su propia tipografía. Si la imagen trae texto, se duplica y además saldría
   borroso al escalar. Única excepción: el logo del título (punto aparte).
2. **JPG para fondos opacos, PNG solo si hace falta transparencia.** Un PNG de
   1920×1080 ocupa unos 11 MB de VRAM; los JPG pesan mucho menos en disco.
3. **No pedir más de 1920×1080.** Ya tuvimos un cuelgue por falta de VRAM con
   texturas de 8K (ver `entorno.reducir_texturas`). No repitamos el problema
   con la interfaz.
4. **Composición oscura en las zonas de texto.** El texto del juego es claro
   (`rgb 240,238,232`); si el fondo es claro ahí, no se lee. Pedir
   explícitamente que esas zonas queden oscuras.

---

## 2. Bloque de estilo (pegar SIEMPRE al principio)

Este bloque es lo que mantiene coherentes todas las imágenes entre sí. Va antes
de cada prompt, sin cambiar una palabra.

```
STYLE: Dark fantasy game UI art, in the visual language of Elden Ring and Dark
Souls. Painterly digital oil painting, muted and desaturated palette dominated
by deep charcoal black, cold slate grey and aged tarnished gold. Heavy vignette
darkening all four corners. Ornate heraldic filigree and thin gold linework.
Weathered stone, cracked gilding, drifting ash and faint floating embers.
Volumetric light shafts through darkness. Solemn, melancholic, reverent mood.
High detail in the outer thirds of the frame, deliberately calm and dark in the
area reserved for text. Cinematic wide composition, 16:9 aspect ratio.
No text, no letters, no words, no watermark, no UI elements, no buttons.
```

**Prompt negativo** (si Gemini lo pide aparte):

```
text, letters, words, typography, watermark, signature, UI buttons, HUD,
bright saturated colors, neon, cartoon, anime, cel shading, cluttered center,
modern objects, lens flare, blurry, low quality
```

---

## 3. Prompts por pantalla

### 3.1 Menú principal — fondo

El texto va centrado en vertical (título en `y=.26`, botones de `y=.02` a
`y=-.18`), así que la columna central debe quedar oscura y despejada.

```
[STYLE BLOCK]

SCENE: A vast ruined colosseum of black basalt under a total solar eclipse. The
eclipsed sun hangs high in the upper third: a perfect black disc ringed by a
thin burning corona of pale gold light, with six faint radiating cracks in the
sky around it. Broken colossal statues of armoured guardians line both left and
right edges of the frame, half-swallowed by shadow, their gilding flaking away.
The centre of the image is an empty, dark, misty void — a deep vertical corridor
of shadow and drifting ash, almost black, reserved for menu text. Faint embers
rise from the bottom edge. Cold blue-grey rim light on the stone, warm dying
gold from the corona.
```

### 3.2 Instrucciones — fondo

```
[STYLE BLOCK]

SCENE: The dim interior of an ancient stone archive. Towering weathered walls
covered in faded engraved diagrams of celestial cycles — suns, moons, orbits —
carved into dark grey stone and filled with tarnished gold leaf. A single shaft
of cold pale light falls from a high unseen opening. The centre of the frame is
a large flat expanse of plain dark stone in shadow, almost featureless, reserved
for text. Ornate gold filigree borders frame the top and bottom edges. Dust
motes floating in the light. Extremely subdued, quiet, scholarly atmosphere.
```

### 3.3 Selección de guardián — fondo con marco (PNG)

La UI va a la **izquierda** (`x=-.62`) y el modelo 3D aparece a la **derecha**.

```
[STYLE BLOCK]

SCENE: A solemn sanctuary of black stone, composed strictly for a vertical split
layout. On the LEFT THIRD: an ornate gothic stone pillar and an aged gold
filigree panel frame, dark and richly detailed, forming a vertical border for a
list of names. On the RIGHT TWO THIRDS: almost entirely EMPTY — pure deep black
void with only a faint circular pool of dim gold light on the floor at the very
bottom, like a pedestal awaiting a figure. No objects, no statues and no detail
whatsoever in the right two thirds. Drifting ash. Strong vignette. The empty
right side must read as depth and darkness, not as a wall.
```

> Al exportar: borrar los dos tercios derechos a **transparencia total** para
> que se vea el modelo 3D. Conservar el charco de luz del suelo si queda bien
> bajo los pies del personaje.

### 3.4 Tienda del mercader — fondo con marco (PNG)

La UI va a la **derecha** (`x=.34`) y el modelo del mercader a la **izquierda**.

```
[STYLE BLOCK]

SCENE: A cramped nocturnal merchant's camp at the edge of ruins, composed for a
vertical split layout. On the RIGHT HALF: a hanging tattered canopy of dark
cloth, worn leather straps, small brass lanterns with warm dim flames, stacked
crates and an ornate aged gold panel frame — richly detailed, forming a border
for a list of wares. On the LEFT HALF: almost entirely EMPTY dark night — deep
black void with faint warm lantern glow spilling in from the right and a small
dim circle of firelight on the dirt ground at the very bottom. No objects and no
detail in the left half. Embers drifting. Intimate, secretive, warm-against-cold
atmosphere.
```

> Al exportar: borrar la mitad izquierda a transparencia total.

### 3.5 Transición entre combates — fondo

Se usa tras liberar a cada guardián, con los diálogos de la Guardiana de la Luna.

```
[STYLE BLOCK]

SCENE: A desolate moonlit plain after battle, seen wide and distant. A pale thin
crescent moon low in a vast dark sky streaked with slow clouds. Silhouettes of
broken banners and a single fallen colossal armoured figure at the far left and
far right edges, reduced to dark shapes. The entire centre of the frame is empty
sky and mist — a soft dark gradient from near-black at the edges to very deep
blue-grey in the middle, reserved for text. Cold silver-blue palette with a
single faint warm gold accent. Ash falling like snow. Elegiac, mournful,
peaceful aftermath.
```

### 3.6 Pantalla final — fondo

```
[STYLE BLOCK]

SCENE: The restored celestial mechanism seen from below. A colossal ring of aged
gold gears, orbits and armillary bands turning slowly in a black sky, the
eclipse ending: a sliver of warm dawn light returning at the ring's edge and
spilling downward. Six small elemental sigils glowing faintly around the ring —
sun, flame, ice, leaf, void, moon. The lower centre of the frame is dark open
sky, reserved for text. Warm gold light finally overcoming the cold blue dark.
Hopeful but exhausted, reverent, monumental.
```

### 3.7 Marco del HUD durante el combate (PNG, opcional)

Cuidado aquí: todo el centro debe ser transparente o tapará el juego.

```
[STYLE BLOCK]

SCENE: An ornamental border frame ONLY, on a pure flat black background. Aged
tarnished gold filigree and worn stone corner ornaments hugging the extreme
outer edges of the frame — thin, restrained, elegant. Small heraldic motifs in
the four corners. The entire central area is completely flat solid black and
absolutely empty. The gold ornament must occupy no more than the outermost eight
percent of the image on each side.
```

> Al exportar: convertir todo el negro central en transparencia y guardar como
> PNG. Bajar la opacidad general al 40–60 % para que no compita con el HUD.

### 3.8 Logo del título (PNG con transparencia)

**Esta es la única imagen que sí lleva texto.** Si el logo queda bien, se
sustituye el `Text` del menú por la imagen.

```
Ornate dark fantasy game logo emblem, in the visual language of Elden Ring.
The words "GUARDIANES DEL ECLIPSE" in an elegant engraved serif capital
typeface, letterspaced wide, rendered in aged tarnished gold with worn metallic
texture and subtle chipping. Behind and around the words: a large circular
eclipse sigil — a black disc with a thin burning corona, crossed by delicate
radiating filigree lines and six small elemental marks. Symmetrical heraldic
composition. Pure transparent background, no scene, no frame. Muted gold on
nothing but transparency. High resolution, crisp edges.
```

> Los generadores suelen escribir mal el texto. Dos alternativas: pedir el
> emblema **sin palabras** y dejar que el juego dibuje el título encima, o
> corregir el texto a mano en un editor de imagen.

---

## 4. Orden de trabajo sugerido

1. **Logo + menú principal.** Son la primera impresión y fijan la paleta.
2. **Transición y final.** Reutilizan la misma composición centrada, fáciles.
3. **Instrucciones.**
4. **Selección y tienda.** Las más delicadas por la transparencia.
5. **Marco del HUD.** Lo último: es un adorno y puede estorbar si se pasa.

Consejo: generar **varias variantes de la primera imagen** y elegir una antes de
seguir. Esa imagen marca el estilo, y las siguientes deben describirse
mencionando explícitamente lo que funcionó en ella (paleta, nivel de detalle,
intensidad del viñeteado) para que el conjunto se vea de la misma mano.

---

## 5. Dónde se incorporan (referencia de código)

Todas las pantallas heredan de `Pantalla` en `interfaz.py` y cuelgan de
`self.raiz`, que ya es hijo de `camera.ui`. Un fondo se añade así:

```python
# dentro del __init__ de la pantalla, ANTES de crear textos y botones
self.fondo = Entity(
    parent=self.raiz,
    model="quad",
    texture=<textura cargada>,
    scale=(camera.aspect_ratio, 1),   # 1.778 x 1 = pantalla completa 16:9
    z=1,                              # detrás del resto de la UI
)
```

El orden importa: lo que se crea primero con `z` mayor queda detrás. Para cargar
la imagen conviene reutilizar `entorno.cargar_textura`, que ya resuelve el
problema de las rutas con acentos y permite limitar el tamaño:

```python
from entorno import cargar_textura
tex = cargar_textura(RAIZ / "assets" / "ui" / "menu.jpg",
                     repetir=False, max_lado=1920)
```

Las imágenes irían en una carpeta nueva `assets/ui/`.

---

## 6. Pantallas sin imagen generada

Dos pantallas del juego **no llevan arte generado**, por decisión de diseño:

- **Pausa.** Solo un velo oscuro semitransparente por código, para que se siga
  viendo el combate congelado por detrás. Una imagen habría tapado la escena y
  restado la sensación de que la partida sigue ahí.
- **Marco del HUD** (§3.7). Se descartó: en combate compite con la información
  del HUD y estorba más de lo que suma.
