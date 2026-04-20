import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LogInteractionPage from './pages/LogInteractionPage';
import Dashboard from './pages/Dashboard';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/log-interaction" element={<LogInteractionPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
