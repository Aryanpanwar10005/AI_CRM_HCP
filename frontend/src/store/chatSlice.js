import { createSlice } from '@reduxjs/toolkit';

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [
      {
        role: "assistant",
        content: "Hi! I am your AI assistant. Describe your visit with an HCP and I will automatically fill the interaction form. You can also ask me to edit details, check compliance, or suggest the next best action.",
        timestamp: new Date().toISOString()
      }
    ],
    isTyping: false,
    sessionId: `session_${Date.now()}`,
    error: null
  },
  reducers: {
    addMessage: (state, action) => {
      state.messages.push({
        ...action.payload,
        timestamp: new Date().toISOString()
      });
    },
    setTyping: (state, action) => {
      state.isTyping = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    }
  }
});

export const { addMessage, setTyping, setError } = chatSlice.actions;
export default chatSlice.reducer;
