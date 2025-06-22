import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import '../styles/ListingsPage.css';
import FilterPanel from './FilterPanel';

const ListingsPage = () => {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const listingsPerPage = 40;
  
  // Filter states
  const [filters, setFilters] = useState({
    make: '',
    model: '',
    minYear: '',
    maxYear: '',
    minPrice: '',
    maxPrice: '',
    location: ''
  });
  useEffect(() => {
    fetchListings();
    fetchTotalCount();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, filters]);

  const fetchListings = async () => {
    setLoading(true);
    try {
      const searchParams = {
        make: filters.make || null,
        model: filters.model || null,
        min_year: filters.minYear ? parseInt(filters.minYear) : null,
        max_year: filters.maxYear ? parseInt(filters.maxYear) : null,
        min_price: filters.minPrice ? parseFloat(filters.minPrice) : null,
        max_price: filters.maxPrice ? parseFloat(filters.maxPrice) : null,
        location: filters.location || null
      };
      
      // Calculate offset based on current page
      const offset = (currentPage - 1) * listingsPerPage;
      
      const response = await axios.post(
        `http://localhost:8001/search?limit=${listingsPerPage}&offset=${offset}`, 
        searchParams
      );
      
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
      const searchParams = {
        make: filters.make || null,
        model: filters.model || null,
        min_year: filters.minYear ? parseInt(filters.minYear) : null,
        max_year: filters.maxYear ? parseInt(filters.maxYear) : null,
        min_price: filters.minPrice ? parseFloat(filters.minPrice) : null,
        max_price: filters.maxPrice ? parseFloat(filters.maxPrice) : null,
        location: filters.location || null
      };
      
      const countResponse = await axios.post('http://localhost:8001/search/count', searchParams);
      const totalListings = countResponse.data.total;
      setTotalPages(Math.ceil(totalListings / listingsPerPage));
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
      
      <FilterPanel 
        filters={filters} 
        onFilterChange={handleFilterChange}
      />
      
      {loading ? (
        <div className="loading">Loading...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : (
        <>
          <div className="listings-grid">
            {listings.length > 0 ? (
              listings.map(listing => (
                <div className="listing-card" key={listing.id}>
                  <Link to={`/listing/${listing.id}`} className="listing-link">
                    <div className="listing-image">                      {listing.image_urls && listing.image_urls.trim() ? (
                        <img 
                          src={listing.image_urls.split(',')[0]} 
                          alt={`${listing.make} ${listing.model}`}                          onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = `${process.env.PUBLIC_URL}/placeholder-car.svg`;
                          }}
                        />
                      ) : (
                        <div className="no-image">No Image Available</div>
                      )}
                    </div>
                    <div className="listing-info">
                      <h3>{listing.title}</h3>
                      <p className="listing-price">{listing.price} {listing.currency}</p>
                      <div className="listing-details">
                        <span>{listing.year_oM}</span>
                        <span>•</span>
                        <span>{listing.kilometers ? `${listing.kilometers} km` : 'N/A'}</span>
                      </div>
                      <p className="listing-location">{listing.loc || 'Location N/A'}</p>
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
  );
};

export default ListingsPage;
