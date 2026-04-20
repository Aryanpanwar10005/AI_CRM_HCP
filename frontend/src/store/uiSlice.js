import { createSlice } from '@reduxjs/toolkit';

const uiSlice = createSlice({
  name: 'ui',
  initialState: {
    isSidebarOpen: true,
    activeModal: null,
    theme: 'light'
  },
  reducers: {
    toggleSidebar: (state) => {
      state.isSidebarOpen = !state.isSidebarOpen;
    },
    setActiveModal: (state, action) => {
      state.activeModal = action.payload;
    }
  }
});

export const { toggleSidebar, setActiveModal } = uiSlice.actions;
export default uiSlice.reducer;
