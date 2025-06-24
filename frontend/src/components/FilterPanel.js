import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/FilterPanel.css';

const FilterPanel = ({ filters, onFilterChange }) => {  const [makes, setMakes] = useState([]);
  const [models, setModels] = useState([]);
  const [years, setYears] = useState([]);
  const [locations, setLocations] = useState([]);
  const [localFilters, setLocalFilters] = useState({
    ...filters
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
      const [makesRes, yearsRes, locationsRes] = await Promise.all([
        axios.get('http://localhost:8001/makes'),
        axios.get('http://localhost:8001/years'),
        axios.get('http://localhost:8001/locations')
      ]);
      
      setMakes(makesRes.data);
      setYears(yearsRes.data);
      setLocations(locationsRes.data);
    } catch (error) {
      console.error('Error fetching filter options:', error);
    }
  };

  const fetchModelsByMake = async (make) => {
    try {
      const response = await axios.get(`http://localhost:8001/models/${make}`);
      setModels(response.data);
    } catch (error) {
      console.error('Error fetching models:', error);
    }
  };
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setLocalFilters(prev => ({ ...prev, [name]: value }));
  };
  const applyFilters = () => {
    // Map frontend filter names to backend expected names
    const mappedFilters = {
      brand: localFilters.make,
      model: localFilters.model,
      minYear: localFilters.minYear,
      maxYear: localFilters.maxYear,
      minPrice: localFilters.minPrice,
      maxPrice: localFilters.maxPrice,
      locationCity: localFilters.location, // Note: This is a simplification, locationCity and locationRegion might need separate handling
      locationRegion: localFilters.location
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
      location: ''
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
      locationRegion: ''
    };
    
    onFilterChange(mappedEmptyFilters);
  };

  return (
    <div className="filter-panel">
      <h3>Filter Listings</h3>
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
        
        <div className="filter-buttons">
          <button onClick={applyFilters} className="apply-filters-btn">Apply Filters</button>
          <button onClick={clearFilters} className="clear-filters-btn">Clear All</button>
        </div>
      </div>
    </div>
  );
};

export default FilterPanel;
