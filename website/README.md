# Gesture / Racing web experience

The Next.js site, interactive practice track, game launch flow, and browser-based live cockpit are part of the full Gesture / Racing project.

See the [root README](../README.md) for the complete product overview, architecture, gestures, setup, security notes, and verification steps.

## Run locally

```bash
npm ci
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000). Camera features require a supported browser and explicit camera permission. The optional external-game keyboard bridge is a separate Windows process described in the root README.

## Checks

```bash
npm run lint
npm run build
```
