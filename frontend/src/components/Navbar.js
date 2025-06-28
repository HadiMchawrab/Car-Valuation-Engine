import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import DarkModeToggle from './DarkModeToggle';
import '../styles/Navbar.css';
import markabaLogo from '../Markaba logo.png';

const Navbar = () => {
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          <img src={markabaLogo} alt="Markaba" className="logo-image" />
          <div className="logo-text">
            <span className="logo-main">Markaba</span>
            {!isMobile && <span className="logo-subtitle">Car Listings</span>}
          </div>
        </Link>
        <div className="navbar-links">
          <Link to="/" className="nav-link">
            <span className="nav-icon">🏠</span>
            <span className="nav-text">Home</span>
          </Link>
          <Link to="/analytics" className="nav-link">
            <span className="nav-icon">�</span>
            <span className="nav-text">Analytics</span>
          </Link>
          <DarkModeToggle />
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
