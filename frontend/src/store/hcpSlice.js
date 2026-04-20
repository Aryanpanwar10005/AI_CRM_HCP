import { createSlice } from '@reduxjs/toolkit';

const hcpSlice = createSlice({
  name: 'hcps',
  initialState: {
    list: [],
    selectedHcp: null,
    loading: false,
    error: null
  },
  reducers: {
    setHcps: (state, action) => {
      state.list = action.payload;
    },
    setSelectedHcp: (state, action) => {
      state.selectedHcp = action.payload;
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    }
  }
});

export const { setHcps, setSelectedHcp, setLoading } = hcpSlice.actions;
export default hcpSlice.reducer;
