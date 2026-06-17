/*
 * Adapted from bpmn-analyzer-js (https://github.com/timKraeuter/bpmn-analyzer-js)
 * MIT License, Copyright (c) 2024 Tim Kräuter. See ./LICENSE.
 * Vendored into BLG for token-replay visualization of control-flow counterexamples.
 */

import "./token-simulation.css";

import CounterExampleVisualizer from "./CounterExampleVisualizer";
import AnimationModule from "./animation";
import TokenCountModule from "./token-count";
import MessageCountModule from "./message-count";
import TokenColorsModule from "./token-colors";
import NotificationsModule from "./notifications";
import LogModule from "./log";
import DisableModelingModule from "./disable-modeling";
import TokenSimulationPaletteModule from "./palette";
import RestartCounterExampleModule from "./restart-counter-example";
import PauseExecutionModule from "./pause-execution";
import SetAnimationSpeedModule from "./set-animation-speed";

export default {
  __depends__: [
    AnimationModule,
    TokenCountModule,
    MessageCountModule,
    TokenColorsModule,
    NotificationsModule,
    LogModule,
    DisableModelingModule,
    TokenSimulationPaletteModule,
    RestartCounterExampleModule,
    PauseExecutionModule,
    SetAnimationSpeedModule,
  ],
  __init__: ["counterExampleVisualizer"],
  counterExampleVisualizer: ["type", CounterExampleVisualizer],
};