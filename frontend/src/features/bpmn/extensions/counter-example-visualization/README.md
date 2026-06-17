# counter-example-visualization

Vendored bpmn-js modules that animate a **token replay** over a BPMN diagram, used to
show *how* a control-flow violation (deadlock, safeness, proper-completion) is reached.

## License

Adapted from **[bpmn-analyzer-js](https://github.com/timKraeuter/bpmn-analyzer-js)** by
Tim Kräuter. **MIT License, Copyright (c) 2024 Tim Kräuter** (see [`LICENSE`](./LICENSE)).

Changes made when vendoring into BLG:
- Dropped the editor-only modules: `toggle-modeling/`, the standalone `analysis/`,
  `analysis-overlays/`, `properties-summary/`, and `quick-fixes/`.
- `CounterExampleVisualizer.js`: removed the `analysis.done` auto-wiring; the replay is now
  triggered programmatically via the `counterexample.visualization.start` event
  (see `composables/useCounterExampleReplay.ts`).
- Per-file attribution header added to each source file.

The counterexample data is produced by the Rust analyzer bindings on the backend and delivered
per-criterion (`counter_example` field); this front-end only renders it.
