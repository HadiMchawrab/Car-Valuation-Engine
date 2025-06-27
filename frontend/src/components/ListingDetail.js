import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import '../styles/ListingDetail.css';
import { getTransmissionType, getBodyType } from '../utils/mappings';
import API_BASE_URL from '../config/api';

const ListingDetail = () => {

  const { id } = useParams();
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchListingDetail = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`${API_BASE_URL}/listings/${id}`);
        setListing(response.data);
        setLoading(false);
      } catch (err) {
        setError('Error fetching listing details. Please try again later.');
        setLoading(false);
        console.error('Error fetching listing detail:', err);
      }
    };

    fetchListingDetail();  }, [id]);

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (!listing) {
    return <div className="not-found">Listing not found</div>;
  }  // In new schema, we have a single image URL
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
                <div className="detail-value">{listing.color}</div>
              </div>
            )}
            {listing.seller_type && (
              <div className="detail-row">
                <div className="detail-label">Seller Type</div>
                <div className="detail-value">{listing.seller_type}</div>
              </div>
            )}
          </div>
          
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
