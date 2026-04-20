import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  interaction_id: null,
  hcp_name: "",
  hcp_id: null,
  date: new Date().toISOString().split('T')[0],
  time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }),
  mode: "Meeting",
  product_discussed: "",
  sentiment: "Neutral",
  materials_shared: "",
  key_topics: "",
  outcome: "",
  follow_up_date: "",
  follow_up_notes: "",
  compliance_consent: false,
  status: "Draft",
  
  // UI State
  isFormDirty: false,
  highlightedFields: [],
  isSaving: false,
  saveSuccess: false
};

const formSlice = createSlice({
  name: 'form',
  initialState,
  reducers: {
    updateField: (state, action) => {
      const { name, value } = action.payload;
      state[name] = value;
      state.isFormDirty = true;
    },
    updateFromAI: (state, action) => {
      const updates = action.payload;
      const highlighted = [];
      
      Object.keys(updates).forEach(key => {
        if (key in state && key !== 'highlightedFields') {
          state[key] = updates[key];
          highlighted.push(key);
        }
      });
      
      state.highlightedFields = highlighted;
      state.isFormDirty = true;
    },
    clearHighlights: (state) => {
      state.highlightedFields = [];
    },
    resetForm: (state) => {
      return {
        ...initialState,
        highlightedFields: [],
        isFormDirty: false
      };
    },
    setSaving: (state, action) => {
      state.isSaving = action.payload;
    },
    setSaveSuccess: (state, action) => {
      state.saveSuccess = action.payload;
    }
  }
});

export const { updateField, updateFromAI, clearHighlights, resetForm, setSaving, setSaveSuccess } = formSlice.actions;
export default formSlice.reducer;
