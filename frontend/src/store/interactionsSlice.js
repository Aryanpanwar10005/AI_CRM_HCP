import { createSlice } from '@reduxjs/toolkit';

const interactionsSlice = createSlice({
  name: 'interactions',
  initialState: {
    list: [],
    loading: false,
    error: null
  },
  reducers: {
    setInteractions: (state, action) => {
      state.list = action.payload;
    },
    addInteraction: (state, action) => {
      state.list.unshift(action.payload);
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    }
  }
});

export const { setInteractions, addInteraction, setLoading } = interactionsSlice.actions;
export default interactionsSlice.reducer;
