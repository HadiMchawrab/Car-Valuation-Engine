import React from 'react';
import { useTheme } from '../context/ThemeContext';
import '../styles/DarkModeToggle.css';

const DarkModeToggle = () => {
  const { isDarkMode, toggleDarkMode } = useTheme();

  return (
    <button 
      className="dark-mode-toggle"
      onClick={toggleDarkMode}
      aria-label="Toggle dark mode"
    >
      <div className={`toggle-icon ${isDarkMode ? 'dark' : 'light'}`}>
        {isDarkMode ? '🌙' : '☀️'}
      </div>
    </button>
  );
};

export default DarkModeToggle;
