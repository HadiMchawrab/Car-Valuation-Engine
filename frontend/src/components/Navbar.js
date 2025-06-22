import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/Navbar.css';

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-container">        <Link to="/" className="navbar-logo">
          <span>Markaba</span> <span className="logo-subtitle">Car Listings</span>
        </Link>
      </div>
    </nav>
  );
};

export default Navbar;
