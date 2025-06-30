import React, { useState, useEffect } from 'react';
import { Scatter } from 'react-chartjs-2';
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
  const [years, setYears] = useState([]);
  const [selectedMake, setSelectedMake] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [selectedYear, setSelectedYear] = useState('');
  const [priceSpreadData, setPriceSpreadData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch makes on component mount
  useEffect(() => {
    fetchMakes();
    fetchYears();
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

  // Fetch price spread data when all selections are made
  useEffect(() => {
    if (selectedMake && selectedModel && selectedYear) {
      fetchPriceSpreadData(selectedMake, selectedModel, selectedYear);
    } else {
      setPriceSpreadData(null);
    }
  }, [selectedMake, selectedModel, selectedYear]);

  const fetchMakes = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/makes`);
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
      const response = await fetch(`${process.env.REACT_APP_API_URL}/models/${encodeURIComponent(make)}`);
      if (!response.ok) throw new Error('Failed to fetch models');
      const data = await response.json();
      setModels(data);
    } catch (err) {
      console.error('Error fetching models:', err);
      setError('Failed to load models');
    }
  };

  const fetchYears = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/years`);
      if (!response.ok) throw new Error('Failed to fetch years');
      const data = await response.json();
      setYears(data.sort((a, b) => b - a)); // Sort descending
    } catch (err) {
      console.error('Error fetching years:', err);
      setError('Failed to load years');
    }
  };

  const fetchPriceSpreadData = async (make, model, year) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/api/analytics/price-spread?make=${encodeURIComponent(make)}&model=${encodeURIComponent(model)}&year=${year}`
      );
      
      if (!response.ok) throw new Error('Failed to fetch price spread data');
      
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
    const outliers = priceSpreadData.outliers || [];
    const outlierIds = new Set(outliers.map(o => o.ad_id));

    const normalData = listings
      .filter(listing => !outlierIds.has(listing.ad_id))
      .map((listing, index) => ({
        x: index + 1,
        y: listing.price,
        listing: listing
      }));

    const outlierData = listings
      .filter(listing => outlierIds.has(listing.ad_id))
      .map((listing, index) => ({
        x: listings.findIndex(l => l.ad_id === listing.ad_id) + 1,
        y: listing.price,
        listing: listing
      }));

    return {
      datasets: [
        {
          label: 'Normal Prices',
          data: normalData,
          backgroundColor: 'rgba(75, 192, 192, 0.6)',
          borderColor: 'rgba(75, 192, 192, 1)',
          pointRadius: 5,
        },
        {
          label: 'Outliers',
          data: outlierData,
          backgroundColor: 'rgba(255, 99, 132, 0.6)',
          borderColor: 'rgba(255, 99, 132, 1)',
          pointRadius: 8,
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
        text: `Price Distribution for ${selectedMake} ${selectedModel} ${selectedYear}`,
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
          Identify price outliers and market anomalies
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
            onChange={(e) => setSelectedModel(e.target.value)}
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
          <label htmlFor="year-select">Select Year:</label>
          <select
            id="year-select"
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
            disabled={!selectedModel}
            className="analysis-select"
          >
            <option value="">Choose a year...</option>
            {years.map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
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
            
            <div className="stat-card">
              <h3>Outliers Detected</h3>
              <p className="stat-value text-red">
                {priceSpreadData.outliers ? priceSpreadData.outliers.length : 0}
              </p>
            </div>
          </div>

          <div className="chart-container">
            {getChartData() && (
              <Scatter data={getChartData()} options={chartOptions} />
            )}
          </div>

          {priceSpreadData.outliers && priceSpreadData.outliers.length > 0 && (
            <div className="outliers-table">
              <h3>Price Outliers</h3>
              <table>
                <thead>
                  <tr>
                    <th>Price</th>
                    <th>Mileage</th>
                    <th>Location</th>
                    <th>Seller</th>
                    <th>Deviation</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {priceSpreadData.outliers.map((outlier) => (
                    <tr key={outlier.ad_id}>
                      <td className="price-cell">
                        {outlier.price.toLocaleString()} SAR
                      </td>
                      <td>{outlier.mileage || 'N/A'} km</td>
                      <td>{outlier.location_city || 'N/A'}</td>
                      <td>{outlier.seller || 'N/A'}</td>
                      <td className={outlier.deviation_type === 'high' ? 'high-outlier' : 'low-outlier'}>
                        {outlier.deviation_type === 'high' ? 'Above Market' : 'Below Market'}
                      </td>
                      <td>
                        <a 
                          href={outlier.url} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="view-listing-btn"
                        >
                          View
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

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
