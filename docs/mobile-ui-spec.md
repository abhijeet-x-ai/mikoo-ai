# Mikoo mobile UI specification

## Direction

Mikoo's Android APK uses the supplied dark mobile references as a visual direction: near-black background, charcoal raised surfaces, bright neutral text, muted secondary text, blue primary actions, a rounded composer, and a compact top bar. The design is inspired by the interaction patterns shown in the references but uses Mikoo's own name, copy, and offline coding workflow.

## Chat-first layout

The default screen is now a focused chat surface. During a conversation, task cards, workspace controls, and navigation options are not kept permanently on screen. The user sees the model header, a compact agent-state indicator, the scrollable transcript, and the composer. This keeps the conversation readable on small displays.

A three-line navigation button is placed in the upper-left corner. It opens a local menu containing Chat, Tasks, Agent, New workspace, Chat history, and New chat. The menu closes after an option is selected. Tasks and workspace management are therefore available without competing with the active conversation.

## Main surfaces

| Surface | Behavior |
|---|---|
| Top bar | Shows the Mikoo model label, local mode indicator, and the three-line navigation button. |
| Navigation menu | Provides Chat, Tasks, Agent, New workspace, Chat history, and New chat actions. |
| Agent-state chip | Shows READY, THINKING, REPLIED, CANCELLED, STOPPED, or RESTORED so the user can tell whether Mikoo is responding. |
| Transcript | Scrollable local conversation with explicit You/Mikoo labels and a temporary working marker. |
| Composer | Multiline task entry, keyboard send action, Stop, and blue send action. |
| Tasks screen | Shows workspace selection and local task states without occupying the chat screen. |
| Chat history | Stores the latest local prompts on-device and allows a prompt to be returned to Chat. |
| Status line | Shows offline runtime state, latency, context limit, PSS estimate, and generated-token count after a generation attempt. |

## Session behavior

The current transcript and the latest bounded list of prompts are stored in app-private local preferences only. Clear session removes the current transcript and returns the UI to the starter suggestions; it does not contact a server. A restored session is labeled RESTORED so the user knows it was recovered from local storage.

When a prompt is submitted, the UI immediately appends the user message, shows `THINKING`, displays a progress indicator, and inserts a temporary `working locally` marker. The marker is replaced by the native response, including a truthful checkpoint-pending explanation when no trained Mikoo checkpoint is installed. Stop and memory-guard paths also replace the marker with a visible safe-stop message.

## Accessibility and low-end behavior

The layout uses native Android widgets, readable contrast, touch targets larger than the minimum practical size, visible text labels, and no image assets required for the first APK. The transcript, task list, and history list are the only scrolling surfaces. A single model process is assumed, with the runtime memory policy reducing context or stopping safely near the 749 MB hard cap.

## Runtime boundary

The APK is an offline-first UI and native runtime shell. It does not call an external AI API. The current checkpoint is intentionally pending; until a validated self-trained local model is connected, the native bridge acknowledges the prompt and explains the limitation rather than fabricating code or output. The next model milestone is a validated Mikoo checkpoint plus a bounded C++ inference adapter that respects the memory policy.
