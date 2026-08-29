# JUPI HOME V1 — MASTER SPECIFICATION

## Updated Build Specification — Phases 1–3 Complete

You are building **Jupi Home V1**, the native Windows desktop client/interface for an existing AI system called **Saturnia**.

This is a real software project, not a disposable demo.

The project is being developed in controlled phases.

### CURRENT STATUS

The following phases are COMPLETE:

* ✅ Phase 1 — WPF foundation
* ✅ Phase 2 — Saturnia HTTP connection
* ✅ Phase 3 — Core chat experience

Do NOT rebuild or unnecessarily replace completed functionality.

The next phase is:

**Phase 4 — Conversation Experience**

Only proceed to the next phase when explicitly instructed.

---

# 1. ABSOLUTE RULES

These rules override convenience.

1. Jupi Home is a **separate project** from Saturnia.
2. NEVER modify the existing Saturnia source code.
3. NEVER rewrite Saturnia.
4. NEVER duplicate Saturnia's AI logic.
5. NEVER put the Gemini API key in Jupi Home.
6. NEVER call Gemini directly from Jupi Home.
7. NEVER import Python/Saturnia modules into the C# project.
8. NEVER use Electron.
9. NEVER use WinForms.
10. NEVER use Godot.
11. NEVER use a Python GUI framework.
12. NEVER turn Jupi Home into a browser wrapper.
13. Do not invent Saturnia APIs.
14. Do not silently modify Saturnia to make Jupi Home easier to build.
15. Do not implement future phases early.
16. Build and test after each phase.
17. Stop after the requested phase.
18. Prefer simple, understandable architecture over unnecessary abstraction.

If something appears to require modifying Saturnia:

**STOP and explain why.**

---

# 2. PRODUCT IDENTITY

Product:

**Jupi Home**

Jupi Home is the Windows interface for Saturnia.

Saturnia is the intelligence.

Jupi Home is the native client.

The intended long-term ecosystem is:

```text
                 SATURNIA
                 AI BRAIN
                    │
        ┌───────────┼───────────┐
        │           │           │
   Jupi Mobile  Jupi Home   Future Jupi
    Android      Windows      Hardware
                                │
                              ESP32
                                │
                         Smart Home/etc.
```

For V1, ONLY the Windows client is being built.

---

# 3. TECHNOLOGY

Use:

* C#
* .NET 8
* WPF
* HttpClient
* standard .NET libraries where practical

Do NOT use:

* Electron
* Chromium desktop wrappers
* WinForms
* WinUI 3
* MAUI
* Python GUI
* Godot

The application should be genuinely native Windows software.

---

# 4. PROJECT SEPARATION

Expected project:

```text
jupi-home/
└── src/
    └── JupiHome/
```

Saturnia exists separately.

Do not move Jupi Home into Saturnia.

Do not copy Saturnia into Jupi Home.

Do not modify Saturnia.

---

# 5. SATURNIA ARCHITECTURE

Saturnia is the existing Python backend.

Important components include:

* main.py
* app/core/web.py
* app/core/brain.py
* app/core/personality.py
* app/core/memory.py
* app/core/router.py
* math engines
* quirks.py
* Gemini integration

The core intelligence pipeline is:

```text
User
 ↓
Jupi Home
 ↓
HTTP
 ↓
Flask
 ↓
brain.think()
 ↓
router / memory / math / personality / Gemini
 ↓
response
 ↓
Jupi Home
```

Jupi Home must remain a client.

---

# 6. EXISTING API

Chat endpoint:

```text
POST http://127.0.0.1:5000/api/chat
```

Request:

```json
{
    "message": "<user message>"
}
```

Response:

```json
{
    "response": "<assistant response>"
}
```

Jupi Home communicates with Saturnia through this API.

Do NOT call Gemini directly.

Do NOT expose Gemini credentials.

---

# 7. STATUS ENDPOINT

Current status check:

```text
GET http://127.0.0.1:5000/
```

Use this for connection monitoring.

Do NOT create a new Saturnia health endpoint.

Do not hammer the server with excessive polling.

---

# 8. SATURNIA STARTUP

Jupi Home should eventually behave like:

```text
Launch Jupi Home
      ↓
Check Saturnia
      ↓
Already running?
   ↙       ↘
 YES       NO
  ↓         ↓
Connect   Start Saturnia
```

Startup must be configurable.

Do not make unsafe assumptions about:

