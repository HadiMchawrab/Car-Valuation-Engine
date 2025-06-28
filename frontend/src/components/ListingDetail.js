import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import '../styles/ListingDetail.css';
import { getTransmissionType, getBodyType, getColor } from '../utils/mappings';
import API_BASE_URL from '../config/api';

const ListingDetail = () => {

  const { id } = useParams();
  const [listingData, setListingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchListingDetail = async () => {
      setLoading(true);
      try {
        // Try enhanced endpoint first, fallback to regular endpoint
        let response;
        try {
          response = await axios.get(`${API_BASE_URL}/api/listings/${id}/enhanced`);
        } catch (enhancedError) {
          // Fallback to regular endpoint if enhanced fails
          response = await axios.get(`${API_BASE_URL}/listings/${id}`);
          response.data = { listing: response.data, seller_stats: null };
        }
        
        setListingData(response.data);
        setLoading(false);
      } catch (err) {
        setError('Error fetching listing details. Please try again later.');
        setLoading(false);
        console.error('Error fetching listing detail:', err);
      }
    };

    fetchListingDetail();
  }, [id]);

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (!listingData || !listingData.listing) {
    return <div className="not-found">Listing not found</div>;
  }

  const listing = listingData.listing;
  const sellerStats = listingData.seller_stats;  // In new schema, we have a single image URL
  const hasImage = listing.image_url && listing.image_url.trim() !== '';

  return (
    <div className="listing-detail-container">
      <Link to="/" className="back-button">← Back to Listings</Link>
      
      <h1 className="listing-title">{listing.title}</h1>
      
      <div className="listing-content">
        <div className="listing-images-section">
          {hasImage ? (
            <div className="image-gallery">              
              <div className="main-image-container">
                <img 
                  src={listing.image_url}
                  alt={`${listing.brand} ${listing.model}`}
                  className="main-image"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = `${process.env.PUBLIC_URL}/placeholder-car.svg`;
                  }}
                />
              </div>
            </div>
          ) : (
            <div className="no-image-container">
              <div className="no-image">No Images Available</div>
            </div>
          )}
        </div>
        
        <div className="listing-details-section">
          <div className="price-section">
            <h2>{listing.price} {listing.currency}</h2>
          </div>
            <div className="details-table">
            <div className="detail-row">
              <div className="detail-label">Brand</div>
              <div className="detail-value">{listing.brand}</div>
            </div>
            <div className="detail-row">
              <div className="detail-label">Model</div>
              <div className="detail-value">{listing.model}</div>
            </div>            <div className="detail-row">
              <div className="detail-label">Year</div>
              <div className="detail-value">{listing.year}</div>
            </div>
            <div className="detail-row">
              <div className="detail-label">Mileage</div>
              <div className="detail-value">{listing.mileage ? `${listing.mileage} km` : 'N/A'}</div>
            </div>
            <div className="detail-row">
              <div className="detail-label">Location</div>
              <div className="detail-value">
                {listing.location_city || listing.location_region ? 
                  `${listing.location_city || ''} ${listing.location_region || ''}`.trim() : 
                  'N/A'
                }
              </div>
            </div>
            <div className="detail-row">
              <div className="detail-label">Website</div>
              <div className="detail-value">{listing.website}</div>
            </div>
            <div className="detail-row">
              <div className="detail-label">Post Date</div>
              <div className="detail-value">{new Date(listing.post_date).toLocaleString()}</div>
            </div>
            {listing.fuel_type && (
              <div className="detail-row">
                <div className="detail-label">Fuel Type</div>
                <div className="detail-value">{listing.fuel_type}</div>
              </div>
            )}
            {listing.transmission_type && (
              <div className="detail-row">
                <div className="detail-label">Transmission</div>
                <div className="detail-value">{getTransmissionType(listing.transmission_type)}</div>
              </div>
            )}
            {listing.body_type && (
              <div className="detail-row">
                <div className="detail-label">Body Type</div>
                <div className="detail-value">{getBodyType(listing.body_type)}</div>
              </div>
            )}
            {listing.condition && (
              <div className="detail-row">
                <div className="detail-label">Condition</div>
                <div className="detail-value">{listing.condition}</div>
              </div>
            )}
            {listing.color && (
              <div className="detail-row">
                <div className="detail-label">Color</div>
                <div className="detail-value">{getColor(listing.color)}</div>
              </div>
            )}
            {listing.seller_type && (
              <div className="detail-row">
                <div className="detail-label">Seller Type</div>
                <div className="detail-value">{listing.seller_type}</div>
              </div>
            )}
          </div>

          {/* Enhanced Seller Information Section */}
          {(listing.seller || listing.agency_name || sellerStats) && (
            <div className="seller-info-section">
              <h3>{listing.seller ? 'Seller Information' : 'Agency Information'}</h3>
              <div className="seller-details">
                {(listing.seller || listing.agency_name) && (
                  <div className="detail-row">
                    <div className="detail-label">{listing.seller ? 'Seller' : 'Agency'}</div>
                    <div className="detail-value">{listing.seller || listing.agency_name}</div>
                  </div>
                )}
                {listing.seller_verified && (
                  <div className="detail-row">
                    <div className="detail-label">Verified</div>
                    <div className="detail-value verified">✓ Verified {listing.seller ? 'Seller' : 'Agency'}</div>
                  </div>
                )}
                {listing.is_agent && (
                  <div className="detail-row">
                    <div className="detail-label">Type</div>
                    <div className="detail-value">Licensed Agent</div>
                  </div>
                )}
              </div>

              {/* Seller Statistics */}
              {sellerStats && (
                <div className="seller-stats">
                  <h4>Seller Activity</h4>
                  <div className="stats-grid">
                    <div className="stat-item">
                      <span className="stat-number">{sellerStats.total_listings}</span>
                      <span className="stat-label">Total Listings</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-number">{sellerStats.recent_listings}</span>
                      <span className="stat-label">Recent (30 days)</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-number">
                        ${Math.round(sellerStats.average_price || 0).toLocaleString()}
                      </span>
                      <span className="stat-label">Avg. Price</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-number">
                        {sellerStats.first_listing_date ? 
                          new Date(sellerStats.first_listing_date).toLocaleDateString() : 'N/A'}
                      </span>
                      <span className="stat-label">Member Since</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          
          <div className="listing-actions">            <a 
              href={listing.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="view-original-btn"
            >
              View Original Listing
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ListingDetail;
