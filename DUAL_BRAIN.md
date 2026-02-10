# 🧠 Dual Brain Architecture: Titan Core vs. LangGraph

This document defines the separation of concerns between the two AI brains in the Gemini Video ecosystem. This separation is critical to prevent functional overlap and ensure scalable operations.

## 1. The Creative Strategist: Titan Core
**Engine:** Autogen (Multi-Agent System)
**Role:** "Thinking", Strategy, Research, & Design.

**Responsibilities:**
*   **Market Research:** Analyzing trends, competitor ads, and viral hooks.
*   **Angle Generation:** Brainstorming unique marketing angles and concepts.
*   **Scriptwriting:** Drafting video scripts, storyboards, and visual directions.
*   **Visual Prompting:** Generating image/video generation prompts (Midjourney, Runway).
*   **Data Entry:** Structuring creative output into the `ScriptInternal` format.

**Output:**
*   A structured JSON object (`ScriptInternal`) saved to the Database (Postgres).
*   **Status Handover:** Sets status to `READY_FOR_PRODUCTION`.

**Direct Interfaces:**
*   Meta Marketing API (Read-Only/Analysis)
*   Google Trends / YouTube Search
*   LLMs (Claude 3.5 Sonnet, GPT-4o)

---

## 2. The Operator: LangGraph App
**Engine:** LangGraph (Stateful Graph Execution)
**Role:** "Doing", Execution, Orchestration, & Interaction.

**Responsibilities:**
*   **Execution:** Picking up `READY_FOR_PRODUCTION` scripts from the DB.
*   **Asset Retrieval:** Fetching raw clips from `drive-intel` or stock libraries.
*   **Orchestration:** Calling `video-agent` to render the final video.
*   **Publishing:** Uploading finished videos to TikTok, Reels, YouTube Shorts.
*   **Community Management:** Monitoring comments and replying to users.

**Input:**
*   `ScriptInternal` objects from the Database.

**Direct Interfaces:**
*   Video Agent (Rendering Service)
*   Social Media APIs (Write Access: Upload/Comment)
*   Drive Intel (Read Access)

---

## 3. The Handover Protocol (The "Corpus Callosum")
The **PostgreSQL Database** acts as the only bridge between the two brains.

1.  **Titan Core** works in the `Ideation` phase. It finalizes a script and saves it with `status='READY_FOR_PRODUCTION'`.
2.  **LangGraph App** polls (or is event-triggered) for jobs with `status='READY_FOR_PRODUCTION'`.
3.  **LangGraph App** locks the job by setting `status='PROCESSING'`.
4.  Upon completion, **LangGraph App** sets `status='PUBLISHED'` and records performance metrics.

## 4. Anti-Patterns (What NOT to do)
*   ❌ **Titan Core should NEVER render video.** It only designs it.
*   ❌ **LangGraph App should NEVER write scripts.** It only executes them.
*   ❌ **Direct Communication:** The brains should not call each other's APIs directly if possible; they should decouple via the DB state machine.
