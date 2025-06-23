import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import '../styles/ListingDetail.css';

const ListingDetail = () => {
  const { id } = useParams();
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  useEffect(() => {
    const fetchListingDetail = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`http://localhost:8001/listings/${id}`);
        setListing(response.data);
        setLoading(false);
      } catch (err) {
        setError('Error fetching listing details. Please try again later.');
        setLoading(false);
        console.error('Error fetching listing detail:', err);
      }
    };

    fetchListingDetail();
  }, [id]);

  // Handle image navigation
  const handlePrevImage = () => {
    if (listing && listing.image_urls) {
      const imageUrls = listing.image_urls.split(',');
      setCurrentImageIndex((prevIndex) => 
        prevIndex === 0 ? imageUrls.length - 1 : prevIndex - 1
      );
    }
  };

  const handleNextImage = () => {
    if (listing && listing.image_urls) {
      const imageUrls = listing.image_urls.split(',');
      setCurrentImageIndex((prevIndex) => 
        prevIndex === imageUrls.length - 1 ? 0 : prevIndex + 1
      );
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (!listing) {
    return <div className="not-found">Listing not found</div>;
  }
  // Process image URLs
  const imageUrls = listing.image_urls && listing.image_urls.trim() ? listing.image_urls.split(',').filter(url => url.trim()) : [];

  return (
    <div className="listing-detail-container">
      <Link to="/" className="back-button">← Back to Listings</Link>
      
      <h1 className="listing-title">{listing.title}</h1>
      
      <div className="listing-content">
        <div className="listing-images-section">
          {imageUrls.length > 0 ? (
            <div className="image-gallery">
              <div className="main-image-container">                <img 
                  src={imageUrls[currentImageIndex]} 
                  alt={`${listing.make} ${listing.model}`}
                  className="main-image"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = `${process.env.PUBLIC_URL}/placeholder-car.svg`;
                  }}
                />
                
                {imageUrls.length > 1 && (
                  <>
                    <button className="nav-button prev-button" onClick={handlePrevImage}>❮</button>
                    <button className="nav-button next-button" onClick={handleNextImage}>❯</button>
                  </>
                )}
                
                {imageUrls.length > 1 && (
                  <div className="image-counter">
                    {currentImageIndex + 1} / {imageUrls.length}
                  </div>
                )}
              </div>
              
              {imageUrls.length > 1 && (
                <div className="thumbnail-container">
                  {imageUrls.map((url, index) => (
                    <img 
                      key={index}
                      src={url}
                      alt={`Thumbnail ${index + 1}`}
                      className={`thumbnail ${index === currentImageIndex ? 'active' : ''}`}
                      onClick={() => setCurrentImageIndex(index)}                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = `${process.env.PUBLIC_URL}/placeholder-car.svg`;
                      }}
                    />
                  ))}
                </div>
              )}
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
              <div className="detail-label">Make</div>
              <div className="detail-value">{listing.make}</div>
            </div>
            <div className="detail-row">
              <div className="detail-label">Model</div>
              <div className="detail-value">{listing.model}</div>
            </div>
            <div className="detail-row">
              <div className="detail-label">Year</div>
              <div className="detail-value">{listing.year_oM}</div>
            </div>
            <div className="detail-row">
              <div className="detail-label">Kilometers</div>
              <div className="detail-value">{listing.kilometers ? `${listing.kilometers} km` : 'N/A'}</div>
            </div>
            <div className="detail-row">
              <div className="detail-label">Location</div>
              <div className="detail-value">{listing.loc || 'N/A'}</div>
            </div>
            <div className="detail-row">
              <div className="detail-label">Website</div>
              <div className="detail-value">{listing.website}</div>
            </div>
            <div className="detail-row">
              <div className="detail-label">Created At</div>
              <div className="detail-value">{new Date(listing.created_at).toLocaleString()}</div>
            </div>
          </div>
          
          <div className="listing-actions">
            <a 
              href={listing.web_url} 
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
