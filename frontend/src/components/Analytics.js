import React, { useState, useEffect, useCallback } from 'react';
import { FaCar, FaCalendarAlt, FaChartBar, FaTrophy, FaChartLine, FaDollarSign } from 'react-icons/fa';
import TopContributors from './Analytics/TopContributors';
import DepreciationAnalysis from './Analytics/DepreciationAnalysis';
import PriceSpreadAnalysis from './Analytics/PriceSpreadAnalysis';
import API_BASE_URL from '../config/api';
import '../styles/Analytics.css';

const Analytics = () => {
  const [analyticsStats, setAnalyticsStats] = useState(null);
  const [activeSection, setActiveSection] = useState('overview'); // 'overview', 'contributors', 'depreciation', 'price-spread'
  const [filters, setFilters] = useState({
    websites: null // null means all websites
  });
  const [websiteOptions, setWebsiteOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // --- Website Filter UI logic ---
  const [dropdownValue, setDropdownValue] = useState('');

  // Fetch website options on mount
  useEffect(() => {
    const fetchWebsites = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/websites`);
        if (!response.ok) throw new Error('Failed to fetch website options');
        const data = await response.json();
        setWebsiteOptions(data);
      } catch (err) {
        setWebsiteOptions([]);
      }
    };
    fetchWebsites();
  }, []);

  // Initialize website filter to null on mount
  useEffect(() => {
    setFilters({ websites: null });
    setDropdownValue('');
  }, []); // Only run on mount

  const handleDropdownChange = (e) => {
    const value = e.target.value;
    if (value === 'ALL') {
      setFilters({ websites: null });
      setDropdownValue('');
    } else if (value) {
      let newWebsites = filters.websites ? [...filters.websites] : [];
      if (!newWebsites.includes(value)) {
        newWebsites.push(value);
      }
      setFilters({ websites: newWebsites });
      setDropdownValue('');
    }
  };

  const handleRemoveWebsite = (site) => {
    if (site === 'ALL') {
      setFilters({ websites: null });
    } else {
      const newWebsites = (filters.websites || []).filter(w => w !== site);
      setFilters({ websites: newWebsites.length === 0 ? null : newWebsites });
    }
  };

  const renderWebsiteChips = () => {
    if (!filters.websites || filters.websites.length === 0) {
      return (
        <div className="website-chips">
          <span className="website-chip all-websites">
            All Websites
          </span>
        </div>
      );
    }
    return (
      <div className="website-chips">
        {filters.websites.map(site => (
          <span className="website-chip selected-website" key={site}>
            {site}
            <button className="chip-remove" onClick={() => handleRemoveWebsite(site)}>×</button>
          </span>
        ))}
        <button 
          className="clear-all-button" 
          onClick={() => setFilters({ websites: null })}
          title="Clear all website filters"
        >
          Clear All
        </button>
      </div>
    );
  };

  const renderWebsiteFilter = () => (
    <div className="website-filter-bar">
      <label htmlFor="website-select">Website:</label>
      <select
        id="website-select"
        value={dropdownValue}
        onChange={handleDropdownChange}
      >
        <option value="" disabled>Select website...</option>
        <option value="ALL">All Websites</option>
        {websiteOptions.filter(site => !filters.websites || !filters.websites.includes(site)).map(site => (
          <option key={site} value={site}>{site}</option>
        ))}
      </select>
      {renderWebsiteChips()}
    </div>
  );

  const fetchAnalyticsStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Build URL with query parameters
      const url = new URL(`${API_BASE_URL}/api/analytics/stats`);
      
      // Add websites parameter if there are selected websites
      if (filters.websites && filters.websites.length > 0) {
        url.searchParams.set('websites', filters.websites.join(','));
      }
      
      console.log('Analytics - Requesting URL:', url.toString()); // Debug log
      
      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      if (!response.ok) {
        throw new Error('Failed to fetch analytics stats');
      }
      const data = await response.json();
      setAnalyticsStats(data);
    } catch (err) {
      console.error('Error fetching analytics stats:', err);
      setError('Failed to load analytics data. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Fetch analytics stats on component mount and when filters change
  useEffect(() => {
    fetchAnalyticsStats();
  }, [fetchAnalyticsStats]);

  const renderActiveSection = () => {
    switch (activeSection) {
      case 'contributors':
        return <TopContributors filters={filters} onRemoveWebsite={handleRemoveWebsite} />;
      case 'depreciation':
        return <DepreciationAnalysis />;
      case 'price-spread':
        return <PriceSpreadAnalysis />;
      default:
        return (
          <div className="analytics-overview">
            {/* Filter Status Display */}
            {filters.websites && filters.websites.length > 0 && (
              <div className="filter-status">
                <span className="filter-label">Showing data for:</span>
                <div className="website-filter-buttons">
                  {filters.websites.map(site => (
                    <button 
                      key={site}
                      className="website-filter-button"
                      onClick={() => handleRemoveWebsite(site)}
                    >
                      {site}
                      <span className="remove-icon">×</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            <div className="analytics-stats">
              <div className="stat-card">
                <FaCar className="stat-icon" />
                <div className="stat-content">
                  <h3>Total Listings</h3>
                  <p className="stat-number">
                    {analyticsStats ? analyticsStats.total_listings.toLocaleString() : '0'}
                  </p>
                </div>
              </div>

              <div className="stat-card">
                <FaCalendarAlt className="stat-icon" />
                <div className="stat-content">
                  <h3>This Month</h3>
                  <p className="stat-number">
                    {analyticsStats ? analyticsStats.listings_this_month.toLocaleString() : '0'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        );
    }
  };

  if (loading) {
    return (
      <div className="analytics-page">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading analytics data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-page">
        <div className="error-state">
          <p className="error-message">{error}</p>
          <button onClick={fetchAnalyticsStats} className="retry-button">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1><FaChartBar /> Analytics Dashboard</h1>
        <p className="analytics-subtitle">
          Explore car listing trends and market insights
        </p>
      </div>

      <div className="analytics-navigation">
        <button 
          className={`nav-btn ${activeSection === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveSection('overview')}
        >
          <FaChartLine /> Overview
        </button>
        <button 
          className={`nav-btn ${activeSection === 'contributors' ? 'active' : ''}`}
          onClick={() => setActiveSection('contributors')}
        >
          <FaTrophy /> Top Contributors
        </button>
        <button 
          className={`nav-btn ${activeSection === 'depreciation' ? 'active' : ''}`}
          onClick={() => setActiveSection('depreciation')}
        >
          <FaChartLine /> Depreciation Analysis
        </button>
        <button 
          className={`nav-btn ${activeSection === 'price-spread' ? 'active' : ''}`}
          onClick={() => setActiveSection('price-spread')}
        >
          <FaDollarSign /> Price Spread Analysis
        </button>
      </div>

      <div className="analytics-container">
        {/* Show website filter only for overview and contributors */}
        {(activeSection === 'overview' || activeSection === 'contributors') && renderWebsiteFilter()}
        <div className="main-content">
          {renderActiveSection()}
        </div>
      </div>
    </div>
  );
};

export default Analytics;