* Python installation
* Saturnia path
* executable location

Do not embed Saturnia inside Jupi Home.

A future packaged Saturnia runtime should be possible.

---

# 9. PHASE STATUS

## PHASE 1 — FOUNDATION

COMPLETE.

Created:

* .NET 8 WPF project
* application shell
* basic architecture
* configuration foundation
* logging foundation
* resource/theme foundation

Do not rebuild it unnecessarily.

---

## PHASE 2 — SATURNIA CONNECTION

COMPLETE.

Jupi Home can communicate with Saturnia using:

```text
POST /api/chat
```

The project has a Saturnia communication layer.

Connection monitoring exists or is being integrated into the architecture.

Do not replace working networking code without a concrete reason.

---

## PHASE 3 — CORE CHAT

COMPLETE.

The application can now demonstrate the core interaction:

```text
User types
   ↓
Jupi Home
   ↓
Saturnia
   ↓
Response
   ↓
Jupi Home
```

The application has a working initial chat interaction.

Do not rebuild Phase 3 from scratch.

---

# 10. PHASE 4 — CONVERSATION EXPERIENCE

THIS IS THE NEXT PHASE.

Implement ONLY Phase 4 when explicitly instructed.

Goals:

### New Chat

Provide a clear:

**New Chat**

action.

Starting a new UI conversation must NOT delete Saturnia's permanent memory.

Do not modify:

```text
saturnia_memory.json
```

---

### Conversation History

Jupi Home should support a proper history experience.

Intended UX:

```text
Previous conversation
Previous conversation
Previous conversation

+ New Chat
```

The user should be able to select a previous conversation.

The user should be able to continue it.

---

# 11. IMPORTANT HISTORY DISTINCTION

Saturnia currently has several different concepts of history.

Do NOT confuse them.

### Saturnia long-term memory

Controlled by Saturnia.

Example:

```text
memory.py
saturnia_memory.json
```

Jupi Home does not control this in V1.

### Saturnia in-process conversation context

This exists inside Saturnia.

Jupi Home should not pretend that its local history automatically equals this context.

### Jupi Home local UI history

This can be stored locally by Jupi Home.

It represents what the Jupi Home interface remembers.

These systems must remain conceptually separate.

Do NOT fake a backend history API.

---

# 12. LOCAL HISTORY

If implementing local history in V1:

Store it using a sensible local application-data location.

Do not put random history files in the source repository.

Do not store secrets.

Do not call local UI history "Saturnia memory."

Use a clean model such as:

```text
Conversation
 ├── Id
 ├── Title
 ├── CreatedAt
 ├── UpdatedAt
 └── Messages[]
```

Messages should contain appropriate information such as:

```text
Message
 ├── Id
 ├── Role
 ├── Content
 └── Timestamp
```

Keep the model simple.

---

# 13. HISTORY UX

History should not dominate the application.

Possible layout:

```text
┌────────────┬───────────────────────────────┐
│ History    │                               │
│            │          Conversation         │
│ Chat 1     │                               │
│ Chat 2     │                               │
│ Chat 3     │                               │
│            │                               │
│ + New Chat │                               │
│            │                               │
│            │                               │
└────────────┴───────────────────────────────┘
```

Do not create a giant permanent sidebar.

The history area should be visually restrained.

---

# 14. MARKDOWN

Saturnia responses may contain Markdown.

Support:

* headings
* bold
* italic
* unordered lists
* ordered lists
* inline code
* fenced code blocks
* links where appropriate

Rendering should be readable.

Do not make Markdown look like a generic web page.

---

# 15. CODE BLOCKS

Code blocks should have:

* readable monospace typography
* clear separation
* sensible formatting
* Copy button

Copy must copy the actual code.

Do not execute code.

Do not preview arbitrary code.

Do not add a terminal execution system.

---

# 16. MESSAGE ACTIONS

Provide appropriate actions.

At minimum:

**Copy**

For user messages where technically supported:

**Edit**

If true editing/re-generation would require unsupported Saturnia functionality:

Do not fake it.

Instead:

* provide safe local editing behavior where possible
* clearly separate it from backend conversation mutation
* prepare the architecture for future support

---

# 17. V1 FEATURES

Jupi Home V1 ultimately includes:

