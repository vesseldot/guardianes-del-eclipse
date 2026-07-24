# Guardianes del Eclipse — proyecto Ursina

## Cómo ejecutar

```bash
pip install ursina panda3d-gltf simplepbr
cd guardianes
python main.py
```

El juego **corre desde ahora**, incluso sin los modelos 3D. Mientras falte un
`.glb`, cada personaje se dibuja como una primitiva de su color y la consola
avisa cuáles faltan. Eso permite programar y probar en paralelo al modelado.

`simplepbr` da la iluminación PBR de los modelos `.glb`; si no está instalado,
el juego sigue funcionando pero los modelos se ven planos.

## Controles

| Tecla / Ratón | Acción |
|---|---|
| `WASD` | Moverse (relativo a la cámara) |
| `Shift` | Correr (gasta estamina) |
| `Ratón` | Orbitar la cámara |
| `Rueda del ratón` | Acercar / alejar la cámara |
| `Clic izq` | Ataque ligero |
| `Clic der` | Ataque pesado |
| `Espacio` | Rodar / esquivar (i-frames) |
| `Q` | Lanzar hechizo |
| `E` | Cambiar de hechizo |
| `R` | Beber frasco (curación) |
| `F` | Fijar / soltar objetivo (lock-on) |
| `1` `2` `3` | Cambiar de arma |
| `Esc` | Menú / pausa |

---

## Assets (importante para clonar el repo)

Los **modelos 3D** (`modelos/**/*.glb`, ~2 GB en total) **no están en el
repositorio**: varios archivos rozan el límite de 100 MB por archivo de GitHub
y en conjunto exceden el tamaño razonable de un repo. El juego arranca igual
usando primitivas de respaldo (ver `recursos.py`). Para jugar con los modelos
reales, colócalos en `modelos/` siguiendo la estructura de más abajo.

**Sí** están incluidas las texturas del entorno que el juego carga en runtime:

- `rock_wall_16_4k.blend/textures/rock_wall_16_diff_4k.jpg` — suelo de la arena.
- `NightSkyHDRI016B_1K/NightSkyHDRI016B_1K_TONEMAPPED.jpg` — cielo nocturno.

Quedan excluidos los `.blend`, el resto del set PBR de roca (displacement,
normal, roughness) y el HDRI en `.exr`, por peso y porque no se usan en runtime.
Consulta `.gitignore` para el detalle.

---

## Estructura

| Archivo | Qué hace |
|---|---|
| `main.py` | Punto de entrada y máquina de estados (menú, selección, combate, tienda, transición, fin) |
| `config.py` | Presets de calidad y monitor de rendimiento adaptativo |
| `datos.py` | Estadísticas de guardianes, jefes y objetos de la tienda — **aquí se balancea el juego** |
| `recursos.py` | Carga de modelos con respaldo automático |
| `entorno.py` | Carga de texturas del entorno (suelo, cielo) con filtrado y respaldo |
| `jugador.py` | Guardián controlable y cámara (órbita, lock-on, zoom con rueda) |
| `jefe.py` | Guardianes corrompidos y jefe final |
| `proyectiles.py` | Pool de hechizos |
| `interfaz.py` | HUD, menús, selección, tienda y transiciones |
| `vitrina.py` | Escaparate 3D para selección de guardián y tienda |

---

## Optimización aplicada

- **Pool de proyectiles**: las entidades se crean una vez y solo se activan
  y desactivan. Nunca se crean ni destruyen durante el combate.
- **Un solo `update()` global** en lugar de uno por entidad. Ursina descubre
  los `update()` por reflexión y cada uno tiene coste fijo por frame.
- **Colisión por distancia al cuadrado**, sin colisionadores físicos y sin
  raíz cuadrada.
- **Textos que solo se reescriben al cambiar de valor.** Asignar `.text`
  regenera la geometría del texto; hacerlo 60 veces por segundo se nota.
- **Una sola escena** que se activa y desactiva por secciones. Nunca se
  recarga el nivel.
- **Una única luz direccional**, con sombras solo en calidad alta.
- **Tres presets de calidad** (`bajo`, `medio`, `alto`) que controlan sombras,
  partículas, distancia de dibujado y tamaño del pool.
- **Calidad adaptativa**: si los FPS promedio caen por debajo de 28 durante
  2.5 segundos, el juego baja un nivel de calidad solo. Si el usuario elige
  la calidad manualmente desde el menú, se respeta su elección.

---

## Siguientes pasos: importar los modelos desde Blender

### Paso 1 — Preparar el archivo en Blender

1. Selecciona el personaje completo (malla + armature si tiene).
2. `Object → Apply → All Transforms` (`Ctrl+A`). Sin esto, el modelo aparece
   con escalas o rotaciones raras en el motor.
