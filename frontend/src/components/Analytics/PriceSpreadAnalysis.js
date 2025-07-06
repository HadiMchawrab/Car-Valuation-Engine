import React, { useState, useEffect } from 'react';
import { Scatter } from 'react-chartjs-2';
import API_BASE_URL from '../../config/api';
import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from 'chart.js';
import '../../styles/PriceSpreadAnalysis.css';

// Register Chart.js components
ChartJS.register(LinearScale, PointElement, LineElement, Tooltip, Legend);

const PriceSpreadAnalysis = () => {
  const [makes, setMakes] = useState([]);
  const [models, setModels] = useState([]);
  const [trims, setTrims] = useState([]);
  const [years, setYears] = useState([]);
  const [selectedMake, setSelectedMake] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [selectedTrim, setSelectedTrim] = useState('');
  const [selectedYear, setSelectedYear] = useState('');
  const [priceSpreadData, setPriceSpreadData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [noYearsAvailable, setNoYearsAvailable] = useState(false);

  // Fetch makes on component mount
  useEffect(() => {
    fetchMakes();
  }, []);

  // Fetch models when make is selected
  useEffect(() => {
    if (selectedMake) {
      fetchModels(selectedMake);
    } else {
      setModels([]);
      setSelectedModel('');
    }
  }, [selectedMake]);

  // Fetch trims when make and model are selected
  useEffect(() => {
    if (selectedMake && selectedModel) {
      fetchTrims(selectedMake, selectedModel);
    } else {
      setTrims([]);
      setSelectedTrim('');
    }
  }, [selectedMake, selectedModel]);

  // Fetch price spread data when all selections are made
  useEffect(() => {
    if (selectedMake && selectedModel && selectedYear) {
      fetchPriceSpreadData(selectedMake, selectedModel, selectedYear, selectedTrim);
    } else {
      setPriceSpreadData(null);
    }
  }, [selectedMake, selectedModel, selectedYear, selectedTrim]);

  // Fetch years when make and model are selected
  useEffect(() => {
    if (selectedMake && selectedModel) {
      fetchYearsForMakeModel(selectedMake, selectedModel);
    } else {
      setYears([]);
      setSelectedYear('');
    }
  }, [selectedMake, selectedModel]);

  const fetchMakes = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/makes`);
      if (!response.ok) throw new Error('Failed to fetch makes');
      const data = await response.json();
      setMakes(data);
    } catch (err) {
      console.error('Error fetching makes:', err);
      setError('Failed to load makes');
    }
  };

  const fetchModels = async (make) => {
    try {
      const response = await fetch(`${API_BASE_URL}/models/${encodeURIComponent(make)}`);
      if (!response.ok) throw new Error('Failed to fetch models');
      const data = await response.json();
      setModels(data);
    } catch (err) {
      console.error('Error fetching models:', err);
      setError('Failed to load models');
    }
  };

  const fetchTrims = async (make, model) => {
    try {
      const response = await fetch(`${API_BASE_URL}/trims/${encodeURIComponent(make)}/${encodeURIComponent(model)}`);
      if (!response.ok) throw new Error('Failed to fetch trims');
      const data = await response.json();
      setTrims(data);
    } catch (err) {
      console.error('Error fetching trims:', err);
      setTrims([]);
    }
  };

  const fetchYearsForMakeModel = async (make, model) => {
    try {
      const response = await fetch(`${API_BASE_URL}/years/${encodeURIComponent(make)}/${encodeURIComponent(model)}`);
      if (!response.ok) throw new Error('Failed to fetch years');
      const data = await response.json();
      setYears(data.sort((a, b) => b - a));
      setNoYearsAvailable(data.length === 0);
    } catch (err) {
      setYears([]);
      setNoYearsAvailable(true);
    }
  };

  const fetchPriceSpreadData = async (make, model, year, trim = '') => {
    setLoading(true);
    setError(null);
    
    try {
      let url = `${API_BASE_URL}/api/analytics/price-spread?make=${encodeURIComponent(make)}&model=${encodeURIComponent(model)}&year=${year}`;
      if (trim && trim.trim() !== '') {
        url += `&trim=${encodeURIComponent(trim)}`;
      }
      
      const response = await fetch(url);
      
      if (!response.ok) {
        if (response.status === 404) {
          // Specific error for no data found
          const trimText = trim && trim.trim() !== '' ? ` ${trim}` : '';
          setError(`No price spread data found for ${make} ${model}${trimText} ${year}. Try a different trim or year.`);
          setPriceSpreadData(null); // Clear previous data
          return;
        }
        throw new Error('Failed to fetch price spread data');
      }
      
      const data = await response.json();
      setPriceSpreadData(data);
    } catch (err) {
      console.error('Error fetching price spread data:', err);
      setError('Failed to load price spread analysis');
    } finally {
      setLoading(false);
    }
  };

  const getChartData = () => {
    if (!priceSpreadData || !priceSpreadData.listings) return null;

    const listings = priceSpreadData.listings;

    return {
      datasets: [
        {
          label: 'Prices',
          data: listings.map((listing, index) => ({
            x: index + 1,
            y: listing.price,
            listing: listing
          })),
          backgroundColor: 'black',
          borderColor: 'black',
          pointBackgroundColor: 'black',
          pointBorderColor: 'black',
          showLine: true,
          fill: false,
          tension: 0,
          borderWidth: 2,
          lineTension: 0,
          segment: {
            borderColor: 'red',
          },
        },
      ],
    };
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: `Price Distribution for ${selectedMake} ${selectedModel} ${selectedYear}${selectedTrim && selectedTrim.trim() !== '' ? ` ${selectedTrim}` : ''}`,
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const listing = context.raw.listing;
            return [
              `Price: ${context.parsed.y.toLocaleString()} SAR`,
              `Mileage: ${listing.mileage || 'N/A'} km`,
              `Location: ${listing.location_city || 'N/A'}`,
              `Seller: ${listing.seller || 'N/A'}`
            ];
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Listing Index'
        }
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Price (SAR)'
        },
        ticks: {
          callback: function(value) {
            return `${value.toLocaleString()} SAR`;
          }
        }
      }
    }
  };

  return (
    <div className="price-spread-analysis">
      <div className="analysis-header">
        <h2>💰 Price Spread Analysis</h2>
        <p className="analysis-subtitle">
          View price distribution and market statistics
        </p>
      </div>

      <div className="selection-controls">
        <div className="control-group">
          <label htmlFor="make-select">Select Make:</label>
          <select
            id="make-select"
            value={selectedMake}
            onChange={(e) => {
              setSelectedMake(e.target.value);
              setSelectedModel('');
              setSelectedTrim('');
            }}
            className="analysis-select"
          >
            <option value="">Choose a make...</option>
            {makes.map(make => (
              <option key={make} value={make}>{make}</option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="model-select">Select Model:</label>
          <select
            id="model-select"
            value={selectedModel}
            onChange={(e) => {
              setSelectedModel(e.target.value);
              setSelectedTrim('');
            }}
            disabled={!selectedMake}
            className="analysis-select"
          >
            <option value="">Choose a model...</option>
            {models.map(model => (
              <option key={model} value={model}>{model}</option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="trim-select">Select Trim (Optional):</label>
          <select
            id="trim-select"
            value={selectedTrim}
            onChange={(e) => setSelectedTrim(e.target.value)}
            disabled={!selectedMake || !selectedModel}
            className="analysis-select"
          >
            <option value="">All trims</option>
            {trims.map(trim => (
              <option key={trim} value={trim}>{trim}</option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="year-select">Select Year:</label>
          <select
            id="year-select"
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
            disabled={!selectedMake || !selectedModel || noYearsAvailable}
            className="analysis-select"
          >
            {noYearsAvailable ? (
              <option value="">No years available</option>
            ) : (
              <>
                <option value="">All years</option>
                {years.map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </>
            )}
          </select>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}

      {loading && (
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Analyzing price distribution...</p>
        </div>
      )}

      {priceSpreadData && !loading && (
        <div className="price-spread-results">
          <div className="spread-stats">
            <div className="stat-card">
              <h3>Total Listings</h3>
              <p className="stat-value">{priceSpreadData.total_listings}</p>
            </div>
            
            <div className="stat-card">
              <h3>Average Price</h3>
              <p className="stat-value">
                {priceSpreadData.average_price.toLocaleString()} SAR
              </p>
            </div>
            
            <div className="stat-card">
              <h3>Price Range</h3>
              <p className="stat-value">
                {priceSpreadData.min_price.toLocaleString()} - {priceSpreadData.max_price.toLocaleString()} SAR
              </p>
            </div>
          </div>

          <div className="chart-container">
            {getChartData() && (
              <Scatter data={getChartData()} options={chartOptions} />
            )}
          </div>

          <div className="statistical-summary">
            <h3>Statistical Summary</h3>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">Median Price:</span>
                <span className="stat-value">{priceSpreadData.median_price.toLocaleString()} SAR</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Standard Deviation:</span>
                <span className="stat-value">{priceSpreadData.standard_deviation.toFixed(0)} SAR</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Coefficient of Variation:</span>
                <span className="stat-value">{priceSpreadData.coefficient_of_variation.toFixed(2)}%</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {!selectedMake && (
        <div className="placeholder-state">
          <p>Select a make to begin price spread analysis</p>
        </div>
      )}

      {selectedMake && !selectedModel && (
        <div className="placeholder-state">
          <p>Select a model to continue</p>
        </div>
      )}

      {selectedMake && selectedModel && !selectedYear && (
        <div className="placeholder-state">
          <p>Select a year to view price distribution</p>
        </div>
      )}
    </div>
  );
};

export default PriceSpreadAnalysis;
