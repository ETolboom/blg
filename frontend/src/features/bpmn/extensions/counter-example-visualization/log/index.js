/*
 * Adapted from bpmn-analyzer-js (https://github.com/timKraeuter/bpmn-analyzer-js)
 * MIT License, Copyright (c) 2024 Tim Kräuter. See ./LICENSE.
 * Vendored into BLG for token-replay visualization of control-flow counterexamples.
 */

import Log from "./Log";

import NotificationsModule from "../notifications";

export default {
  __depends__: [NotificationsModule],
  __init__: ["log"],
  log: ["type", Log],
};