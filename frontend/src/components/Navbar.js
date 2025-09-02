import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FaHome, FaChartBar, FaBook } from 'react-icons/fa';
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
            <FaHome className="nav-icon" />
            <span className="nav-text">Home</span>
          </Link>
          <Link to="/analytics" className="nav-link">
            <FaChartBar className="nav-icon" />
            <span className="nav-text">Analytics</span>
          </Link>
          <Link to="/documentation" className="nav-link">
            <FaBook className="nav-icon" />
            <span className="nav-text">Documentation</span>
          </Link>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
