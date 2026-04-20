# APP_FLOW.md - Application Flow & Redux State Architecture
## Version 4 - Final - April 19 2026

---

## 1. URLs

Frontend (Vite dev server):  http://localhost:5173
Backend API (FastAPI):       http://localhost:8000

NO production deployment. Video is recorded from localhost only.

---

## 2. Routes

/ or /dashboard         -> Dashboard (recent interactions + upcoming follow-ups)
/log-interaction        -> Log Interaction Screen (CORE SCREEN)
/hcps                   -> HCP list
/hcps/:id               -> HCP profile + full history

---

## 3. Redux Store - Complete Structure

```
store/
  interactionsSlice   interactions[], loading, error
  hcpSlice            hcps[], selectedHCP, loading
  chatSlice           messages[], isTyping, sessionId, error
  formSlice           all left-panel form fields + UI state
  uiSlice             activeModal, sidebarOpen
```

### formSlice - Full Initial State
```js
const initialFormState = {
  // Form fields (must match API form_updates keys exactly)
  interaction_id:    null,
  hcp_name:          "",
  hcp_id:            null,
  date:              "",
  mode:              "",
  product_discussed: "",
  sentiment:         "",
  materials_shared:  "",
  key_topics:        "",
  outcome:           "",
  follow_up_date:    "",
  follow_up_notes:   "",
  status:            "completed",
  // UI state
  isFormDirty:       false,      // true once any field AI-populated
  highlightedFields: [],         // fields to animate (highlight 1500ms)
  isSaving:          false,      // true while POST /api/interactions in flight
  saveSuccess:       false,
};
```

### formSlice - Key Reducers
```js
updateFromAI: (state, action) => {
  // action.payload = form_updates from API response
  // Update ONLY fields present in payload
  Object.keys(action.payload).forEach(key => {
    if (key in state) {
      state[key] = action.payload[key];
    }
  });
  state.highlightedFields = Object.keys(action.payload);
  state.isFormDirty = true;
},
clearHighlights: (state) => {
  state.highlightedFields = [];
},
resetForm: (state) => {
  return { ...initialFormState };
},
```

### chatSlice - Full Initial State
```js
const initialChatState = {
  messages: [
    {
      role: "assistant",
      content: "Hi! I am your AI assistant. Describe your visit with an HCP and I will automatically fill the interaction form. You can also ask me to edit details, check compliance, or suggest the next best action.",
      timestamp: null,
      tool_used: null,
    }
  ],
  isTyping:  false,    // true while waiting for API (shows animated dots)
  sessionId: null,     // generated on first message, sent to backend
  error:     null,
};
```

---

## 4. Split Screen - Log Interaction (Component Tree)

```
<LogInteractionPage>
  <LeftPanel>                     // 40% width, bg: --color-left-panel
    <FormHeader>                  // "Interaction Details" title + Reset button
    <FormField name="hcp_name">   // readOnly, highlights when updated
    <FormField name="date">
    <FormField name="mode">
    <FormField name="product_discussed">
    <FormField name="sentiment">
    <FormField name="materials_shared">
    <FormField name="key_topics">
    <FormField name="outcome">
    <FormField name="follow_up_date">
    <FormField name="follow_up_notes">
    <SaveButton>                  // disabled unless hcp_name AND date filled
  </LeftPanel>

  <RightPanel>                    // 60% width, bg: --color-surface
    <ChatHeader>                  // "AI Chat Assistant" title
    <MessageList>                 // scrolls to bottom on new message
      <MessageBubble role="assistant">   // teal-tinted bg
      <MessageBubble role="user">        // white bg, right-aligned
      <TypingIndicator>          // 3 bouncing dots, shown when isTyping=true
    </MessageList>
    <ChatInput>
      <textarea>                 // multi-line, Enter to send (Shift+Enter newline)
      <SendButton>               // disabled when isTyping=true
    </ChatInput>
  </RightPanel>
</LogInteractionPage>
```

---

## 5. Complete Chat Turn - Step by Step

```
1. User types message + presses Send

2. Frontend dispatches:
   chatSlice.setTyping(true)
   chatSlice.addMessage({ role: "user", content: message })

3. Frontend calls:
   POST http://localhost:8000/api/chat
   Body: {
     message: "Visited Dr. Sharma...",
     session_id: chatSlice.sessionId,
     current_form_state: formSlice (all current fields),
     current_interaction_id: formSlice.interaction_id
   }

4. Backend receives in main.py router

5. Backend calls:
   result = graph.invoke({
     messages: [*history, HumanMessage(message)],
     current_form_state: request.current_form_state,
     current_interaction_id: request.current_interaction_id,
     form_updates: {},
     actions_taken: []
   })

6. LangGraph executes:
   agent node -> LLM decides tool_call -> tools node executes tool
   -> tool writes to state.form_updates + state.actions_taken
   -> agent node -> LLM generates final reply (no more tool_calls)
   -> END

7. Backend returns:
   {
     "reply": "Logged interaction with Dr. Sharma (ID: 6)",
     "actions_taken": ["log_interaction"],
     "interaction_id": 6,
     "form_updates": {
       "hcp_name": "Dr. Meera Sharma",
       "hcp_id": 1,
       "date": "2026-04-19",
       "mode": "visit",
       "product_discussed": "Atorvastatin 10mg",
       "sentiment": "Positive",
       "materials_shared": "Brochures",
       "key_topics": "Cholesterol management, post-MI patients",
       "outcome": "interested"
     }
   }

8. Frontend receives response:
   chatSlice.setTyping(false)
   chatSlice.addMessage({ role: "assistant", content: reply, tool_used: actions_taken[0] })
   formSlice.updateFromAI(form_updates)
   -> each key in form_updates updates matching field in Redux state
   -> highlightedFields = Object.keys(form_updates)
   -> React re-renders: each highlighted field gets CSS class "field-highlight"
   -> setTimeout 1500ms -> formSlice.clearHighlights()
```

