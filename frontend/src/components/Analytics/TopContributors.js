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
      const response = await fetch(`${API_BASE_URL}/api/analytics/contributors?limit=20`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: Object.keys(cleanFilters).length > 0 ? JSON.stringify(cleanFilters) : JSON.stringify({})
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
        </div>
      ) : (
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
                <h3 className="contributor-name">
                  {contributor.seller_name}
                </h3>
                
                <div className="contributor-type">
                  {contributor.contributor_type === 'agency' ? 'Agency' : 'Individual Seller'}
                </div>
                
                <div className="contributor-listings">
                  <span className="listings-label">Total Listings:</span>
                  <span className="listings-value">{contributor.total_listings}</span>
                </div>
              </div>
              
              <div className="contributor-arrow">
                →
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default TopContributors;