* native WPF window
* conversation interface
* Saturnia HTTP communication
* connection status
* thinking indicator
* text input
* Enter = Send
* Shift+Enter = newline
* animated paper plane
* New Chat
* conversation history
* local history where appropriate
* Markdown
* code blocks
* Copy
* Edit where supported
* local logging
* update indication architecture
* native Windows window behavior

---

# 18. FEATURES NOT IN V1

Do NOT implement:

* microphone
* voice input
* text-to-speech
* wake word
* always listening
* PC control
* autonomous computer actions
* arbitrary command execution
* ESP32
* Arduino
* smart-home control
* full notification system
* browser integration
* Google search integration
* side-panel tools
* fake confidence scores
* satisfaction meters
* dark mode

These are future work.

---

# 19. UI DESIGN

Jupi Home must feel like a real application.

Design qualities:

* minimal
* light
* warm
* clean
* technical
* friendly
* restrained
* expressive

The UI should not feel like an automatically generated AI dashboard.

---

# 20. EXPLICIT "DO NOT DO" VISUAL RULES

DO NOT make Jupi Home:

* black futuristic
* neon cyberpunk
* glowing blue everywhere
* giant AI-brain themed
* robot-themed
* generic ChatGPT clone
* pure white with blue buttons
* giant-card based
* excessive glassmorphism
* excessive gradients
* excessive pills
* excessive shadows
* excessive rounded rectangles
* game-like
* HUD-like
* filled with random particles
* filled with unnecessary animations
* mostly empty white space

Do not use:

"black + glowing blue + futuristic robot"

as the design language.

Also do not use:

"white + blue SaaS dashboard"

as the design language.

Jupi should have its own identity.

---

# 21. LIGHT THEME

V1 is light theme only.

Do not implement dark mode yet.

Use restrained neutral tones.

The interface should have enough hierarchy to avoid becoming a blank white page.

Do not rely entirely on blue.

Do not make the UI unnecessarily colorful.

---

# 22. TYPOGRAPHY

Preferred Google fonts:

**Handjet**

and:

**Rum Raisin**

Use Handjet preferentially for Jupi branding/headings where appropriate.

Rum Raisin may be used for the J/branding treatment.

DO NOT use decorative fonts everywhere.

Conversation text must remain highly readable.

If fonts are not available locally:

* create a typography system allowing them to be added
* use sensible fallbacks
* do not download random unofficial font files

Typography is part of Jupi's identity.

---

# 23. CHAT DESIGN

Messages should feel like normal conversation.

Do NOT use huge speech bubbles.

Do NOT put every message inside giant rounded cards.

Use:

* typography
* spacing
* subtle alignment
* small visual differences

to distinguish user and assistant.

The interface should feel calm.

---

# 24. INPUT

The input area should support:

```text
Enter       → Send
Shift+Enter → New line
```

The input must remain responsive.

If sending fails, retain the message where sensible.

Prevent accidental duplicate sends.

---

# 25. SEND BUTTON

Use an animated paper-plane concept.

The animation should be:

* short
* subtle
* polished
* purposeful

Do not make the paper plane fly across the entire screen.

The interaction should communicate:

"Message sent."

---

# 26. THINKING STATE

When waiting for Saturnia, show subtle animated dots.

Example:

```text
Thinking
Thinking.
Thinking..
```

Do not use giant loading animations.

Do not freeze the whole interface.

---

# 27. CONNECTION STATUS

Display connection state around the input/status region and lower-left area where appropriate.

Connected:

```text
Connected
```

Disconnected example:

```text
Disconnected
Can't fetch answers. Make sure to check your internet :)
```

Use friendly wording.

The status should not dominate the UI.

---

# 28. ERROR HANDLING

Handle:

* Saturnia offline
* connection refused
* timeout
* HTTP 400
* unexpected HTTP status
* malformed JSON
* malformed response
* backend/Gemini error strings
* application exceptions

The UI must not crash because Saturnia is offline.

Do not pretend failed requests succeeded.

---

# 29. SATURNIA PERSONALITY

Saturnia's personality remains in:

```text
personality.py
```

Do NOT duplicate it.

Jupi Home is not responsible for personality generation.

Future visual states may represent actual Saturnia information.

Do NOT invent fake confidence values.

Never display arbitrary:

```text
Confidence: 97%
```

unless Saturnia actually supplies such information.

---

# 30. FUTURE SIDE PANEL

Jupi Home will eventually support a contextual side panel.

Possible future contents:

* browser/search-style information
* sources
* weather
* contextual information
* tools
* additional assistant output

