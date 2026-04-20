import { configureStore } from '@reduxjs/toolkit';
import formReducer from './formSlice';
import chatReducer from './chatSlice';
import hcpReducer from './hcpSlice';
import interactionsReducer from './interactionsSlice';
import uiReducer from './uiSlice';

const store = configureStore({
  reducer: {
    form: formReducer,
    chat: chatReducer,
    hcps: hcpReducer,
    interactions: interactionsReducer,
    ui: uiReducer,
  },
});

export default store;