3. Coloca el origen del objeto **en los pies**, no en el centro del cuerpo:
   `Object → Set Origin → Origin to 3D Cursor`, con el cursor en el suelo.
   Así el personaje se apoya en `y = 0` sin necesidad de compensar en código.
4. Comprueba la escala: el jugador mide aproximadamente **2 unidades de alto**
   en el juego. Si tu modelo mide 180 en Blender, escálalo antes de exportar.

### Paso 2 — Nombrar las animaciones

Si el personaje está animado, abre el *Dope Sheet → Action Editor* y renombra
cada acción con nombres exactos. El código busca estos:

| Nombre de acción | Cuándo se usa |
|---|---|
| `Idle` | En reposo |
| `Run` | Al moverse |
| `Attack` | Al atacar (jefes) |
| `Hit` | Opcional, al recibir daño |

Marca cada acción con el botón del **escudo** (*Fake User*) para que Blender
no la descarte al guardar. Sin eso, las acciones no llegan al `.gltf`.

### Paso 3 — Exportar

`File → Export → glTF 2.0 (.glb/.gltf)`

- **Format:** `glTF Separate (.gltf + .bin + textures)` ← importante, es el
  formato que espera el proyecto.
- **Include:** activa *Selected Objects* si solo quieres exportar el personaje.
- **Transform:** deja `+Y Up` activado (valor por defecto).
- **Data → Mesh:** activa *Apply Modifiers*.
- **Animation:** activa *Animation* y, dentro, *Export Deformation Bones Only*
  para reducir el tamaño del archivo.
- Guárdalo con el nombre exacto que espera el proyecto (siguiente paso).

### Paso 4 — Colocar los archivos

Copia la carpeta exportada **completa** (`.gltf` + `.bin` + `textures/`) dentro
de `modelos/`, con estos nombres:

```
modelos/
  sol/sol.gltf                       ← chibi jugable
  fuego/fuego.gltf
  hielo/hielo.gltf
  naturaleza/naturaleza.gltf
  vacio/vacio.gltf
  luna/luna.gltf
  sol_jefe/sol_jefe.gltf             ← forma armada
  fuego_jefe/fuego_jefe.gltf
  hielo_jefe/hielo_jefe.gltf
  naturaleza_jefe/naturaleza_jefe.gltf
  vacio_jefe/vacio_jefe.gltf
  conejo/conejo.gltf                 ← jefe final
  mercader/mercader.gltf             ← dinosaurio
  fantasma/fantasma.gltf
```

Las carpetas ya están creadas y vacías. Si quieres otros nombres, edítalos en
el diccionario `MODELOS` de `datos.py`.

### Paso 5 — Verificar

Arranca el juego. En la consola verás qué modelos siguen usando primitivas:

```
[modelos] usando primitivas de respaldo para: fuego, hielo, ...
```

Para confirmar los nombres reales de las animaciones de un modelo ya copiado:

```bash
python -c "import recursos; recursos.listar_animaciones('sol')"
```

Los nombres que imprime son los que debes usar. **No siempre coinciden** con
los que veías en Blender: a veces glTF les añade un prefijo. Si difieren,
ajusta las llamadas a `animar(...)` en `jugador.py` y `jefe.py`.

### Paso 6 — Calibrar tamaño

Si un personaje sale demasiado grande, pequeño o girado, ajusta su `escala` en
el diccionario `MODELOS` de `datos.py`. Es normal tener que calibrar cada
modelo por separado; no es un error de exportación.

---

## Problemas frecuentes

| Síntoma | Causa habitual |
|---|---|
| El modelo no carga y no da error | Falta `pip install panda3d-gltf` |
| Aparece sin texturas | Copiaste solo el `.gltf`, sin la carpeta `textures/` |
| Aparece acostado | No aplicaste las transformaciones en Blender |
| Se hunde en el suelo | El origen no está en los pies |
| La animación no arranca | El nombre no coincide: usa `listar_animaciones()` |
| Va muy lento con el modelo puesto | Demasiados polígonos: aplica un modificador *Decimate* en Blender |

---

## Reparto de trabajo sugerido

**Día 1** — Exportar `sol` y `sol_jefe`, verificar que cargan y que las
animaciones responden. Ese par valida todo el pipeline; el resto es repetir.

**Día 2** — Exportar los cuatro guardianes restantes y sus formas armadas.
En paralelo, balancear `datos.py`.

**Día 3** — Conejo, mercader y fantasma. Añadir el hub visual y las
transiciones con la guardiana de la Luna.

**Día 4** — Balanceo, sonidos, partículas y build final.
