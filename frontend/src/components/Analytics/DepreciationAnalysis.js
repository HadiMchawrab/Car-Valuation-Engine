import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import API_BASE_URL from '../../config/api';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import '../../styles/DepreciationAnalysis.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const DepreciationAnalysis = () => {
  const [makes, setMakes] = useState([]);
  const [models, setModels] = useState([]);
  const [selectedMake, setSelectedMake] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [depreciationData, setDepreciationData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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

  // Fetch depreciation data when both make and model are selected
  useEffect(() => {
    if (selectedMake && selectedModel) {
      fetchDepreciationData(selectedMake, selectedModel);
    } else {
      setDepreciationData(null);
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

  const fetchDepreciationData = async (make, model) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/analytics/depreciation?make=${encodeURIComponent(make)}&model=${encodeURIComponent(model)}`
      );
      
      if (!response.ok) {
        if (response.status === 400) {
          // Handle bad request - likely insufficient data
          const errorData = await response.json().catch(() => ({}));
          setError(`Cannot calculate depreciation for ${make} ${model}. Only one year of data exists - need at least 2 years to show depreciation trends.`);
          return;
        }
        throw new Error('Failed to fetch depreciation data');
      }
      
      const data = await response.json();
      
      // Additional client-side check for insufficient data
      if (!data.yearly_data || data.yearly_data.length < 2) {
        setError(`Cannot calculate depreciation for ${make} ${model}. Only one year of data exists - need at least 2 years to show depreciation trends.`);
        return;
      }
      
      setDepreciationData(data);
    } catch (err) {
      console.error('Error fetching depreciation data:', err);
      if (!error) { // Only set generic error if we haven't already set a specific one
        setError('Failed to load depreciation analysis');
      }
    } finally {
      setLoading(false);
    }
  };

  // Helper to get reversed yearly data
  const getReversedYearlyData = () => {
    if (!depreciationData || !depreciationData.yearly_data) return [];
    return [...depreciationData.yearly_data].sort((a, b) => b.year - a.year);
  };

  const getChartData = () => {
    const reversedData = getReversedYearlyData();
    if (!reversedData.length) return null;
    const years = reversedData.map(item => item.year);
    const prices = reversedData.map(item => item.average_price);
    return {
      labels: years,
      datasets: [
        {
          label: `${selectedMake} ${selectedModel} - Average Price`,
          data: prices,
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          fill: true,
          tension: 0.4,
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
        text: 'Vehicle Depreciation Curve',
      },
    },
    scales: {
      y: {
        beginAtZero: false,
        ticks: {
          callback: function(value) {
            return `${value.toLocaleString()} SAR`;
          },
        },
      },
    },
  };

  return (
    <div className="depreciation-analysis">
      <div className="analysis-header">
        <h2>📉 Depreciation Analysis</h2>
        <p className="analysis-subtitle">
          Analyze how vehicle values change over time
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
              setSelectedModel(''); // Reset model when make changes
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
      </div>

      {error && (
        <div className="error-message">
          <div className="error-icon">⚠️</div>
          <div className="error-content">
            <p>{error}</p>
            {error.includes('Only one year of data exists') && (
              <div className="error-suggestion">
                <p>💡 <strong>Try selecting:</strong></p>
                <ul>
                  <li>A more popular make/model combination</li>
                  <li>Different model years with more market data</li>
                  <li>Models that have been in production for multiple years</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {loading && (
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Calculating depreciation curve...</p>
        </div>
      )}

      {depreciationData && !loading && (
        <div className="depreciation-results">
          <div className="depreciation-stats">
            <div className="stat-card">
              <h3>Current Avg. Price</h3>
              <p className="stat-value">
                {depreciationData.current_avg_price ? 
                  `${depreciationData.current_avg_price.toLocaleString()} SAR` : 
                  'N/A'
                }
              </p>
            </div>
            
            <div className="stat-card">
              <h3>Highest Avg. Price</h3>
              <p className="stat-value">
                {depreciationData.highest_avg_price ? 
                  `${depreciationData.highest_avg_price.toLocaleString()} SAR` : 
                  'N/A'
                }
              </p>
            </div>
            
            <div className="stat-card">
              <h3>Total Depreciation</h3>
              <p className="stat-value">
                {depreciationData.total_depreciation_percentage ? 
                  `${depreciationData.total_depreciation_percentage}%` : 
                  'N/A'
                }
              </p>
            </div>
            
            <div className="stat-card">
              <h3>Annual Depreciation</h3>
              <p className="stat-value">
                {depreciationData.annual_depreciation_rate ? 
                  `${depreciationData.annual_depreciation_rate}%` : 
                  'N/A'
                }
              </p>
            </div>
          </div>

          <div className="chart-container">
            {getChartData() && (
              <Line data={getChartData()} options={chartOptions} />
            )}
          </div>

          <div className="depreciation-table">
            <h3>Year-by-Year Breakdown</h3>
            <table>
              <thead>
                <tr>
                  <th>Year</th>
                  <th>Average Price</th>
                  <th>Sample Size</th>
                  <th>Year-over-Year Change</th>
                </tr>
              </thead>
              <tbody>
                {getReversedYearlyData().map((item, index, arr) => {
                  const nextItem = index < arr.length - 1 ? arr[index + 1] : null;
                  const yoyChange = nextItem ?
                    (((item.average_price - nextItem.average_price) / item.average_price) * 100).toFixed(2) :
                    'N/A';
                  return (
                    <tr key={item.year}>
                      <td>{item.year}</td>
                      <td>{item.average_price.toLocaleString()} SAR</td>
                      <td>{item.listing_count}</td>
                      <td className={yoyChange !== 'N/A' && parseFloat(yoyChange) < 0 ? 'negative' : 'positive'}>
                        {yoyChange !== 'N/A' ? `${yoyChange}%` : 'N/A'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!selectedMake && (
        <div className="placeholder-state">
          <p>Select a make to begin depreciation analysis</p>
        </div>
      )}

      {selectedMake && !selectedModel && (
        <div className="placeholder-state">
          <p>Select a model to view depreciation curve</p>
        </div>
      )}
    </div>
  );
};

export default DepreciationAnalysis;
