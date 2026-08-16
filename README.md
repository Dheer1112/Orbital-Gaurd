# 🛰️ NX-77 — Orbital Command Center

**NICOTECH-X Space Debris Collision Avoidance System**
*Built with love by Team Nicotech*

A single-file, browser-based 3D mission control interface for monitoring a satellite (**NX-77**) in low Earth orbit, reviewing nearby debris conjunctions, and simulating a collision-avoidance maneuver — all rendered live with [Three.js](https://threejs.org/).

## 🌐 Live Demo

The whole project is one self-contained file: `index.html`. There is no build step and no server — download the file and open it in any modern browser (Chrome/Edge/Firefox with WebGL2 support). An internet connection is needed on first load, since Three.js, the Earth/cloud textures, and the fonts are pulled from public CDNs.

## 🚀 What is NX-77?

NX-77 is an interactive command-center screen for a fictional LEO satellite of the same name. It opens with a boot sequence and a title screen, then drops you into a 3D scene of Earth surrounded by orbital rings, a tracked debris field, and a set of flagged "conjunction" objects — pieces of debris whose orbits are projected to pass close to NX-77. From there you can inspect each threat, review the satellite's own orbital profile, and dial in an avoidance maneuver to see its effect on collision risk.

## 🎯 The Problem

Satellite operators have to continuously watch for debris and other objects whose orbits might intersect their own, judge how serious each conjunction is, and decide whether (and how) to burn fuel to shift the satellite's path. NX-77 dramatizes that workflow as a single, self-contained screen: a ranked list of conjunctions, a risk readout for whichever one is selected, and a small set of maneuver options to try before "executing" one.

## 💡 How NX-77 Works

Everything the interface shows is driven by two hand-authored JavaScript data objects that live inside `index.html`:

- **`threatData`** — five debris objects, each with a name, an estimated collision probability, a miss distance, a relative velocity, and a HIGH/MED/LOW threat level.
- **`maneuverData`** — three preset avoidance maneuvers (A/B/C), each with a Δv (velocity change), a resulting collision risk, and a resulting miss distance.

Clicking a threat (in the side list or directly on its 3D marker) copies that object's numbers into every readout on screen — the risk panel, the miss-distance popup, the header. Choosing and "executing" a maneuver copies the matching `maneuverData` entry in the same way, animating the risk number down and flipping the mission-impact readout to "PRESERVED." The 3D positions of the satellite, debris field, and orbit rings are animated with simple trigonometric motion for visual effect — the numbers you read are the fixed dataset values, not a live physics computation, even though the SYSTEM tab labels the (display-only) processing core as `SGP4 / SDP4`.

## 🖥️ Explore the Interface

### Boot Sequence & Launch Screen
On load, a boot overlay cycles through status lines ("INITIALIZING SENSOR ARRAY," "CALIBRATING CONJUNCTION SCREEN"...) with a progress bar, then reveals a title screen for the NICOTECH-X system. The **ENTER CONTROL PANEL →** button fades into the 3D command center and fires the first danger alert ("CONJUNCTION SCREENING ACTIVE").

### 3D Orbital Scene
The center of the screen is a live Three.js scene: a textured, rotating Earth with clouds and atmosphere glow, three faint orbital rings, a starfield, a satellite model orbiting on its own path, a field of ~480 small tracked-object points, and glowing markers for the five named debris threats, each trailing its own colored orbit line (red/amber/green by threat level). Drag to rotate the camera, scroll to zoom, and double-click to reset the view.

### Mission Console (left panel, 4 tabs)
- **OVERVIEW** — NX-77's status card: altitude, velocity, inclination, fuel reserve, OPERATIONAL status pill.
- **THREATS** — the ranked list of all five conjunctions, each showing its miss distance, relative velocity, and HIGH/MED/LOW badge; clicking one selects it.
- **SATELLITE** — NX-77's orbital elements: orbit type (LEO), perigee, apogee, period, status.
- **SYSTEM** — display-only "processing core" readout (propagator, screening state, data source, engine, mode).

### Threat Selection & Conjunction Popup
Selecting a debris object — from the THREATS list or by clicking its marker in the 3D scene — highlights it, snaps the camera into a "spectate" mode that follows its orbit, opens a floating popup with its miss distance/relative velocity/risk, and pushes a danger or warning alert into the top-right alert stack depending on its threat level.

### Threat Response Panel (right panel)
- **Risk card** — the selected threat's collision probability as a large percentage, a status line ("ELEVATED / ACTION RECOMMENDED," etc.), and a proportional risk bar.
- **Conjunction stats** — miss distance, time to closest approach, relative velocity, and mission-impact status.
- **Maneuver optimizer** — three preset maneuvers (A: low Δv, B: max safety, C: clearance) selectable as buttons, plus a Δv slider (0.20–1.20 m/s) that updates the displayed magnitude live. **SIMULATE MANEUVER →** "executes" the selected maneuver: the risk number animates down to the maneuver's target value, miss distance updates, and the mission-impact readout turns green ("PRESERVED"). **RESET** returns the whole scenario to its starting state.

### Camera & View Controls (bottom bar)
Buttons for **GLOBAL**, **ASSET**, and **THREAT** camera framings, plus **PAUSE**, which freezes all orbital motion. Clicking the satellite model itself enters a satellite-spectate camera mode that follows NX-77 around its orbit; scrolling out or double-clicking exits any spectate mode.

### Telemetry HUD
Fixed side readouts for ground-station coordinates and link status (left) and UTC clock, session uptime, a live-measured FPS counter, and tracked-object count (right), all updating in real time while the page is open.

## 🧭 Technical Walkthrough

The entire project is one file, `index.html`, organized top-to-bottom as:

1. **`<style>` (lines 9–352)** — all visual styling: the HUD/panel theme, boot screen, alert stack, buttons, sliders, and the custom cursor.
2. **HTML markup (lines 355–556)** — the boot overlay, top/side telemetry readouts, launch screen, and the command-center layout (left mission console, 3D canvas, right threat-response panel, bottom camera bar).
3. **`<script>` (lines 558–1162)** — the Three.js scene and all interface logic, loaded after Three.js itself from a CDN (line 557).

To see how a given feature is implemented, open `index.html` and jump to:

| What you see | Where it lives in `index.html` |
|---|---|
| Earth, clouds, atmosphere, orbit rings, satellite model, debris field, conjunction paths | lines ~560–754 (Three.js scene construction) |
| The five debris conjunctions and their numbers | `threatData` object, lines ~691–697 |
| Drag-to-rotate / wheel-to-zoom / double-click-reset camera | pointer & wheel listeners, lines ~821–843 |
| Threat & satellite "spectate" follow-camera | `enterSpectate` / `enterSatelliteSpectate` / `exitSpectate`, lines ~782–819, and the camera-follow branch in the render loop, lines ~885–897 |
| Procedural motion of debris markers along their orbits | `placeThreats()`, lines ~846–866 |
| Main render/animation loop | `render()`, lines ~868–909 |
| Boot progress sequence | lines ~917–940 |
| Launch screen → command center transition | lines ~942–963 |
| Mission Console tab switching | lines ~965–973 |
| Selecting a threat (list click or 3D-marker click) and updating every readout | `selectThreat()`, lines ~977–1000, plus the raycasting click handler, lines ~1002–1030 |
| Maneuver presets A/B/C and the Δv slider | `maneuverData` object and `setManeuver()`, lines ~1032–1059 |
| "Simulating" a maneuver (risk animating down, impact turning green) | the `executeBtn` click handler, lines ~1061–1082 |
| Resetting the scenario | `resetBtn` click handler, lines ~1084–1101 |
| Global/Asset/Threat camera-mode buttons and Pause | lines ~1103–1117 |
| Smooth animated number transitions (e.g. the risk %) | `animateNumber()`, lines ~1119–1129 |
| Toast notifications and the alert stack | `showToast()` / `pushAlert()`, lines ~949, 1131–1136 |
| UTC clock, session uptime, live FPS counter | lines ~1138–1159 |

## 🧪 Experiment With It

Since there's no build step, the fastest way to try changes is directly in the file or in the browser devtools:

- **Change the threat picture**: edit the `threatData` object (line ~691) to add debris, rename objects, or change their risk/miss/relative-velocity numbers — the THREATS list, risk panel, and popup all read from this one object.
- **Change the maneuver options**: edit `maneuverData` (line ~1033) to try different Δv/risk/miss combinations for maneuvers A, B, and C.
- **Adjust the visuals**: the orbit radii (`orbitRadii`, line ~659), debris field size (`debrisCount`, line ~718), and camera zoom limits (in the `wheel` listener, line ~826) are plain constants near the top of the script.
- **Inspect live state**: with the page open, the browser console has direct access to the scene's variables (`threatData`, `maneuverData`, `selectedId`, `cameraMode`, etc.) since the script runs in an IIFE but Three.js objects are reachable via the DOM/console for debugging.

## 📁 Repository Structure

```
NX-77_NICOTECH_Space_Debris_Control.html   ← the entire project: markup, styles, and logic in one file
```

There are no separate source modules, stylesheets, or data files — CSS, HTML, and JavaScript (including the two data objects that drive every readout) all live inside this single `index.html`.

## 🛠️ Running the Project

No installation or dependencies to manage locally:

1. Download `index.html`.
2. Open it in a WebGL2-capable browser (double-click it, or drag it into a browser window).
3. Keep an internet connection available for the first load — Three.js, the Earth/cloud textures, and the Google Fonts used by the HUD are all fetched from CDNs at runtime.

To host it as a live demo, any static file host (GitHub Pages, Netlify, a plain web server) works, since the page has no backend or server-side dependency.

## 🔮 Limitations

The collision-risk, miss-distance, and maneuver figures come from the fixed `threatData` and `maneuverData` objects rather than a live orbital-mechanics computation, and the SYSTEM tab's `SGP4 / SDP4` and `PUBLIC GP DATA` labels are part of the mission-console display rather than an active data feed.
