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
      id: 'analytics-stats',
      name: 'Get Analytics Stats',
      path: '/api/analytics/stats',
      method: 'GET',
      description: 'Get overall analytics statistics with optional website filtering',
      parameters: [
        { name: 'websites', type: 'string', optional: true, description: 'Comma-separated list of websites to filter by' }
      ],
      response: `{
  "total_listings": 45678,
  "listings_this_month": 3456,
  "applied_filters": {
    "websites": ["dubizzle", "hatla2ee"]
  }
}`
    },
    {
      id: 'analytics-contributors',
      name: 'Get Top Contributors',
      path: '/api/analytics/contributors',
      method: 'GET',
      description: 'Get top contributors (sellers/agencies) with their listing statistics',
      parameters: [
        { name: 'limit', type: 'integer', default: '20', description: 'Number of contributors to return (1-100)' },
        { name: 'websites', type: 'string', optional: true, description: 'Comma-separated list of websites to filter by' }
      ],
      response: `{
  "contributors": [
    {
      "seller_name": "Al Futtaim Motors",
      "seller_id": "alfuttaim_001",
      "agency_name": "Al Futtaim Motors",
      "website": "dubizzle",
      "total_listings": 1250,
      "contributor_type": "agency"
    },
    {
      "seller_name": "Ahmed Al Mahmoud",
      "seller_id": "Ahmed Al Mahmoud",
      "agency_name": null,
      "website": "dubizzle",
      "total_listings": 45,
      "contributor_type": "individual_seller"
    }
  ],
  "total_count": 2
}`
    },
    {
      id: 'analytics-depreciation',
      name: 'Get Depreciation Analysis',
      path: '/api/analytics/depreciation',
      method: 'GET',
      description: 'Get depreciation analysis for a specific car make and model over time',
      parameters: [
        { name: 'make', type: 'string', description: 'Car make/brand (required)' },
        { name: 'model', type: 'string', description: 'Car model (required)' },
        { name: 'trim', type: 'string', optional: true, description: 'Car trim level' },
        { name: 'websites', type: 'string', optional: true, description: 'Comma-separated list of websites to filter by' }
      ],
      response: `{
  "make": "Toyota",
  "model": "Camry",
  "trim": "SE",
  "yearly_data": [
    {
      "year": 2018,
      "average_price": 95000.50,
      "listing_count": 25,
      "min_price": 85000,
      "max_price": 110000
    },
    {
      "year": 2019,
      "average_price": 88000.75,
      "listing_count": 30,
      "min_price": 78000,
      "max_price": 98000
    }
  ],
  "current_avg_price": 82000.25,
  "highest_avg_price": 95000.50,
  "total_depreciation_percentage": 13.68,
  "annual_depreciation_rate": 6.84,
  "analysis_period": "2018 - 2020",
  "data_points": 3
}`
    },
    {
      id: 'analytics-price-spread',
      name: 'Get Price Spread Analysis',
      path: '/api/analytics/price-spread',
      method: 'GET',
      description: 'Get price spread analysis for a specific car make, model, and year',
      parameters: [
        { name: 'make', type: 'string', description: 'Car make/brand (required)' },
        { name: 'model', type: 'string', description: 'Car model (required)' },
        { name: 'year', type: 'integer', description: 'Car year (required)' },
        { name: 'trim', type: 'string', optional: true, description: 'Car trim level' },
        { name: 'websites', type: 'string', optional: true, description: 'Comma-separated list of websites to filter by' }
      ],
      response: `{
  "make": "BMW",
  "model": "X5",
  "trim": null,
  "year": 2020,
  "total_listings": 15,
  "listings": [
    {
      "ad_id": "54321",
      "url": "https://example.com/listing/54321",
      "title": "BMW X5 2020 - Excellent Condition",
      "price": 285000,
      "mileage": 25000,
      "location_city": "Dubai",
      "seller": "Premium Motors",
      "post_date": "2024-01-10T14:20:00Z"
    }
  ],
  "average_price": 295500.75,
  "median_price": 290000.00,
  "min_price": 265000,
  "max_price": 340000,
  "standard_deviation": 18750.25,
  "coefficient_of_variation": 6.35
}`
    },
    {
      id: 'makes',
      name: 'Get All Makes',
      path: '/makes',
      method: 'GET',
      description: 'Get all available car makes/brands in the database',
      parameters: [
        { name: 'limit', type: 'integer', default: '200', description: 'Number of makes to return (1+)' },
        { name: 'offset', type: 'integer', default: '0', description: 'Number of items to skip (0+)' },
        { name: 'page', type: 'integer', optional: true, description: 'Page number (1+, overrides offset if provided)' },
        { name: 'meta', type: 'boolean', default: 'false', description: 'Include pagination metadata in response' }
      ],
      response: `{
  "items": ["Toyota", "BMW", "Mercedes-Benz", "Audi", "Nissan", "Ford"],
  "total_count": 45,
  "page": 1,
  "items_per_page": 200
}`
    },
    {
      id: 'models',
      name: 'Get All Models',
      path: '/models',
      method: 'GET',
      description: 'Get all available car models in the database',
      parameters: [
        { name: 'limit', type: 'integer', default: '200', description: 'Number of models to return (1+)' },
        { name: 'offset', type: 'integer', default: '0', description: 'Number of items to skip (0+)' },
        { name: 'page', type: 'integer', optional: true, description: 'Page number (1+, overrides offset if provided)' },
        { name: 'meta', type: 'boolean', default: 'false', description: 'Include pagination metadata in response' }
      ],
      response: `{
  "items": ["Camry", "Corolla", "X5", "3 Series", "C-Class", "A4", "Altima"],
  "total_count": 156,
  "page": 1,
  "items_per_page": 200
}`
    },
    {
      id: 'models-by-brand',
      name: 'Get Models by Brand',
      path: '/models/{brand}',
      method: 'GET',
      description: 'Get all models available for a specific car brand',
      parameters: [
        { name: 'brand', type: 'string', description: 'Car brand name', inPath: true },
        { name: 'limit', type: 'integer', default: '100', description: 'Number of models to return (1+)' },
        { name: 'offset', type: 'integer', default: '0', description: 'Number of items to skip (0+)' },
        { name: 'page', type: 'integer', optional: true, description: 'Page number (1+, overrides offset if provided)' },
        { name: 'meta', type: 'boolean', default: 'false', description: 'Include pagination metadata in response' }
      ],
      response: `{
  "items": ["Camry", "Corolla", "RAV4", "Highlander", "Prius", "Land Cruiser"],
  "total_count": 15,
  "page": 1,
  "items_per_page": 100
}`
    },
    {
      id: 'trims',
      name: 'Get Trims by Brand and Model',
      path: '/trims/{brand}/{model}',
      method: 'GET',
      description: 'Get all trim levels available for a specific car brand and model',
      parameters: [
        { name: 'brand', type: 'string', description: 'Car brand name', inPath: true },
        { name: 'model', type: 'string', description: 'Car model name', inPath: true },
        { name: 'seller', type: 'string', optional: true, description: 'Filter trims by seller/agency' },
        { name: 'limit', type: 'integer', default: '100', description: 'Number of trims to return (1+)' },
        { name: 'offset', type: 'integer', default: '0', description: 'Number of items to skip (0+)' },
        { name: 'page', type: 'integer', optional: true, description: 'Page number (1+, overrides offset if provided)' },
        { name: 'meta', type: 'boolean', default: 'false', description: 'Include pagination metadata in response' }
      ],
      response: `{
  "items": ["xDrive40i", "xDrive50i", "M50i", "xDrive30d"],
  "total_count": 4,
  "page": 1,
  "items_per_page": 100
}`
    },
    {
      id: 'fuel-types',
      name: 'Get Fuel Types',
      path: '/fuel-types',
      method: 'GET',
      description: 'Get all available fuel types',
      parameters: [],
      response: `["Gasoline", "Diesel", "Hybrid", "Electric", "CNG"]`
    },
    {
      id: 'body-types',
      name: 'Get Body Types',
      path: '/body-types',
      method: 'GET',
      description: 'Get all available body types',
      parameters: [],
      response: `["Sedan", "SUV", "Hatchback", "Coupe", "Convertible", "Wagon", "Pickup", "Van"]`
    },
    {
      id: 'transmission-types',
      name: 'Get Transmission Types',
      path: '/transmission-types',
      method: 'GET',
      description: 'Get all available transmission types',
      parameters: [],
      response: `["Automatic", "Manual", "CVT"]`
    },
    {
      id: 'locations',
      name: 'Get Locations',
      path: '/locations',
      method: 'GET',
      description: 'Get all available locations',
      parameters: [],
      response: `["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah", "Umm Al Quwain"]`
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


              <div className="example-section">
                <h3>Example Request</h3>
                <pre className="example-code">
                  <code>{`fetch("${
                    endpoint.id === 'root' ?
                      'https://markaba-backend-app.orangeocean-8c10ab2e.uaenorth.azurecontainerapps.io/' :
                    endpoint.id === 'listing-detail' ?  
                      'https://markaba-backend-app.orangeocean-8c10ab2e.uaenorth.azurecontainerapps.io/listings/123' :
                    endpoint.id === 'search' ?
                      'https://markaba-backend-app.orangeocean-8c10ab2e.uaenorth.azurecontainerapps.io/search?brand=Toyota&limit=20&meta=true' :

                    endpoint.id === 'analytics-stats' ?
                      'https://markaba-backend-app.orangeocean-8c10ab2e.uaenorth.azurecontainerapps.io/api/analytics/stats?websites=dubizzle,hatla2ee' :
                    endpoint.id === 'analytics-contributors' ?
                      'https://markaba-backend-app.orangeocean-8c10ab2e.uaenorth.azurecontainerapps.io/api/analytics/contributors?limit=10&websites=dubizzle' :
                    endpoint.id === 'analytics-depreciation' ?
                      'https://markaba-backend-app.orangeocean-8c10ab2e.uaenorth.azurecontainerapps.io/api/analytics/depreciation?make=Toyota&model=Camry&trim=SE&websites=dubizzle' :
                    endpoint.id === 'analytics-price-spread' ?
                      'https://markaba-backend-app.orangeocean-8c10ab2e.uaenorth.azurecontainerapps.io/api/analytics/price-spread?make=BMW&model=X5&year=2020&websites=dubizzle,hatla2ee' :
                    endpoint.id === 'makes' ?
                      'https://markaba-backend-app.orangeocean-8c10ab2e.uaenorth.azurecontainerapps.io/makes?limit=50&meta=true' :
                    endpoint.id === 'models' ?
                      'https://markaba-backend-app.orangeocean-8c10ab2e.uaenorth.azurecontainerapps.io/models?limit=100&meta=true' :
                    endpoint.id === 'models-by-brand' ?
                      'https://markaba-backend-app.orangeocean-8c10ab2e.uaenorth.azurecontainerapps.io/models/Toyota?limit=20&meta=true' :
                    endpoint.id === 'trims' ?
                      'https://markaba-backend-app.orangeocean-8c10ab2e.uaenorth.azurecontainerapps.io/trims/BMW/X5?seller=Premium%20Motors&meta=true' :
                    endpoint.id === 'fuel-types' ?
                      'https://markaba-backend-app.orangeocean-8c10ab2e.uaenorth.azurecontainerapps.io/fuel-types' :
                    endpoint.id === 'body-types' ?
                      'https://markaba-backend-app.orangeocean-8c10ab2e.uaenorth.azurecontainerapps.io/body-types' :
                    endpoint.id === 'transmission-types' ?
                      'https://markaba-backend-app.orangeocean-8c10ab2e.uaenorth.azurecontainerapps.io/transmission-types' :
                    endpoint.id === 'locations' ?
                      'https://markaba-backend-app.orangeocean-8c10ab2e.uaenorth.azurecontainerapps.io/locations' :
                    `${window.location.origin}${endpoint.path.replace(/{([^}]+)}/g, '123')}`
                  }", {
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
              <div className="response-section">
                <h3>Response</h3>
                <pre className="response-example">
                  <code>{endpoint.response}</code>
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