Do NOT fully implement this now.

Build the application so the side panel can later be added without rebuilding the entire UI.

Do not reserve half the screen for an empty placeholder.

---

# 31. FUTURE POSITIVE INTERACTION VISUALS

Jupi may eventually react visually to particularly successful interactions.

Possible future behavior:

* subtle animation
* small acknowledgment
* tasteful transitions

Do NOT implement:

* satisfaction meter
* points
* gamification
* fake emotional claims

Keep V1 restrained.

---

# 32. LOGGING

Maintain useful local logs.

Log:

* application startup
* shutdown
* Saturnia startup attempts
* connection changes
* HTTP failures
* timeouts
* unexpected application exceptions

Do NOT log:

* API keys
* passwords
* secrets
* unnecessary private conversation content

---

# 33. UPDATE INDICATION

V1 does not need a complete automatic updater.

The application may contain architecture/UI for:

```text
Jupi Home update available
```

But do not fake update information.

Only show it when an actual update source later confirms an update.

---

# 34. WINDOWS EXPERIENCE

Jupi Home must behave like a normal native Windows application.

Support:

* minimize
* maximize
* close
* resize
* sensible minimum dimensions
* keyboard navigation
* focus management
* clean shutdown

Do not create a browser-like application.

---

# 35. PERFORMANCE

Keep the app lightweight.

Avoid unnecessary dependencies.

Do not block the UI thread.

Network operations must be asynchronous.

Avoid:

* unnecessary background loops
* excessive polling
* excessive animation
* memory leaks
* giant dependencies

---

# 36. SECURITY

Jupi Home is a local client.

Never store Gemini credentials.

Never expose Saturnia secrets.

Never execute arbitrary commands from Saturnia output.

Never implement PC control in V1.

Never treat AI responses as executable instructions.

---

# 37. TESTING

After each phase:

1. Build.
2. Run.
3. Test the relevant functionality.
4. Check compilation errors.
5. Check relevant warnings.
6. Verify behavior.
7. Report what was actually tested.

Do not claim something works without testing it.

---

# 38. DEVELOPMENT PHILOSOPHY

Use the following priority:

```text
Reliability
    >
Clarity
    >
Maintainability
    >
Native Windows behavior
    >
Jupi identity
    >
Extra features
```

Do not optimize for number of files.

Do not optimize for amount of generated code.

Do not over-engineer.

---

# 39. FUTURE DEVELOPMENT PHASES

After Phase 4:

## PHASE 5 — VISUAL IDENTITY

* typography refinement
* Handjet
* Rum Raisin
* Jupi branding
* light theme polish
* spacing
* subtle animations
* refined status states

## PHASE 6 — FUTURE EXTENSIONS

Prepare architecture for:

* side panel
* contextual web information
* weather
* sources
* notifications
* voice
* wake word
* PC tools
* smart-home
* ESP32
* physical Jupi

These are NOT V1 core features.

---

# 40. LONG-TERM ARCHITECTURE

Eventually:

```text
                       SATURNIA
                          │
              ┌───────────┼────────────┐
              │           │            │
         Jupi Mobile  Jupi Home    Physical Jupi
              │           │            │
              │           │          ESP32
              │           │            │
              └───────────┼────────────┘
                          │
                     Future tools
                          │
              ┌───────────┼─────────────┐
              │           │             │
           Browser      PC tools     Smart Home
```

Do not build this entire ecosystem now.

Build the foundation that makes it possible later.

---

# 41. CURRENT COMMAND

Phases 1–3 are complete.

The next phase is Phase 4.

When explicitly instructed:

**Proceed to Phase 4 only.**

Implement:

* New Chat
* conversation history
* local history architecture
* conversation selection
* Markdown
* code blocks
* Copy
* Edit where technically supported

Do not modify Saturnia.

Do not implement Phase 5.

Do not implement Phase 6.

After Phase 4:

1. Build.
2. Run.
3. Test.
4. Report files changed.
5. Report tests performed.
6. Report any limitations.
7. STOP.

Wait for explicit approval before continuing.

---

# FINAL PRINCIPLE

Jupi Home should feel like a real personal desktop assistant.

Not:

"AI-generated demo."

Not:

"generic chatbot."

Not:

"futuristic dashboard."

It should feel like **Jupi**.

Build carefully.

Keep Saturnia untouched.

Keep the architecture clean.

Build one layer at a time.

update -all of it is done
 