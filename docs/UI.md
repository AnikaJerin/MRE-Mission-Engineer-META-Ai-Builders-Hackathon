# Lunar workspace UI

From the repository root, inside its virtual environment:

```sh
python -m mre_engineer serve
```

Open http://127.0.0.1:8766 yourself. Stop with Ctrl+C. If occupied, use
`python -m mre_engineer serve --port 8767` and open port 8767 instead.

This first dashboard is read-only. It does not download sources, invoke a model,
generate a plan or run physical calculations. Investigation steps are labelled not
run/not built. Animations depict the theme, not experiment progress. The moon is
an original CSS concept illustration, not a reactor image or physical simulation.

Implemented: lunar palette/orbit illustration; evidence filters; keyboard-accessible
native source dialogs; resource catalog with rights; local integrity status; JSON
export without local source paths; empty original/revised-plan states; mobile
layout, focus indicators, skip link and reduced-motion support. There are no
external fonts, scripts or images. Opening source links makes external requests
only when you choose them; initial loading uses the local server.

## Owner checks (not executed by the assistant)

1. Confirm seven evidence records, three gaps and eight source entries.
2. Switch all views and evidence filters.
3. Open/close an evidence dialog using keyboard and Escape. Check source links.
4. Export JSON; confirm no invented investigation result or raw trace.
5. Resize to phone width and check horizontal overflow.
6. Enable system reduced motion; orbit and entry animations should stop.
7. Register a source file, refresh and confirm the integrity state changes.

The assistant has authored but not started, browser-tested or visually verified
this UI, following the owner's instruction not to run the project.
