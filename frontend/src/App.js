import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import ListingsPage from './components/ListingsPage';
import ListingDetail from './components/ListingDetail';
import Analytics from './components/Analytics';
import ContributorDetail from './components/Analytics/ContributorDetail';
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
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/analytics/contributor/:sellerId" element={<ContributorDetail />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
