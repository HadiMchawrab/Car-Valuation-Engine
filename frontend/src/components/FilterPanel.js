import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import '../styles/FilterPanel.css';
import { getTransmissionType, getBodyType, getColor } from '../utils/mappings';
import API_BASE_URL from '../config/api';

const FilterPanel = ({ filters, onFilterChange, totalCount }) => {

  const [makes, setMakes] = useState([]);
  const [models, setModels] = useState([]);
  const [trims, setTrims] = useState([]); 
  const [years, setYears] = useState([]);
  const [locations, setLocations] = useState([]);
  const [fuelTypes, setFuelTypes] = useState([]);
  const [bodyTypes, setBodyTypes] = useState([]);
  const [transmissionTypes, setTransmissionTypes] = useState([]);
  const [sellerTypes, setSellerTypes] = useState([]);
  const [colors, setColors] = useState([]);
  const [websites, setWebsites] = useState([]);
  const [isLoadingOptions, setIsLoadingOptions] = useState(false);
  const [localFilters, setLocalFilters] = useState({
    ...filters,
    // Fix the brand/make mismatch in initial state
    make: filters.brand || filters.make || '',
    minPostDate: '',
    maxPostDate: '',
    color: '',
    website: '',
    contributorName: '', // Track contributor (agency/seller) name for profile link
    contributorType: '' // Track if contributor is agency or individual_seller
  });
  const [initialYears, setInitialYears] = useState([]);

  useEffect(() => {
    // Fetch initial filter options when component mounts or seller changes
    fetchInitialFilterOptions();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.seller]); // Re-fetch when seller changes

  useEffect(() => {
    // Fetch dynamic filter options when any filter changes (except on initial load)
    if (Object.keys(localFilters).some(key => localFilters[key] !== '' && localFilters[key] !== null)) {
      fetchDynamicFilterOptions();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [localFilters]); // Re-fetch when any local filter changes

  // Update local filters when props change (important for URL-based filters)
  useEffect(() => {
    console.log('FilterPanel: Received new filters from parent:', filters);
    setLocalFilters(prev => {
      const updated = {
        ...prev,
        ...filters,
        // Fix the brand/make mismatch - use brand from filters as make in local state
        make: filters.brand || filters.make || '',
        contributorName: filters.sellerDisplayName || filters.seller || '', // Use display name for UI
        contributorType: filters.sellerDisplayType || ''
      };
      console.log('FilterPanel: Updated local filters:', updated);
      return updated;
    });
  }, [filters]);

  useEffect(() => {
  }, [localFilters.make, filters.seller]);
  const fetchInitialFilterOptions = async () => {
    try {
      // Build base URL with seller filter if present
      const baseUrl = API_BASE_URL;
      const sellerParam = filters.seller ? `?seller=${encodeURIComponent(filters.seller)}` : '';
      
      const [
        makesRes, 
        yearsRes, 
        locationsRes, 
        fuelTypesRes, 
        bodyTypesRes, 
        transmissionTypesRes, 
        sellerTypesRes,
        colorsRes,
        websitesRes
      ] = await Promise.all([
        axios.get(`${baseUrl}/makes${sellerParam}`),
        axios.get(`${baseUrl}/years${sellerParam}`),
        axios.get(`${baseUrl}/locations${sellerParam}`),
        axios.get(`${baseUrl}/fuel-types${sellerParam}`),
        axios.get(`${baseUrl}/body-types${sellerParam}`),
        axios.get(`${baseUrl}/transmission-types${sellerParam}`),
        axios.get(`${baseUrl}/seller-types${sellerParam}`),
        axios.get(`${baseUrl}/colors${sellerParam}`),
        axios.get(`${baseUrl}/websites${sellerParam}`)
      ]);
      
      setMakes(makesRes.data);
      setYears(yearsRes.data);
      setInitialYears(yearsRes.data);
      setLocations(locationsRes.data);
      setFuelTypes(fuelTypesRes.data);
      setBodyTypes(bodyTypesRes.data);
      setTransmissionTypes(transmissionTypesRes.data);
      setSellerTypes(sellerTypesRes.data);
      setColors(colorsRes.data);
      setWebsites(websitesRes.data);
      
      if (localFilters.make && !makesRes.data.includes(localFilters.make)) {
        setLocalFilters(prev => ({ ...prev, make: '', model: '', trim: '' }));
      }
    } catch (error) {
      console.error('Error fetching initial filter options:', error);
    }
  };

  const fetchDynamicFilterOptions = async () => {
    setIsLoadingOptions(true);
    try {
      // Convert frontend filter names to backend expected names
      const backendFilters = {
        brand: localFilters.make,
        model: localFilters.model,
        trim: localFilters.trim, // Include trim filter
        min_year: localFilters.minYear,
        max_year: localFilters.maxYear,
        min_price: localFilters.minPrice,
        max_price: localFilters.maxPrice,
        location_city: localFilters.location,
        location_region: localFilters.location,
        is_new: localFilters.isNew,
        max_mileage: localFilters.maxMileage,
        body_type: localFilters.bodyType,
        fuel_type: localFilters.fuelType,
        transmission_type: localFilters.transmissionType,
        seller_type: localFilters.sellerType,
        color: localFilters.color,
        website: localFilters.website,
        min_post_date: localFilters.minPostDate,
        max_post_date: localFilters.maxPostDate,
        seller: filters.seller // Include seller filter
      };

      // Remove empty/null values
      const cleanFilters = Object.fromEntries(
        Object.entries(backendFilters).filter(([_, value]) => 
          value !== '' && value !== null && value !== undefined
        )
      );

      const response = await axios.post(`${API_BASE_URL}/dynamic-filter-options`, cleanFilters);
      const data = response.data;
      
      setMakes(data.makes || []);
      setModels(data.models || []);
      setTrims(data.trims || []); // Set trims from response
      setYears((data.years && data.years.length > 0) ? data.years : initialYears);
      setLocations(data.locations || []);
      setFuelTypes(data.fuelTypes || []);
      setBodyTypes(data.bodyTypes || []);
      setTransmissionTypes(data.transmissionTypes || []);
      setSellerTypes(data.sellerTypes || []);
      setColors(data.colors || []);
      setWebsites(data.websites || []);
      
    } catch (error) {
      console.error('Error fetching dynamic filter options:', error);
    } finally {
      setIsLoadingOptions(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    let updatedFilters = { ...localFilters, [name]: value };
    
    // If make is being changed to "All Makes" (empty value), reset model and trim to "All Models/Trims"
    if (name === 'make' && value === '') {
      updatedFilters = { ...updatedFilters, model: '', trim: '' };
    }
    
    setLocalFilters(updatedFilters);
    
    // Apply filters immediately
    applyFiltersImmediately(updatedFilters);
  };
  
  const handleConditionChange = (condition) => {
    // condition can be 'any', 'new', or 'used'
    const isNew = condition === 'new' ? true : 
                  condition === 'used' ? false : null;
    const updatedFilters = { ...localFilters, condition: condition, isNew };
    setLocalFilters(updatedFilters);
    
    // Apply filters immediately
    applyFiltersImmediately(updatedFilters);
  };

  const handleDateChange = (e) => {
    const { name, value } = e.target;
    
    // Update the filters first
    const updatedFilters = { ...localFilters, [name]: value };
    
    // Validate date range
    if (updatedFilters.minPostDate && updatedFilters.maxPostDate) {
      const minDate = new Date(updatedFilters.minPostDate);
      const maxDate = new Date(updatedFilters.maxPostDate);
      
      if (minDate > maxDate) {
        alert('The "Ad Posted After" date cannot be later than the "Ad Posted Before" date. Please select valid dates.');
        return; // Don't update the state if validation fails
      }
    }
    
    setLocalFilters(updatedFilters);
    
    // Apply filters immediately
    applyFiltersImmediately(updatedFilters);
  };  const applyFiltersImmediately = (updatedFilters) => {
    // Map frontend filter names to backend expected names
    const mappedFilters = {
      brand: updatedFilters.make,
      model: updatedFilters.model,
      trim: updatedFilters.trim, // Include trim filter
      minYear: updatedFilters.minYear,
      maxYear: updatedFilters.maxYear,
      minPrice: updatedFilters.minPrice,
      maxPrice: updatedFilters.maxPrice,
      locationCity: updatedFilters.location,
      locationRegion: updatedFilters.location,
      isNew: updatedFilters.isNew,
      maxMileage: updatedFilters.maxMileage,
      bodyType: updatedFilters.bodyType,
      fuelType: updatedFilters.fuelType,
      transmissionType: updatedFilters.transmissionType,
      sellerType: updatedFilters.sellerType,
      color: updatedFilters.color,
      website: updatedFilters.website,
      minPostDate: updatedFilters.minPostDate,
      maxPostDate: updatedFilters.maxPostDate,
      // Preserve seller/agency filters
      seller: filters.seller,
      sellerDisplayType: filters.sellerDisplayType,
      sellerDisplayName: filters.sellerDisplayName
    };
    
    console.log("Applying filters immediately:", mappedFilters);
    onFilterChange(mappedFilters);
  };

  const clearFilters = async () => {
    // Reset to completely empty state as if page just loaded
    const emptyFilters = {
      make: '',
      model: '',
      trim: '',
      minYear: '',
      maxYear: '',
      minPrice: '',
      maxPrice: '',
      location: '',
      isNew: null,
      condition: '',
      maxMileage: '',
      minMileage: '',
      bodyType: '',
      fuelType: '',
      transmissionType: '',
      sellerType: '',
      color: '',
      website: '',
      minPostDate: '',
      maxPostDate: '',
      contributorName: '', // Clear contributor info
      contributorType: ''
    };
    
    // Update local filters first
    setLocalFilters(emptyFilters);
    
    // Map to backend expected filter names - reset everything to initial state
    const mappedEmptyFilters = {
      brand: '',
      model: '',
      trim: '',
      minYear: '',
      maxYear: '',
      minPrice: '',
      maxPrice: '',
      locationCity: '',
      locationRegion: '',
      isNew: null,
      condition: '',
      maxMileage: '',
      minMileage: '',
      bodyType: '',
      fuelType: '',
      transmissionType: '',
      sellerType: '',
      seller: '', // Clear seller filter
      sellerDisplayType: '', // Clear seller display type
      sellerDisplayName: '', // Clear seller display name
      color: '',
      website: '',
      minPostDate: '',
      maxPostDate: ''
    };
    
    // Apply the cleared filters
    onFilterChange(mappedEmptyFilters);
    
    // Re-fetch initial filter options to restore full available options
    // This ensures that all dropdown options are restored as if page was refreshed
    try {
      await fetchInitialFilterOptions();
    } catch (error) {
      console.error('Error refreshing filter options after clear:', error);
    }
  };

  return (
    <div className="filter-panel">
      {totalCount !== undefined && (
          <div className="results-count">
            <span className="count-text">
              {totalCount.toLocaleString()} {totalCount === 1 ? 'result' : 'results'} found
            </span>
          </div>
        )}
      
      <h3>Filter Listings</h3>
      <div className="filter-buttons">
          <button onClick={clearFilters} className="clear-filters-btn" disabled={isLoadingOptions}>Clear All</button>
        </div>
      
      {isLoadingOptions && (
        <div className="loading-indicator">
          <span>Updating filter options...</span>
        </div>
      )}

      {/* Contributor Filter - Show when filtering by seller/agency */}
      {localFilters.contributorName && (
        <div className="contributor-filter-section">
          <div className="contributor-info">
            <div className="contributor-details">
              <span className="contributor-icon">
                {localFilters.contributorType === 'agency' ? '🏢' : '👤'}
              </span>
              <div className="contributor-text">
                <strong>{localFilters.contributorName}</strong>
                <span className="contributor-type">
                  {localFilters.contributorType === 'agency' ? 'Agency' : 'Individual Seller'}
                </span>
              </div>
            </div>
            <div className="contributor-actions">
              <Link 
                to={`/analytics/contributor/${encodeURIComponent(localFilters.contributorName)}`}
                className="profile-btn"
                title="View Profile & Analytics"
              >
                📊 Profile
              </Link>
              <button 
                onClick={() => {
                  setLocalFilters(prev => ({ ...prev, contributorName: '', contributorType: '' }));
                  onFilterChange({
                    ...filters,
                    seller: '',
                    sellerDisplayType: '',
                    sellerDisplayName: ''
                  });
                }}
                className="remove-contributor-btn"
                title="Remove contributor filter"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}
  <div style={{ height: '20px' }} />
      <div className="filter-controls">        <div className="filter-group">
          <label>Make</label>
          <select 
            name="make"
            value={localFilters.make}
            onChange={handleInputChange}
            disabled={isLoadingOptions}
          >
            <option value="">All Makes</option>
            {makes.map(make => (
              <option key={make} value={make}>{make}</option>
            ))}
          </select>
          {/* Hidden field for brand to match backend param name */}
          <input type="hidden" name="brand" value={localFilters.make} />
        </div>
        
        <div className="filter-group">
          <label>Model</label>
          <select 
            name="model"
            value={localFilters.model}
            onChange={handleInputChange}
            disabled={!localFilters.make || isLoadingOptions}
          >
            <option value="">All Models</option>
            {models.map(model => (
              <option key={model} value={model}>{model}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Trim</label>
          <select
            name="trim"
            value={localFilters.trim}
            onChange={handleInputChange}
            disabled={!localFilters.make || isLoadingOptions}
          >
            <option value="">All Trims</option>
            {trims.map(trim => (
              <option key={trim} value={trim}>{trim}</option>
            ))}
          </select>
        </div>

        <div className="filter-row">
          <div className="filter-group">
            <label>Min Year</label>
            <select 
              name="minYear"
              value={localFilters.minYear}
              onChange={handleInputChange}
              disabled={isLoadingOptions}
            >
              <option value="">Any</option>
              {years.map(year => (
                <option key={`min-${year}`} value={year}>{year}</option>
              ))}
            </select>
          </div>
          
          <div className="filter-group">
            <label>Max Year</label>
            <select 
              name="maxYear"
              value={localFilters.maxYear}
              onChange={handleInputChange}
              disabled={isLoadingOptions}
            >
              <option value="">Any</option>
              {years.map(year => (
                <option key={`max-${year}`} value={year}>{year}</option>
              ))}
            </select>
          </div>
        </div>          {/* Price Filter Section */}
        <div className="filter-row">
          <div className="filter-group">
            <label>Min Price</label>
            <div className="price-input-container">
              <input 
                type="number"
                name="minPrice"
                value={localFilters.minPrice}
                onChange={handleInputChange}
                placeholder="Min Price"
                disabled={isLoadingOptions}
              />
              <span className="price-currency">SAR</span>
            </div>
          </div>
          
          <div className="filter-group">
            <label>Max Price</label>
            <div className="price-input-container">
              <input 
                type="number"
                name="maxPrice"
                value={localFilters.maxPrice}
                onChange={handleInputChange}
                placeholder="Max Price"
                disabled={isLoadingOptions}
              />
              <span className="price-currency">SAR</span>
            </div>
          </div>
        </div>
        
        <div className="filter-group">
          <label>Location</label>
          <select 
            name="location"
            value={localFilters.location}
            onChange={handleInputChange}
            disabled={isLoadingOptions}
          >
            <option value="">All Locations</option>
            {locations.map(location => (
              <option key={location} value={location}>{location}</option>
            ))}
          </select>
        </div>

        {/* Car Condition Filter */}
        <div className="filter-group">
          <label>Car Condition</label>
          <div className="condition-buttons">
            <button 
              className={`condition-btn ${localFilters.isNew === null ? 'active' : ''}`} 
              onClick={() => handleConditionChange('any')}
              disabled={isLoadingOptions}
            >
              Any
            </button>
            <button 
              className={`condition-btn ${localFilters.isNew === true ? 'active' : ''}`} 
              onClick={() => handleConditionChange('new')}
              disabled={isLoadingOptions}
            >
              New
            </button>
            <button 
              className={`condition-btn ${localFilters.isNew === false ? 'active' : ''}`} 
              onClick={() => handleConditionChange('used')}
              disabled={isLoadingOptions}
            >
              Used
            </button>
          </div>
        </div>

        {/* Max Mileage Filter */}
        <div className="filter-group">
          <label>Max Mileage</label>
          <input 
            type="number"
            name="maxMileage"
            value={localFilters.maxMileage}
            onChange={handleInputChange}
            placeholder="Max Mileage"
            disabled={isLoadingOptions}
          />
        </div>

        {/* Date Filter Section */}
        <div className="filter-row">
          <div className="filter-group">
            <label>Ad Posted After</label>
            <input 
              type="date"
              name="minPostDate"
              value={localFilters.minPostDate}
              onChange={handleDateChange}
              placeholder="Posted After"
              disabled={isLoadingOptions}
            />
          </div>
          
          <div className="filter-group">
            <label>Ad Posted Before</label>
            <input 
              type="date"
              name="maxPostDate"
              value={localFilters.maxPostDate}
              onChange={handleDateChange}
              placeholder="Posted Before"
              disabled={isLoadingOptions}
            />
          </div>
        </div>

        <div className="filter-group">
          <label>Body Type</label>
          <select 
            name="bodyType"
            value={localFilters.bodyType}
            onChange={handleInputChange}
            disabled={isLoadingOptions}
          >
            <option value="">All Body Types</option>
            {bodyTypes.map(type => (
              <option key={type} value={type}>{getBodyType(type)}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Fuel Type</label>
          <select 
            name="fuelType"
            value={localFilters.fuelType}
            onChange={handleInputChange}
            disabled={isLoadingOptions}
          >
            <option value="">All Fuel Types</option>
            {fuelTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Transmission</label>
          <select 
            name="transmissionType"
            value={localFilters.transmissionType}
            onChange={handleInputChange}
            disabled={isLoadingOptions}
          >
            <option value="">All Transmissions</option>
            {transmissionTypes.map(type => (
              <option key={type} value={type}>{getTransmissionType(type)}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Color</label>
          <select 
            name="color"
            value={localFilters.color}
            onChange={handleInputChange}
            disabled={isLoadingOptions}
          >
            <option value="">All Colors</option>
            {colors.map(color => (
              <option key={color} value={color}>{getColor(color)}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Website</label>
          <select 
            name="website"
            value={localFilters.website}
            onChange={handleInputChange}
            disabled={isLoadingOptions}
          >
            <option value="">All Websites</option>
            {websites.map(website => (
              <option key={website} value={website}>{website}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Seller Type</label>
          <select 
            name="sellerType"
            value={localFilters.sellerType}
            onChange={handleInputChange}
            disabled={isLoadingOptions}
          >
            <option value="">All Seller Types</option>
            {sellerTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>
        
        
        
        
      </div>
    </div>
  );
};

export default FilterPanel;