---

## 6. Demo Scripts for All 5 Tools (Video Use)

### Tool 1: log_interaction
Input:
  "Visited Dr. Meera Sharma at Apollo Hospital today. Discussed Atorvastatin
  10mg for post-MI patients. She was very positive and requested brochures."

Expected form_updates:
  hcp_name="Dr. Meera Sharma", date="2026-04-19", mode="visit",
  product_discussed="Atorvastatin 10mg", sentiment="Positive",
  materials_shared="Brochures", outcome="interested",
  key_topics="Post-MI patients, cholesterol management"

---

### Tool 2: edit_interaction (run after Tool 1)
Input:
  "Actually it was a phone call not a visit, and her sentiment was neutral."

Expected form_updates (ONLY these 2 fields):
  mode="call", sentiment="Neutral"

All other fields must remain unchanged.

---

### Tool 3: get_hcp_profile
Input:
  "Show me Dr. Meera Sharma's profile and interaction history"

Expected: text in chat (no form update):
  "Dr. Meera Sharma | Cardiologist | Apollo Hospital, New Delhi
   Recent interactions:
   - 2026-04-15: visit - Atorvastatin 10mg (Positive)
   - 2026-04-10: call - Rosuvastatin 20mg (Neutral)"

---

### Tool 4: compliance_check
Input:
  "Can I visit Dr. Rajesh Patel again this month? Is it okay?"

Expected (seeded data has 1 visit for Patel in April):
  "COMPLIANT: Dr. Rajesh Patel has had 1 visit this month. 2 visits remaining
   before the PhRMA monthly limit of 3."

---

### Tool 5: next_best_action
Input:
  "What should I do next with Dr. Anita Verma?"

Expected (llama-3.3-70b-versatile reasoning):
  "Next Best Action for Dr. Anita Verma:
   Based on her strong interest in Insulin Glargine on April 18, recommend
   sending the Phase 3 basal insulin trial data PDF within 7 days and
   scheduling a follow-up call to discuss initiation protocols for her T1D
   patient cohort."

---

## 7. Dashboard Page

Components:
  <RecentInteractions>    GET /api/interactions?limit=10&order=newest
    Table: HCP Name | Product | Sentiment | Date | Mode | Status
    [View] button per row -> navigates to /hcps/:id

  <UpcomingFollowups>     GET /api/followups?status=pending
    Table: HCP Name | Due Date | Notes | [Mark Done] button
    [+ Log New Interaction] button -> navigates to /log-interaction

---

## 8. Error States

| Scenario                          | Frontend Behaviour                                      |
|-----------------------------------|---------------------------------------------------------|
| API timeout (>60s)                | Chat: "Request timed out. Please try again."            |
| Groq API error (500)              | Chat: "AI temporarily unavailable. Try again shortly."  |
| HCP name not found in DB          | Chat: "Could not find that HCP. Please clarify the name."|
| edit with no current interaction  | Chat: "No active interaction to edit. Log one first."   |
| Save with empty hcp_name or date  | Save button disabled - cannot submit                    |
| Network error (fetch fails)       | Chat: "Network error. Check your connection."           |

---

## 9. CSS Animation Specs

### Field Highlight (when AI fills a field)
```css
@keyframes fieldHighlight {
  0%   { background-color: var(--color-field-highlight); }
  70%  { background-color: var(--color-field-highlight); }
  100% { background-color: transparent; }
}
.field-highlight {
  animation: fieldHighlight 1.5s ease-out forwards;
}
```

### Chat Typing Indicator (3 bouncing dots)
```css
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40%           { transform: translateY(-6px); }
}
.typing-dot { width: 8px; height: 8px; border-radius: 50%;
              background: var(--color-primary); display: inline-block;
              animation: bounce 1.2s ease infinite; }
.typing-dot:nth-child(2) { animation-delay: 0.15s; }
.typing-dot:nth-child(3) { animation-delay: 0.30s; }
```

### Message bubble slide-in
```css
@keyframes slideIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.message-bubble { animation: slideIn 0.2s ease-out; }
```
