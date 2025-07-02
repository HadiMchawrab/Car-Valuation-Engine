import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import API_BASE_URL from '../../config/api';
import '../../styles/ContributorDetail.css';

const ContributorDetail = () => {
  const { sellerId } = useParams();
  const location = useLocation();
  const [contributorData, setContributorData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchContributorData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/analytics/contributor/${encodeURIComponent(sellerId)}`);
      if (!response.ok) {
        throw new Error('Failed to fetch contributor data');
      }
      
      const data = await response.json();
      setContributorData(data);
    } catch (err) {
      console.error('Error fetching contributor data:', err);
      setError('Failed to load contributor data. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [sellerId]);

  useEffect(() => {
    fetchContributorData();
  }, [fetchContributorData]);

  const formatDailyData = (dailyData) => {
    return dailyData.map(item => ({
      day: new Date(item.day).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }),
      listings: item.listings_count,
      avgPrice: Math.round(item.avg_price || 0)
    }));
  };

  const formatBrandData = (brandData) => {
    const colors = ['#4ade80', '#22c55e', '#16a34a', '#15803d', '#166534', '#14532d'];
    return brandData.slice(0, 6).map((item, index) => ({
      ...item,
      fill: colors[index % colors.length]
    }));
  };

  // Get listingId from location state if present
  const listingId = location.state && location.state.listingId;

  if (loading) {
    return (
      <div className="contributor-detail-page">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading contributor data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="contributor-detail-page">
        <div className="error-state">
          <p className="error-message">{error}</p>
          <Link to="/analytics" className="back-button">
            ← Back to Analytics
          </Link>
        </div>
      </div>
    );
  }

  if (!contributorData) {
    return (
      <div className="contributor-detail-page">
        <div className="error-state">
          <p className="error-message">Contributor not found</p>
          <Link to="/analytics" className="back-button">
            ← Back to Analytics
          </Link>
        </div>
      </div>
    );
  }

  const { contributor, daily_distribution, brand_distribution } = contributorData;
  const dailyChartData = formatDailyData(daily_distribution);
  const brandChartData = formatBrandData(brand_distribution);

  return (
    <div className="contributor-detail-page">
      {/* Return to Car Detail button if navigated from a listing */}
      {listingId && (
        <Link to={`/listing/${listingId}`} className="back-button">
          ← Return to Car Detail
        </Link>
      )}
      <div className="contributor-header">
        <Link to="/analytics" className="back-button">
          ← Back to Analytics
        </Link>
        
        <div className="contributor-info">
          <h1>
            {contributor.contributor_type === 'agency' ? '🏢' : '👤'} {contributor.seller_name}
          </h1>
          {contributor.contributor_type === 'agency' && (
            <p className="agency-name">Agency</p>
          )}
          {contributor.contributor_type === 'individual_seller' && (
            <p className="agency-name">Individual Seller</p>
          )}
          <div className="contributor-badges">
            {contributor.seller_id && (
              <span className="badge">ID: {contributor.seller_id}</span>
            )}
            {contributor.agency_id && (
              <span className="badge">Agency ID: {contributor.agency_id}</span>
            )}
            {contributor.contributor_type && (
              <span className="badge">Type: {contributor.contributor_type.replace('_', ' ').toUpperCase()}</span>
            )}
          </div>
        </div>
        
        {contributor.contributor_type === 'agency' && !contributor.agency_id ? (
          <button className="view-listings-btn" disabled title="No agency ID available for this agency">
            🚗 View All Listings
          </button>
        ) : (
          <Link 
            to={`/?seller=${encodeURIComponent(
              contributor.contributor_type === 'agency'
                ? contributor.agency_id
                : contributor.seller_name
            )}&sellerType=${contributor.contributor_type === 'agency' ? 'business' : 'individual'}&sellerDisplayName=${encodeURIComponent(contributor.seller_name)}`}
            className="view-listings-btn"
          >
            🚗 View All Listings
          </Link>
        )}
      </div>

      <div className="contributor-stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <h3>Total Listings</h3>
            <p className="stat-number">{contributor.total_listings}</p>
          </div>
        </div>

        {/* <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <h3>Average Price</h3>
            <p className="stat-number">${Math.round(contributor.average_price || 0).toLocaleString()}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💵</div>
          <div className="stat-content">
            <h3>Total Value</h3>
            <p className="stat-number">${Math.round(contributor.total_value || 0).toLocaleString()}</p>
          </div>
        </div> */}

        <div className="stat-card">
          <div className="stat-icon">📅</div>
          <div className="stat-content">
            <h3>Active Since</h3>
            <p className="stat-number">
              {new Date(contributor.first_listing_date).toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>

      <div className="charts-container">
        {/* <div className="chart-section">
          <h2>📈 Daily Listing Distribution</h2>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={dailyChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis 
                  dataKey="day" 
                  stroke="var(--text-secondary)"
                  fontSize={12}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis 
                  stroke="var(--text-secondary)"
                  fontSize={12}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    color: 'var(--text-primary)'
                  }}
                />
                <Legend />
                <Bar 
                  dataKey="listings" 
                  fill="#4ade80" 
                  name="Listings Count"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div> */}

        <div className="chart-section">
          <h2>🚗 Brand Distribution</h2>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={400}>
              <PieChart>
                <Pie
                  data={brandChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ brand, count, percent }) => `${brand}: ${count} (${(percent * 100).toFixed(0)}%)`}
                  outerRadius={120}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {brandChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    color: 'var(--text-primary)'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-section full-width">
          <h2>📊 Listing Trend Over Time</h2>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dailyChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis 
                  dataKey="day" 
                  stroke="var(--text-secondary)"
                  fontSize={12}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis 
                  stroke="var(--text-secondary)"
                  fontSize={12}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    color: 'var(--text-primary)'
                  }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="listings" 
                  stroke="#4ade80" 
                  strokeWidth={3}
                  dot={{ fill: '#4ade80', strokeWidth: 2, r: 6 }}
                  name="Listings Count"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="additional-info">
        <div className="info-card">
          <h3>Activity Timeline</h3>
          <div className="timeline-info">
            <p><strong>First Listing:</strong> {new Date(contributor.first_listing_date).toLocaleDateString()}</p>
            <p><strong>Latest Listing:</strong> {new Date(contributor.last_listing_date).toLocaleDateString()}</p>
            <p><strong>Total Period:</strong> {Math.ceil((new Date(contributor.last_listing_date) - new Date(contributor.first_listing_date)) / (1000 * 60 * 60 * 24))} days</p>
          </div>
        </div>

        <div className="info-card">
          <h3>Performance Metrics</h3>
          <div className="metrics-info">
            <p><strong>Average listings per day:</strong> {(contributor.total_listings / Math.max(1, daily_distribution.length)).toFixed(1)}</p>
            <p><strong>Most active day:</strong> {daily_distribution.length > 0 ? 
              dailyChartData.reduce((max, curr) => curr.listings > max.listings ? curr : max, dailyChartData[0])?.day : 'N/A'
            }</p>
            <p><strong>Primary brand:</strong> {brand_distribution.length > 0 ? brand_distribution[0].brand : 'N/A'}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContributorDetail;
