# Mikoo mobile UI specification

## Direction

Mikoo's Android APK uses the supplied dark mobile references as a visual direction: near-black background, charcoal raised surfaces, bright neutral text, muted secondary text, blue primary actions, rounded composer, compact top bar, and a Tasks/Agent switcher. The design is inspired by the interaction patterns shown in the references but uses Mikoo's own name, copy, and offline coding workflow.

## Main surfaces

| Surface | Behavior |
|---|---|
| Top bar | Shows Mikoo model label, local mode indicator, and back navigation. |
| Offline banner | Makes local execution visible and dismissible. It never implies a remote service. |
| Tasks/Agent switcher | Agent opens the coding conversation; Tasks shows recent local task states. |
| Workspace row | Opens Android's app-scoped document-tree picker without broad storage permissions. |
| Suggestions | Starts common coding prompts: bug fix, patch review, and test generation. |
| Transcript | Scrollable local conversation with clear speaker labels. |
| Composer | Multiline task entry, stop action, and send action. |
| Status line | Shows model/runtime state, context limit, latency, PSS estimate, and generated-token count. |

## Accessibility and low-end behavior

The layout uses native Android widgets, readable contrast, touch targets larger than the minimum practical size, content descriptions through visible text, and no image assets required for the first APK. The transcript and task panels are the only scrolling surfaces. A single model process is assumed, with the runtime memory policy reducing context or stopping safely near the 749 MB hard cap.

## Runtime boundary

The APK is an offline-first UI and native runtime shell. It does not call an external AI API. The current checkpoint is intentionally pending; until a validated local model is connected, the native bridge reports that the runtime adapter is not connected rather than fabricating output.
