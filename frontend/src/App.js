import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import ListingsPage from './components/ListingsPage';
import ListingDetail from './components/ListingDetail';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Navbar />
        <div className="content">
          <Routes>
            <Route path="/" element={<ListingsPage />} />
            <Route path="/listing/:id" element={<ListingDetail />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
