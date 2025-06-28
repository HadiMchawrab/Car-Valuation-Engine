import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/ListingsPage.css';
import FilterPanel from './FilterPanel';
import { getTransmissionType, getBodyType, getColor } from '../utils/mappings';
import API_BASE_URL from '../config/api';

const ListingsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const listingsPerPage = 40;
  
  // Sort state
  const [sortBy, setSortBy] = useState('newest_listed'); // Default sort
  
  // Sort options
  const sortOptions = [
    { value: 'newest_listed', label: 'Newly Listed' },
    { value: 'oldest_listed', label: 'Oldest Listings' },
    { value: 'lowest_price', label: 'Lowest Price' },
    { value: 'highest_price', label: 'Highest Price' },
    { value: 'newest_model', label: 'Newest Model Year' },
    { value: 'oldest_model', label: 'Oldest Model Year' },
    { value: 'verified_seller', label: 'Verified Account' },
    { value: 'price_asc', label: 'Price A to Z' },
    { value: 'price_desc', label: 'Price Z to A' }
  ];
  
  // Filter states
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
    website: '',
    minPostDate: '',
    maxPostDate: '',
    seller: '', // Add seller filter
    sellerDisplayType: '' // Track if it's seller or agency
  });
  // Helper function to convert sort option to backend parameter
  const getSortParam = (sortBy) => {
    switch (sortBy) {
      case 'newest_listed':
        return 'post_date_desc';
      case 'oldest_listed':
        return 'post_date_asc';
      case 'lowest_price':
      case 'price_asc':
        return 'price_asc';
      case 'highest_price':
      case 'price_desc':
        return 'price_desc';
      case 'newest_model':
        return 'year_desc';
      case 'oldest_model':
        return 'year_asc';
      case 'verified_seller':
        return 'verified_seller';
      default:
        return 'post_date_desc';
    }
  };

  // Helper function to build search parameters from filters
  const buildSearchParams = () => {
    const params = {
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
      website: filters.website || null,
      min_post_date: filters.minPostDate || null,
      max_post_date: filters.maxPostDate || null,
      seller: filters.seller || null, // Add seller filter
      sort_by: getSortParam(sortBy) // Use backend sort parameter
    };
    
    console.log('Search params being sent:', params);
    return params;
  };

  // Frontend sorting fallback function
  const sortListingsFrontend = (listings, sortBy) => {
    const sorted = [...listings];
    
    switch (sortBy) {
      case 'newest_listed':
        return sorted.sort((a, b) => new Date(b.post_date) - new Date(a.post_date));
      case 'oldest_listed':
        return sorted.sort((a, b) => new Date(a.post_date) - new Date(b.post_date));
      case 'lowest_price':
      case 'price_asc':
        return sorted.sort((a, b) => (a.price || 0) - (b.price || 0));
      case 'highest_price':
      case 'price_desc':
        return sorted.sort((a, b) => (b.price || 0) - (a.price || 0));
      case 'newest_model':
        return sorted.sort((a, b) => (b.year || 0) - (a.year || 0));
      case 'oldest_model':
        return sorted.sort((a, b) => (a.year || 0) - (b.year || 0));
      case 'verified_seller':
        return sorted.sort((a, b) => {
          if (a.seller_verified && !b.seller_verified) return -1;
          if (!a.seller_verified && b.seller_verified) return 1;
          return new Date(b.post_date) - new Date(a.post_date); // Secondary sort by date
        });
      default:
        return sorted;
    }
  };

  useEffect(() => {
    fetchListings();
    fetchTotalCount();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, filters, sortBy]);

  // Handle URL parameters on component mount
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const seller = searchParams.get('seller');
    const sellerType = searchParams.get('sellerType');
    
    console.log('URL Parameters:', { seller, sellerType });
    
    if (seller) {
      setFilters(prev => ({
        ...prev,
        seller: seller,
        sellerDisplayType: sellerType || 'seller'
      }));
    }
  }, [location.search]);

  const fetchListings = async () => {
    setLoading(true);
    try {
      const searchParams = buildSearchParams();
      
      // Calculate offset based on current page
      const offset = (currentPage - 1) * listingsPerPage;
      
      console.log('Fetching listings with sort:', searchParams.sort_by);
      
      // Make the API call with sorting in the POST body
      const response = await axios.post(
        `${API_BASE_URL}/search?limit=${listingsPerPage}&offset=${offset}`, 
        searchParams
      );
      
      // Log the response for debugging
      console.log('API Response:', response.data);
      console.log('First few listings post_dates:', response.data.slice(0, 3).map(l => ({ 
        title: l.title, 
        post_date: l.post_date,
        price: l.price,
        year: l.year 
      })));
      
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
      
      const countResponse = await axios.post(`${API_BASE_URL}/search/count`, searchParams);
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
    
    // Update URL parameters when seller filter changes
    if (!newFilters.seller && location.search.includes('seller=')) {
      // Clear URL parameters when seller filter is cleared
      navigate('/', { replace: true });
    }
  };

  const handleSortChange = (newSortBy) => {
    setSortBy(newSortBy);
    setCurrentPage(1); // Reset to first page when sort changes
  };

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    window.scrollTo(0, 0); // Scroll to top when page changes
  };

  return (
    <div className="listings-page">
      <h1>Car Listings</h1>
      
      {/* Seller Filter Banner */}
      {filters.seller && (
        <div className="seller-filter-banner">
          <div className="seller-info">
            <h2>
              {filters.sellerDisplayType === 'agency' ? '🏢' : '👤'} 
              {filters.sellerDisplayType === 'agency' ? 'Agency' : 'Seller'}: {filters.seller}
            </h2>
            <p>Showing all listings from this {filters.sellerDisplayType}</p>
          </div>
          <button 
            className="clear-seller-filter"
            onClick={() => {
              const newFilters = { ...filters, seller: '', sellerDisplayType: '' };
              setFilters(newFilters);
              navigate('/', { replace: true });
            }}
          >
            ✕ Clear Filter
          </button>
        </div>
      )}
      
      <div className="listings-container">
        <div className="sidebar">
          <FilterPanel 
            filters={filters} 
            onFilterChange={handleFilterChange}
            totalCount={totalCount}
          />
        </div>
        
        <div className="main-content">
          {/* Sort Dropdown */}
          <div className="sort-section">
            <label htmlFor="sort-select" className="sort-label">Sort by:</label>
            <select 
              id="sort-select"
              value={sortBy} 
              onChange={(e) => handleSortChange(e.target.value)}
              className="sort-dropdown"
            >
              {sortOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          
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
                        <h3 className="listing-title">
                          {listing.title}
                          {listing.seller_verified && (
                            <span className="verified-badge">✓ Verified</span>
                          )}
                        </h3>
                        <div className="listing-price">
                          {listing.price ? `${listing.price.toLocaleString()} ${listing.currency}` : 'Price N/A'}
                        </div>
                      </div>
                      
                      <div className="listing-details">
                        <div className="detail-item">
                          <span className="detail-label">Make</span>
                          <span className="detail-value">{listing.brand || 'N/A'}</span>
                        </div>
                        <div className="detail-item">
                          <span className="detail-label">Model</span>
                          <span className="detail-value">{listing.model || 'N/A'}</span>
                        </div>
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
                        <div className="detail-item">
                          <span className="detail-label">Color</span>
                          <span className="detail-value">{getColor(listing.color)}</span>
                        </div>
                      </div>
                      
                      <div className="seller-info">
                        <div className="seller-name">
                          <span className="seller-label">Seller:</span>
                          <span className="seller-value">
                            {listing.seller || listing.agency_name || 'N/A'}
                          </span>
                        </div>
                        <div className="post-date">
                          <span className="post-label">Posted:</span>
                          <span className="post-value">
                            {listing.post_date ? new Date(listing.post_date).toLocaleDateString() : 'N/A'}
                          </span>
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