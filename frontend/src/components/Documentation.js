import React, { useState } from 'react';
import '../styles/Documentation.css';

const Documentation = () => {
  const [activeEndpoint, setActiveEndpoint] = useState('root');

  const endpoints = [
    {
      id: 'root',
      name: 'Root',
      path: '/',
      method: 'GET',
      description: 'Welcome endpoint for the Markaba API',
      response: '{ "message": "Welcome to the Markaba API!" }',
      parameters: []
    },
    {
      id: 'listings',
      name: 'Get All Listings',
      path: '/listings',
      method: 'GET',
      description: 'Retrieve a paginated list of car listings',
      parameters: [
        { name: 'limit', type: 'integer', default: '10', description: 'Number of items per page (1-100)' },
        { name: 'offset', type: 'integer', default: '0', description: 'Number of items to skip' },
        { name: 'page', type: 'integer', optional: true, description: 'Page number (1-based, overrides offset if provided)' },
        { name: 'meta', type: 'boolean', default: 'false', description: 'Include pagination metadata in response' }
      ],
      response: `{
  "items": [
    {
      "ad_id": "string",
      "url": "string",
      "website": "string",
      "title": "string",
      "price": 0,
      "currency": "string",
      "brand": "string",
      "model": "string",
      "trim": "string",
      "year": 0,
      ...
    }
  ],
  "total_count": 0,
  "page": 1,
  "items_per_page": 10
}`
    },
    {
      id: 'listing-detail',
      name: 'Get Listing by ID',
      path: '/listings/{ad_id}',
      method: 'GET',
      description: 'Retrieve detailed information about a specific car listing',
      parameters: [
        { name: 'ad_id', type: 'string', description: 'The unique identifier of the listing', inPath: true }
      ],
      response: `{
  "ad_id": "string",
  "url": "string",
  "website": "string",
  "title": "string",
  "price": 0,
  "currency": "string",
  "brand": "string",
  "model": "string",
  "trim": "string",
  "year": 0,
  "mileage": 0,
  "mileage_unit": "string",
  "fuel_type": "string",
  "transmission_type": "string",
  "body_type": "string",
  "condition": "string",
  "color": "string",
  "seller": "string",
  "seller_type": "string",
  "location_city": "string",
  "location_region": "string",
  "image_url": "string",
  "number_of_images": 0,
  "post_date": "string"
}`
    },
    {
      id: 'search',
      name: 'Search Listings',
      path: '/search',
      method: 'GET',
      description: 'Search car listings with various filters and sorting options',
      parameters: [
        { name: 'brand', type: 'string', optional: true, description: 'Car brand' },
        { name: 'model', type: 'string', optional: true, description: 'Car model' },
        { name: 'trim', type: 'string', optional: true, description: 'Car trim' },
        { name: 'year', type: 'integer', optional: true, description: 'Exact year' },
        { name: 'min_price', type: 'integer', optional: true, description: 'Minimum price' },
        { name: 'max_price', type: 'integer', optional: true, description: 'Maximum price' },
        { name: 'min_year', type: 'integer', optional: true, description: 'Minimum year' },
        { name: 'max_year', type: 'integer', optional: true, description: 'Maximum year' },
        { name: 'min_mileage', type: 'integer', optional: true, description: 'Minimum mileage' },
        { name: 'max_mileage', type: 'integer', optional: true, description: 'Maximum mileage' },
        { name: 'fuel_type', type: 'string', optional: true, description: 'Fuel type' },
        { name: 'transmission_type', type: 'string', optional: true, description: 'Transmission type' },
        { name: 'body_type', type: 'string', optional: true, description: 'Body type' },
        { name: 'condition', type: 'string', optional: true, description: 'Car condition' },
        { name: 'color', type: 'string', optional: true, description: 'Car color' },
        { name: 'seller_type', type: 'string', optional: true, description: 'Type of seller' },
        { name: 'location_city', type: 'string', optional: true, description: 'City location' },
        { name: 'location_region', type: 'string', optional: true, description: 'Region location' },
        { name: 'website', type: 'string', optional: true, description: 'Source website' },
        { name: 'sort_by', type: 'string', default: 'post_date_desc', description: 'Sorting option (post_date_desc, post_date_asc, title_az, title_za, year_desc, year_asc, verified_seller, price_desc, price_asc)' },
        { name: 'limit', type: 'integer', default: '40', description: 'Number of items per page (1-100)' },
        { name: 'offset', type: 'integer', default: '0', description: 'Number of items to skip' },
        { name: 'page', type: 'integer', optional: true, description: 'Page number (1-based, overrides offset if provided)' },
        { name: 'meta', type: 'boolean', default: 'false', description: 'Include pagination metadata in response' }
      ],
      response: `{
  "items": [...],
  "total_count": 0,
  "page": 1,
  "items_per_page": 40
}`
    },
    {
      id: 'analytics-stats',
      name: 'Get Analytics Stats',
      path: '/api/analytics/stats',
      method: 'POST',
      description: 'Get analytics statistics with optional filters',
      parameters: [
        { name: 'filters', type: 'object', optional: true, description: 'Search filters (same as search endpoint)' }
      ],
      response: `{
  "total_listings": 1234,
  "listings_this_month": 123
}`
    },
    {
      id: 'top-contributors',
      name: 'Get Top Contributors',
      path: '/api/analytics/contributors',
      method: 'POST',
      description: 'Get top contributors with seller statistics and optional filtering',
      parameters: [
        { name: 'limit', type: 'integer', default: '20', description: 'Number of contributors to return (1-100)' },
        { name: 'search', type: 'object', optional: true, description: 'Search filters (same as search endpoint)' }
      ],
      response: `{
  "contributors": [
    {
      "seller_name": "string",
      "seller_id": "string",
      "agency_name": "string",
      "total_listings": 0,
      "contributor_type": "agency|individual_seller|unknown"
    }
  ],
  "total_count": 0
}`
    },
    {
      id: 'contributor-details',
      name: 'Get Contributor Details',
      path: '/api/analytics/contributor/{seller_identifier}',
      method: 'GET',
      description: 'Get detailed analytics for a specific contributor',
      parameters: [
        { name: 'seller_identifier', type: 'string', description: 'Seller name, seller_id, or agency name/ID', inPath: true }
      ],
      response: `{
  "seller_name": "string",
  "seller_id": "string",
  "agency_name": "string",
  "agency_id": "string",
  "total_listings": 0,
  "average_price": 0,
  "total_value": 0,
  "first_listing_date": "string",
  "last_listing_date": "string",
  "all_post_dates": ["string"],
  "all_prices": [0],
  "all_brands": ["string"],
  "all_models": ["string"],
  "contributor_type": "agency|individual_seller|unknown"
}`
    }
  ];

  return (
    <div className="documentation-container">
      <h1>Markaba API Documentation</h1>
      <p className="api-description">
        This documentation provides details on how to use the Markaba API to access car listings and analytics data.
      </p>

      <div className="documentation-content">
        <div className="endpoint-sidebar">
          <h3>Endpoints</h3>
          <ul>
            {endpoints.map(endpoint => (
              <li 
                key={endpoint.id} 
                className={activeEndpoint === endpoint.id ? 'active' : ''}
                onClick={() => setActiveEndpoint(endpoint.id)}
              >
                <span className={`method-badge ${endpoint.method.toLowerCase()}`}>{endpoint.method}</span>
                {endpoint.name}
              </li>
            ))}
          </ul>
        </div>

        <div className="endpoint-details">
          {endpoints.filter(endpoint => endpoint.id === activeEndpoint).map(endpoint => (
            <div key={endpoint.id} className="endpoint">
              <div className="endpoint-header">
                <div className="endpoint-method-path">
                  <span className={`method-badge large ${endpoint.method.toLowerCase()}`}>{endpoint.method}</span>
                  <h2 className="endpoint-path">{endpoint.path}</h2>
                </div>
                <p className="endpoint-name">{endpoint.name}</p>
              </div>
              
              <div className="endpoint-description">
                <p>{endpoint.description}</p>
              </div>

              <div className="parameters-section">
                <h3>Parameters</h3>
                {endpoint.parameters.length === 0 ? (
                  <p>No parameters</p>
                ) : (
                  <table className="parameters-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Required</th>
                        <th>Default</th>
                        <th>Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {endpoint.parameters.map((param, index) => (
                        <tr key={index}>
                          <td className={param.inPath ? 'path-param' : ''}>
                            {param.name}
                            {param.inPath && <span className="param-badge path">path</span>}
                          </td>
                          <td>{param.type}</td>
                          <td>{param.optional ? 'No' : 'Yes'}</td>
                          <td>{param.default || '-'}</td>
                          <td>{param.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              <div className="response-section">
                <h3>Response</h3>
                <pre className="response-example">
                  <code>{endpoint.response}</code>
                </pre>
              </div>

              <div className="example-section">
                <h3>Example Request</h3>
                <pre className="example-code">
                  <code>{`fetch("${window.location.origin}${endpoint.path.replace(/{([^}]+)}/g, '123')}", {
  method: "${endpoint.method}",${endpoint.method !== 'GET' ? `
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify(${endpoint.id === 'analytics-stats' ? '{ filters: {} }' : 
    endpoint.id === 'top-contributors' ? '{ limit: 20 }' : '{}'}),` : ''}
})
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error("Error:", error));`}</code>
                </pre>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Documentation;
