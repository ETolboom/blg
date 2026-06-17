/*
 * Adapted from bpmn-analyzer-js (https://github.com/timKraeuter/bpmn-analyzer-js)
 * MIT License, Copyright (c) 2024 Tim Kräuter. See ./LICENSE.
 * Vendored into BLG for token-replay visualization of control-flow counterexamples.
 */

import DisableModeling from "./DisableModeling";

export default {
  __init__: ["disableModeling"],
  disableModeling: ["type", DisableModeling],
};