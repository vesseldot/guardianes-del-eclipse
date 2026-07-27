# Guardianes del Eclipse

Juego de acción en tercera persona con estructura de *boss-rush*, hecho con
**Ursina Engine** (Python) sobre Panda3D.

Eliges a uno de los seis Guardianes elementales y te enfrentas, uno tras otro, a
tus compañeros corrompidos. Entre combate y combate, el Mercader vende mejoras a
cambio de los fragmentos obtenidos.

---

## Cómo ejecutar

```bash
pip install ursina panda3d-gltf simplepbr
python main.py
```

El juego arranca en pantalla completa. Para trabajar en ventana, pon
`PANTALLA_COMPLETA = False` en `config.py`.

Si falta algún modelo `.glb`, el personaje se dibuja como una primitiva de su
color y la consola avisa cuáles faltan: el juego nunca deja de arrancar.

### Portátiles con dos tarjetas gráficas

Windows puede ejecutar el juego en la GPU integrada y dar pocos FPS. Para forzar
la dedicada: **Panel de Control de NVIDIA → Administrar configuración 3D →
Configuración de programa → Agregar `python.exe` → Procesador NVIDIA de alto
rendimiento**.

El ajuste de *Configuración → Pantalla → Gráficos* de Windows no sirve aquí:
solo afecta a aplicaciones DirectX, y este juego usa OpenGL.

---

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
| `Esc` | Pausar el combate |

---

## Estructura

| Archivo | Qué hace |
|---|---|
| `main.py` | Punto de entrada y máquina de estados del juego |
| `config.py` | Presets de calidad y monitor de rendimiento |
| `datos.py` | Estadísticas de guardianes, jefes, armas y objetos — **aquí se balancea el juego** |
| `recursos.py` | Carga de modelos con respaldo automático |
| `entorno.py` | Texturas del entorno y reducción de texturas |
| `jugador.py` | Guardián controlable, combate y cámara |
| `jefe.py` | IA de los jefes |
| `fantasma.py` | Enemigo menor invocado por el jefe final |
| `movimientos_personaje.py` | Animación de locomoción, golpe y armas equipables |
| `sonido.py` | Música por estado y efectos |
| `proyectiles.py` | Pool de proyectiles |
| `interfaz.py` | HUD y pantallas de UI |
| `vitrina.py` | Escaparate 3D de la selección y la tienda |

```
modelos/    modelos 3D .glb (personajes y armas)
texturas/   suelo de la arena y cielo nocturno
assets/     music/ · sounds/ · ui/
```

---

## Assets

Los **modelos 3D** (`modelos/**/*.glb`, ~2.6 GB) **no están en el repositorio**:
varios superan el límite de 100 MB por archivo de GitHub. Se entregan dentro del
proyecto comprimido. El resto de assets (texturas, música, efectos e imágenes de
interfaz) sí están incluidos.

---

## Documentación

- **`ARTE_UI.md`** — instrucciones usadas para generar el arte de las pantallas.
- La documentación completa del proyecto se entrega **en PDF**, aparte.
