import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/FilterPanel.css';
import { getTransmissionType, getBodyType, getColor } from '../utils/mappings';
import API_BASE_URL from '../config/api';

const FilterPanel = ({ filters, onFilterChange, totalCount }) => {

  const [makes, setMakes] = useState([]);
  const [models, setModels] = useState([]);
  const [years, setYears] = useState([]);
  const [locations, setLocations] = useState([]);
  const [fuelTypes, setFuelTypes] = useState([]);
  const [bodyTypes, setBodyTypes] = useState([]);
  const [transmissionTypes, setTransmissionTypes] = useState([]);
  const [sellerTypes, setSellerTypes] = useState([]);
  const [colors, setColors] = useState([]);
  const [websites, setWebsites] = useState([]);
  const [localFilters, setLocalFilters] = useState({
    ...filters,
    minPostDate: '',
    maxPostDate: '',
    color: '',
    website: ''
  });

  useEffect(() => {
    fetchFilterOptions();
  }, []);

  useEffect(() => {
    // Fetch models when make changes
    if (localFilters.make) {
      fetchModelsByMake(localFilters.make);
    }
  }, [localFilters.make]);
  const fetchFilterOptions = async () => {
    try {
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
        axios.get(`${API_BASE_URL}/makes`),
        axios.get(`${API_BASE_URL}/years`),
        axios.get(`${API_BASE_URL}/locations`),
        axios.get(`${API_BASE_URL}/fuel-types`),
        axios.get(`${API_BASE_URL}/body-types`),
        axios.get(`${API_BASE_URL}/transmission-types`),
        axios.get(`${API_BASE_URL}/seller-types`),
        axios.get(`${API_BASE_URL}/colors`),
        axios.get(`${API_BASE_URL}/websites`)
      ]);
      
      setMakes(makesRes.data);
      setYears(yearsRes.data);
      setLocations(locationsRes.data);
      setFuelTypes(fuelTypesRes.data);
      setBodyTypes(bodyTypesRes.data);
      setTransmissionTypes(transmissionTypesRes.data);
      setSellerTypes(sellerTypesRes.data);
      setColors(colorsRes.data);
      setWebsites(websitesRes.data);
    } catch (error) {
      console.error('Error fetching filter options:', error);
    }
  };

  const fetchModelsByMake = async (make) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/models/${make}`);
      setModels(response.data);
    } catch (error) {
      console.error('Error fetching models:', error);
    }
  };  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setLocalFilters(prev => ({ ...prev, [name]: value }));
  };
  
  const handleConditionChange = (condition) => {
    // condition can be 'any', 'new', or 'used'
    const isNew = condition === 'new' ? true : 
                  condition === 'used' ? false : null;
    setLocalFilters(prev => ({ ...prev, condition: condition, isNew }));
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
  };  const applyFilters = () => {
    // Map frontend filter names to backend expected names
    const mappedFilters = {
      brand: localFilters.make,
      model: localFilters.model,
      minYear: localFilters.minYear,
      maxYear: localFilters.maxYear,
      minPrice: localFilters.minPrice,
      maxPrice: localFilters.maxPrice,
      locationCity: localFilters.location, // Note: This is a simplification, locationCity and locationRegion might need separate handling
      locationRegion: localFilters.location,
      isNew: localFilters.isNew, // null = any, true = new, false = used
      maxMileage: localFilters.maxMileage,
      bodyType: localFilters.bodyType,
      fuelType: localFilters.fuelType,
      transmissionType: localFilters.transmissionType,
      sellerType: localFilters.sellerType,
      color: localFilters.color,
      website: localFilters.website,
      minPostDate: localFilters.minPostDate,
      maxPostDate: localFilters.maxPostDate
    };
    
    console.log("Applying filters:", mappedFilters);
    onFilterChange(mappedFilters);
  };
  const clearFilters = () => {
    const emptyFilters = {
      make: '',
      model: '',
      minYear: '',
      maxYear: '',
      minPrice: '',
      maxPrice: '',
      location: '',
      isNew: null,
      maxMileage: '',
      bodyType: '',
      fuelType: '',
      transmissionType: '',
      sellerType: '',
      color: '',
      website: '',
      minPostDate: '',
      maxPostDate: ''
    };
    setLocalFilters(emptyFilters);
    
    // Map to backend expected filter names
    const mappedEmptyFilters = {
      brand: '',
      model: '',
      minYear: '',
      maxYear: '',
      minPrice: '',
      maxPrice: '',
      locationCity: '',
      locationRegion: '',
      isNew: null,
      maxMileage: '',
      bodyType: '',
      fuelType: '',
      transmissionType: '',
      sellerType: '',
      seller: '', // Clear seller filter
      sellerDisplayType: '', // Clear seller display type
      color: '',
      website: '',
      minPostDate: '',
      maxPostDate: ''
    };
    
    onFilterChange(mappedEmptyFilters);
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
          <button onClick={applyFilters} className="apply-filters-btn">Apply Filters</button>
          <button onClick={clearFilters} className="clear-filters-btn">Clear All</button>
        </div>
      <div className="filter-controls">        <div className="filter-group">
          <label>Make</label>
          <select 
            name="make"
            value={localFilters.make}
            onChange={handleInputChange}
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
            disabled={!localFilters.make}
          >
            <option value="">All Models</option>
            {models.map(model => (
              <option key={model} value={model}>{model}</option>
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
            >
              Any
            </button>
            <button 
              className={`condition-btn ${localFilters.isNew === true ? 'active' : ''}`} 
              onClick={() => handleConditionChange('new')}
            >
              New
            </button>
            <button 
              className={`condition-btn ${localFilters.isNew === false ? 'active' : ''}`} 
              onClick={() => handleConditionChange('used')}
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
            />
          </div>
        </div>

        <div className="filter-group">
          <label>Body Type</label>
          <select 
            name="bodyType"
            value={localFilters.bodyType}
            onChange={handleInputChange}
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
