import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { FaTrophy } from 'react-icons/fa';
import API_BASE_URL from '../../config/api';
import '../../styles/TopContributors.css';

const TopContributors = ({ filters }) => {
  const [contributors, setContributors] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchContributors = useCallback(async () => {
    setLoading(true);
    
    try {
      // Build URL with query parameters
      const url = new URL(`${API_BASE_URL}/api/analytics/contributors`);
      url.searchParams.set('limit', '20');
      
      // Add websites parameter if there are selected websites
      if (filters.websites && filters.websites.length > 0) {
        url.searchParams.set('websites', filters.websites.join(','));
      }

      console.log('TopContributors - Requesting URL:', url.toString()); // Debug log

      // Use GET with query parameters
      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch contributors');
      }
      
      const data = await response.json();
      setContributors(data.contributors || []);
    } catch (err) {
      console.error('Error fetching contributors:', err);
      setContributors([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchContributors();
  }, [fetchContributors]);

  if (loading) {
    return (
      <div className="top-contributors">
        <h2 style={{ color: '#fff' }}><FaTrophy style={{ marginRight: 8, color: '#bfa100' }} />Top Contributors</h2>
        <div className="loading-contributors">
          <div className="loading-spinner"></div>
          <p>Calculating contributor statistics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="top-contributors">
      <div className="contributors-header">
        <h2 style={{ color: '#fff' }}><FaTrophy style={{ marginRight: 8, color: '#bfa100' }} />Top Contributors</h2>
        <p className="contributors-subtitle">
          Sellers with the most listings
        </p>
      </div>

      {contributors.length === 0 ? (
        <div className="no-contributors">
          <p>No contributor data available for the selected filters.</p>
          {filters.websites && filters.websites.length > 0 && (
            <p>Filtered by: {filters.websites.join(', ')}</p>
          )}
        </div>
      ) : (
        <>
          {filters.websites && filters.websites.length > 0 && (
            <div className="contributors-filter-info">
              <p>Showing contributors from: <strong>{filters.websites.join(', ')}</strong></p>
            </div>
          )}
          <div className="contributors-grid">
            {contributors.map((contributor, index) => (
              <Link
                key={contributor.seller_id || contributor.seller_name}
                to={`/analytics/contributor/${encodeURIComponent(contributor.seller_name)}?type=${contributor.contributor_type || (contributor.agency_name ? 'agency' : 'seller')}`}
                className="contributor-card"
              >
                <div className="contributor-rank">
                  #{index + 1}
                </div>
                
                <div className="contributor-info">
                  <span className="contributor-name-small">
                    {contributor.seller_name}
                  </span>
                  <div className="contributor-details-row">
                    <span className="contributor-website">
                      {contributor.website}
                    </span>
                    <div className="contributor-listings">
                      <span className="listings-label">Total Listings:</span>
                      <span className="listings-value">{contributor.total_listings}</span>
                    </div>
                  </div>
                </div>
                
                <div className="contributor-arrow">
                  →
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default TopContributors; 