import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import '../styles/ListingsPage.css';
import FilterPanel from './FilterPanel';
import { getTransmissionType, getBodyType, getFuelType, getCondition, getColor, getSellerType } from '../utils/mappings';

const ListingsPage = () => {

  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const listingsPerPage = 40;      // Filter states
  const [filters, setFilters] = useState({
    brand: '',
    model: '',
    minYear: '',
    maxYear: '',
    minPrice: '',
    maxPrice: '',
    locationCity: '',
    locationRegion: '',
    minMileage: '',
    maxMileage: '',
    isNew: null, // null = all, true = new cars, false = used cars
    bodyType: '',
    fuelType: '',
    transmissionType: '',
    condition: '',
    sellerType: '',
    color: '',
    minPostDate: '',
    maxPostDate: ''
  });
  // Helper function to build search parameters from filters
  const buildSearchParams = () => {
    return {
      brand: filters.brand || null,
      model: filters.model || null,
      min_year: filters.minYear ? parseInt(filters.minYear) : null,
      max_year: filters.maxYear ? parseInt(filters.maxYear) : null,
      min_price: filters.minPrice ? parseFloat(filters.minPrice) : null,
      max_price: filters.maxPrice ? parseFloat(filters.maxPrice) : null,
      location_city: filters.locationCity || null,
      location_region: filters.locationRegion || null,
      min_mileage: filters.minMileage ? parseInt(filters.minMileage) : null,
      max_mileage: filters.maxMileage ? parseInt(filters.maxMileage) : null,
      is_new: filters.isNew, // null = any condition, true = new, false = used
      body_type: filters.bodyType || null,
      fuel_type: filters.fuelType || null,
      transmission_type: filters.transmissionType || null,
      condition: filters.condition || null,
      seller_type: filters.sellerType || null,
      color: filters.color || null,
      min_post_date: filters.minPostDate || null,
      max_post_date: filters.maxPostDate || null
    };
  };

  useEffect(() => {
    fetchListings();
    fetchTotalCount();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, filters]);

  const fetchListings = async () => {
    setLoading(true);
    try {
      const searchParams = buildSearchParams();
      
      // Calculate offset based on current page
      const offset = (currentPage - 1) * listingsPerPage;
      const response = await axios.post(
        `http://localhost:8001/search?limit=${listingsPerPage}&offset=${offset}`, 
        searchParams
      );
      
      // Log image URLs for debugging
      console.log('Listings data:', response.data);
      if (response.data && response.data.length > 0) {
        console.log('First listing image_urls:', response.data[0].image_urls);
      }
      
      setListings(response.data);
      setLoading(false);
    } catch (err) {
      setError('Error fetching listings. Please try again later.');
      setLoading(false);
      console.error('Error fetching listings:', err);
    }
  };

  const fetchTotalCount = async () => {
    try {
      const searchParams = buildSearchParams();
      
      const countResponse = await axios.post('http://localhost:8001/search/count', searchParams);
      const totalListings = countResponse.data.total;
      setTotalPages(Math.ceil(totalListings / listingsPerPage));
      setTotalCount(totalListings);
    } catch (err) {
      console.error('Error fetching total count:', err);
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  };

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    window.scrollTo(0, 0); // Scroll to top when page changes
  };

  return (
    <div className="listings-page">
      <h1>Car Listings</h1>
      
      <div className="listings-container">
        <div className="sidebar">
          <FilterPanel 
            filters={filters} 
            onFilterChange={handleFilterChange}
            totalCount={totalCount}
          />
        </div>
        
        <div className="main-content">
          {loading ? (
            <div className="loading">Loading...</div>
          ) : error ? (
            <div className="error">{error}</div>
          ) : (
            <>
              <div className="listings-grid">
                {listings.length > 0 ? (
                  listings.map(listing => (                <div className="listing-card" key={listing.ad_id}>
                  <Link to={`/listing/${listing.ad_id}`} className="listing-link">
                    <div className="listing-image">
                      {listing.image_url ? (
                        <img 
                          src={listing.image_url}
                          alt={`${listing.brand} ${listing.model}`}
                          onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = `${process.env.PUBLIC_URL}/placeholder-car.svg`;
                          }}
                        />
                      ) : (
                        <div className="no-image">No Image Available</div>
                      )}
                    </div>
                    <div className="listing-info">
                      <div className="listing-header">
                        <h3 className="listing-title">{listing.title}</h3>
                        <div className="listing-price">
                          {listing.price ? `${listing.price.toLocaleString()} ${listing.currency}` : 'Price N/A'}
                        </div>
                      </div>
                      
                      <div className="listing-details">
                        <div className="detail-item">
                          <span className="detail-label">Year</span>
                          <span className="detail-value">{listing.year || 'N/A'}</span>
                        </div>
                        <div className="detail-item">
                          <span className="detail-label">Mileage</span>
                          <span className="detail-value">
                            {listing.mileage ? `${listing.mileage.toLocaleString()} km` : 'New'}
                          </span>
                        </div>
                        <div className="detail-item">
                          <span className="detail-label">Body Type</span>
                          <span className="detail-value">{getBodyType(listing.body_type)}</span>
                        </div>
                        <div className="detail-item">
                          <span className="detail-label">Fuel</span>
                          <span className="detail-value">{listing.fuel_type || 'N/A'}</span>
                        </div>
                        <div className="detail-item">
                          <span className="detail-label">Transmission</span>
                          <span className="detail-value">{getTransmissionType(listing.transmission_type)}</span>
                        </div>
                      
                      </div>
                      
                      <div className="listing-meta">
                        <div className="listing-location">
                          📍 {(listing.location_city || listing.location_region) ? 
                            `${listing.location_city || ''} ${listing.location_region || ''}`.trim() : 
                            'Location N/A'}
                        </div>
                        <div className="listing-date">
                          {listing.post_date ? new Date(listing.post_date).toLocaleDateString() : ''}
                        </div>
                      </div>
                    </div>
                  </Link>
                </div>
              ))
            ) : (
              <div className="no-results">No listings found matching your criteria.</div>
            )}
          </div>
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button 
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
              >
                Previous
              </button>
              
              <span className="page-info">
                Page {currentPage} of {totalPages}
              </span>
              
              <button 
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
        </div>
      </div>
    </div>
  );
};

export default ListingsPage;