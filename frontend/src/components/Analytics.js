import React, { useState, useEffect, useCallback } from 'react';
import FilterPanel from './FilterPanel';
import TopContributors from './Analytics/TopContributors';
import '../styles/Analytics.css';

const Analytics = () => {
  const [analyticsStats, setAnalyticsStats] = useState(null);
  const [filters, setFilters] = useState({
    brand: '',
    model: '',
    min_year: null,
    max_year: null,
    min_price: null,
    max_price: null,
    condition: '',
    fuel_type: '',
    transmission_type: '',
    body_type: '',
    color: '',
    seller_type: '',
    website: '',
    websites: [],
    location_city: '',
    location_region: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAnalyticsStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Prepare search filters for backend
      const searchFilters = {
        ...filters,
        // Convert empty strings to null for backend
        brand: filters.brand || null,
        model: filters.model || null,
        condition: filters.condition || null,
        fuel_type: filters.fuel_type || null,
        transmission_type: filters.transmission_type || null,
        body_type: filters.body_type || null,
        color: filters.color || null,
        seller_type: filters.seller_type || null,
        website: filters.website || null,
        location_city: filters.location_city || null,
        location_region: filters.location_region || null,
        // Only include websites if some are selected
        websites: filters.websites && filters.websites.length > 0 ? filters.websites : null
      };

      // Remove null/undefined values
      const cleanFilters = Object.fromEntries(
        Object.entries(searchFilters).filter(([_, v]) => v != null)
      );

      // Use POST to send filters in request body
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/analytics/stats`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: Object.keys(cleanFilters).length > 0 ? JSON.stringify(cleanFilters) : JSON.stringify({})
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

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    // fetchAnalyticsStats will be called automatically due to useEffect dependency
  };

  const clearFilters = () => {
    const emptyFilters = {
      brand: '',
      model: '',
      min_year: null,
      max_year: null,
      min_price: null,
      max_price: null,
      condition: '',
      fuel_type: '',
      transmission_type: '',
      body_type: '',
      color: '',
      seller_type: '',
      website: '',
      websites: [],
      location_city: '',
      location_region: ''
    };
    setFilters(emptyFilters);
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
        <h1>📊 Analytics Dashboard</h1>
        <p className="analytics-subtitle">
          Explore car listing trends and top contributors
        </p>
      </div>

      <div className="analytics-container">
        <div className="sidebar">
          <FilterPanel
            filters={filters}
            onFilterChange={handleFilterChange}
            onClearFilters={clearFilters}
            resultCount={analyticsStats ? analyticsStats.total_listings : 0}
          />
        </div>

        <div className="main-content">
          <div className="analytics-stats">
            <div className="stat-card">
              <div className="stat-icon">🚗</div>
              <div className="stat-content">
                <h3>Total Listings</h3>
                <p className="stat-number">
                  {analyticsStats ? analyticsStats.total_listings.toLocaleString() : '0'}
                </p>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">💰</div>
              <div className="stat-content">
                <h3>Average Price</h3>
                <p className="stat-number">
                  ${analyticsStats ? 
                    Math.round(analyticsStats.average_price || 0).toLocaleString() :
                    '0'
                  }
                </p>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">📈</div>
              <div className="stat-content">
                <h3>Active Sellers</h3>
                <p className="stat-number">
                  {analyticsStats ? 
                    analyticsStats.total_sellers :
                    '0'
                  }
                </p>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">📅</div>
              <div className="stat-content">
                <h3>This Month</h3>
                <p className="stat-number">
                  {analyticsStats ? analyticsStats.listings_this_month.toLocaleString() : '0'}
                </p>
              </div>
            </div>
          </div>

          <TopContributors filters={filters} />
        </div>
      </div>
    </div>
  );
};

export default Analytics;
