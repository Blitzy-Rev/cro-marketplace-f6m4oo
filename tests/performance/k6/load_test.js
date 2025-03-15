import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Trend } from 'k6/metrics';
import { loadTestConfig, thresholds, endpoints, testData } from './config.json';

// Global constants and custom metrics
const API_BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000/api/v1';
const csvProcessingTrend = new Trend('csv_processing_time');
const moleculeQueryTrend = new Trend('molecule_query_time');
const submissionTrend = new Trend('submission_creation_time');

// Export test configuration
export const options = {
  stages: loadTestConfig.stages,
  thresholds: thresholds,
  noConnectionReuse: false,
  userAgent: 'MoleculeFlow-LoadTest/1.0',
  summaryTimeUnit: 'ms',
};

/**
 * Prepare test data and environment before the load test begins
 */
export function setup() {
  console.log('Setting up test data and environment for load test execution');
  
  // Authenticate test users
  const pharmaAuth = authenticateUser(testData.users.pharma);
  const croAuth = authenticateUser(testData.users.cro);
  
  // Generate test CSV data with varying molecule counts
  const csvTemplates = {};
  for (const [size, config] of Object.entries(testData.csvFiles)) {
    csvTemplates[size] = generateTestCSV(config.moleculeCount, config.properties);
  }
  
  // Create test libraries for querying
  const libraryIds = [];
  if (pharmaAuth) {
    for (const lib of testData.libraries.testLibraries.slice(0, 2)) {
      const response = http.post(`${API_BASE_URL}${endpoints.libraries.create}`, JSON.stringify(lib), {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${pharmaAuth}`,
        },
      });
      
      if (response.status === 201) {
        const library = JSON.parse(response.body);
        libraryIds.push(library.id);
        console.log(`Created test library: ${library.name} (${library.id})`);
      }
    }
  }
  
  // Prepare some initial molecule data for tests
  let initialMolecules = [];
  if (pharmaAuth) {
    // Upload a small CSV to have some molecules available
    const initialCsvUpload = uploadCSV(pharmaAuth, csvTemplates.small);
    if (initialCsvUpload && initialCsvUpload.status === 'completed') {
      // Query for the molecules we just uploaded
      const queryResponse = queryMolecules(pharmaAuth, {
        limit: 50,
        offset: 0
      });
      initialMolecules = queryResponse.molecules || [];
      console.log(`Initial test data prepared with ${initialMolecules.length} molecules`);
    }
  }
  
  return {
    pharmaAuth,
    croAuth,
    csvTemplates,
    libraryIds,
    initialMolecules,
    scenarioWeights: loadTestConfig.scenarioWeights,
    thinkTimeBounds: loadTestConfig.thinkTimeBounds,
    testData,
  };
}

/**
 * Clean up test data after the load test completes
 * @param {Object} data - Test data from setup
 */
export function teardown(data) {
  console.log('Cleaning up after load test execution');
  
  // Log out authenticated sessions
  if (data.pharmaAuth) {
    http.post(`${API_BASE_URL}${endpoints.auth.logout}`, null, {
      headers: {
        'Authorization': `Bearer ${data.pharmaAuth}`,
      },
    });
  }
  
  if (data.croAuth) {
    http.post(`${API_BASE_URL}${endpoints.auth.logout}`, null, {
      headers: {
        'Authorization': `Bearer ${data.croAuth}`,
      },
    });
  }
  
  // Log test summary
  console.log(`Load test completed with ${data.libraryIds.length} test libraries`);
  console.log('Performance metrics have been recorded for analysis');
}

/**
 * Authenticate a user and return the authentication token
 * @param {Object} credentials - User credentials
 * @returns {string} Authentication token
 */
function authenticateUser(credentials) {
  const response = http.post(`${API_BASE_URL}${endpoints.auth.login}`, JSON.stringify({
    username: credentials.username,
    password: credentials.password,
  }), {
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  const checkResult = check(response, {
    'Authentication successful': (r) => r.status === 200,
    'Token received': (r) => JSON.parse(r.body).access_token !== undefined,
  });
  
  if (!checkResult) {
    console.error(`Authentication failed for ${credentials.username}: ${response.status} ${response.body}`);
    return null;
  }
  
  return JSON.parse(response.body).access_token;
}

/**
 * Upload a CSV file with molecule data and measure processing time
 * @param {Object} authToken - Authentication token
 * @param {Object} csvData - CSV data
 * @returns {Object} Upload response with job ID
 */
function uploadCSV(authToken, csvData) {
  const startTime = new Date();
  
  // Prepare file upload
  const filename = `test_upload_${startTime.getTime()}.csv`;
  const fileBlob = new Blob([csvData], { type: 'text/csv' });
  const formData = new FormData();
  formData.append('file', fileBlob, filename);
  
  // Upload CSV file
  const uploadResponse = http.post(`${API_BASE_URL}${endpoints.molecules.upload}`, formData, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
    },
  });
  
  const checkUpload = check(uploadResponse, {
    'CSV upload accepted': (r) => r.status === 202,
    'Job ID returned': (r) => JSON.parse(r.body).job_id !== undefined,
  });
  
  if (!checkUpload) {
    console.error(`CSV upload failed: ${uploadResponse.status} ${uploadResponse.body}`);
    return null;
  }
  
  const jobId = JSON.parse(uploadResponse.body).job_id;
  
  // Poll job status until complete
  let jobComplete = false;
  let attempts = 0;
  const maxAttempts = 30;
  let statusResponse;
  
  while (!jobComplete && attempts < maxAttempts) {
    sleep(1);
    attempts++;
    
    statusResponse = http.get(`${API_BASE_URL}${endpoints.molecules.status.replace('{id}', jobId)}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    });
    
    check(statusResponse, {
      'Status check successful': (r) => r.status === 200,
    });
    
    const status = JSON.parse(statusResponse.body).status;
    if (status === 'completed' || status === 'failed') {
      jobComplete = true;
    }
  }
  
  const endTime = new Date();
  const processingTime = endTime - startTime;
  
  csvProcessingTrend.add(processingTime);
  
  check(statusResponse, {
    'CSV processing completed successfully': (r) => JSON.parse(r.body).status === 'completed',
  });
  
  return {
    jobId,
    processingTime,
    status: statusResponse ? JSON.parse(statusResponse.body).status : 'unknown',
    moleculesProcessed: statusResponse ? JSON.parse(statusResponse.body).molecules_processed : 0,
  };
}

/**
 * Query molecules with filters and measure response time
 * @param {Object} authToken - Authentication token
 * @param {Object} filterParams - Filter parameters
 * @returns {Object} Query response with molecules
 */
function queryMolecules(authToken, filterParams) {
  const startTime = new Date();
  
  const queryResponse = http.post(`${API_BASE_URL}${endpoints.molecules.filter}`, JSON.stringify(filterParams), {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`,
    },
    tags: { name: 'filter' },
  });
  
  const endTime = new Date();
  const queryTime = endTime - startTime;
  
  moleculeQueryTrend.add(queryTime);
  
  check(queryResponse, {
    'Molecule query successful': (r) => r.status === 200,
    'Molecules returned': (r) => JSON.parse(r.body).molecules !== undefined,
  });
  
  return {
    queryTime,
    molecules: queryResponse.status === 200 ? JSON.parse(queryResponse.body).molecules : [],
    totalCount: queryResponse.status === 200 ? JSON.parse(queryResponse.body).total_count : 0,
  };
}

/**
 * Perform library management operations
 * @param {Object} authToken - Authentication token
 * @param {Object} libraryData - Library data
 * @returns {Object} Library operation response
 */
function manageLibrary(authToken, libraryData) {
  const results = {};
  
  group('Library Operations', function() {
    // Create a new library
    if (!libraryData.libraryId) {
      const createResponse = http.post(`${API_BASE_URL}${endpoints.libraries.create}`, JSON.stringify({
        name: `Load Test Library ${new Date().getTime()}`,
        description: 'Created during load testing',
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        tags: { name: 'library_operations' },
      });
      
      check(createResponse, {
        'Library creation successful': (r) => r.status === 201,
        'Library ID returned': (r) => JSON.parse(r.body).id !== undefined,
      });
      
      if (createResponse.status === 201) {
        results.libraryId = JSON.parse(createResponse.body).id;
      }
    } else {
      results.libraryId = libraryData.libraryId;
    }
    
    // Add molecules to library if we have a valid library ID
    if (results.libraryId && libraryData.moleculeIds && libraryData.moleculeIds.length > 0) {
      const addResponse = http.post(`${API_BASE_URL}${endpoints.libraries.molecules.replace('{id}', results.libraryId)}`, JSON.stringify({
        molecule_ids: libraryData.moleculeIds.slice(0, 10), // Limit to 10 molecules
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        tags: { name: 'library_operations' },
      });
      
      check(addResponse, {
        'Adding molecules to library successful': (r) => r.status === 200,
      });
    }
    
    // Get library details
    if (results.libraryId) {
      const getResponse = http.get(`${API_BASE_URL}${endpoints.libraries.detail.replace('{id}', results.libraryId)}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
        tags: { name: 'library_operations' },
      });
      
      check(getResponse, {
        'Library details retrieved successfully': (r) => r.status === 200,
      });
      
      if (getResponse.status === 200) {
        results.libraryDetails = JSON.parse(getResponse.body);
      }
    }
  });
  
  return results;
}

/**
 * Create a CRO submission with selected molecules
 * @param {Object} authToken - Authentication token
 * @param {Object} submissionData - Submission data
 * @returns {Object} Submission response with submission ID
 */
function createSubmission(authToken, submissionData) {
  const startTime = new Date();
  
  const payload = {
    name: submissionData.name || `Load Test Submission ${new Date().getTime()}`,
    cro_service: submissionData.cro_service || 'Binding Assay',
    molecule_ids: submissionData.molecule_ids || [],
    description: 'Created during load testing',
  };
  
  const submissionResponse = http.post(`${API_BASE_URL}${endpoints.submissions.create}`, JSON.stringify(payload), {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`,
    },
  });
  
  const endTime = new Date();
  const submissionTime = endTime - startTime;
  
  submissionTrend.add(submissionTime);
  
  check(submissionResponse, {
    'Submission creation successful': (r) => r.status === 201,
    'Submission ID returned': (r) => JSON.parse(r.body).id !== undefined,
  });
  
  let submissionId = null;
  if (submissionResponse.status === 201) {
    submissionId = JSON.parse(submissionResponse.body).id;
    
    // Get submission details
    const detailsResponse = http.get(`${API_BASE_URL}${endpoints.submissions.detail.replace('{id}', submissionId)}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    });
    
    check(detailsResponse, {
      'Submission details retrieved successfully': (r) => r.status === 200,
    });
  }
  
  return {
    submissionId,
    submissionTime,
    status: submissionResponse.status === 201 ? 'created' : 'failed',
  };
}

/**
 * Generate a test CSV file with the specified number of molecules
 * @param {number} count - Number of molecules to include
 * @param {Array} properties - Properties to include
 * @returns {string} CSV content
 */
function generateTestCSV(count, properties) {
  // Generate CSV header
  let csv = `SMILES,${properties.join(',')}\n`;
  
  // Add sample molecules to reach the desired count
  const sampleSmiles = testData.molecules.sampleSmiles;
  for (let i = 0; i < count; i++) {
    // Use sample SMILES strings and generate random property values
    const smileIndex = i % sampleSmiles.length;
    const smiles = sampleSmiles[smileIndex];
    
    let line = smiles;
    for (const prop of properties) {
      const range = testData.molecules.propertyRanges[prop] || { min: 0, max: 100 };
      const value = range.min + Math.random() * (range.max - range.min);
      line += `,${value.toFixed(2)}`;
    }
    
    csv += line + '\n';
  }
  
  return csv;
}

/**
 * Simulate a specific user scenario based on the scenario type
 * @param {Object} data - Test data
 * @param {string} scenarioType - Type of scenario to simulate
 * @returns {Object} Scenario execution results
 */
function simulateUserScenario(data, scenarioType) {
  const results = {};
  
  // Default to using pharma user authentication token
  const authToken = data.pharmaAuth;
  
  if (!authToken) {
    console.error('No authentication token available for scenario');
    return { error: 'Authentication failed' };
  }
  
  switch (scenarioType) {
    case 'csvUpload':
      // CSV upload scenario
      console.log('Executing CSV upload scenario');
      const csvSize = Math.random() < 0.8 ? 'small' : 'medium'; // 80% small, 20% medium
      results.csvUpload = uploadCSV(authToken, data.csvTemplates[csvSize]);
      break;
      
    case 'moleculeQuery':
      // Molecule query scenario
      console.log('Executing molecule query scenario');
      
      // Select a query pattern
      const queryPatterns = ['simple', 'moderate', 'complex'];
      const patternIndex = Math.floor(Math.random() * queryPatterns.length);
      const pattern = data.testData.queryPatterns[queryPatterns[patternIndex]];
      
      // Create filter parameters
      const filterParams = {
        properties: {},
        limit: pattern.limit,
        offset: 0,
      };
      
      // Add property ranges
      for (const prop of pattern.properties) {
        const range = data.testData.molecules.propertyRanges[prop];
        if (range) {
          // Create a random range within the bounds
          const rangeWidth = range.max - range.min;
          const lowerOffset = Math.random() * rangeWidth * 0.5;
          const upperOffset = Math.random() * rangeWidth * 0.5;
          
          filterParams.properties[prop] = {
            min: range.min + lowerOffset,
            max: range.max - upperOffset,
          };
        }
      }
      
      results.query = queryMolecules(authToken, filterParams);
      
      // If we got molecules back, maybe do a substructure search
      if (results.query.molecules.length > 0 && Math.random() < 0.3) {
        const substructureParams = {
          smiles: data.testData.molecules.sampleSmiles[0],
          limit: 10,
        };
        
        http.post(`${API_BASE_URL}${endpoints.molecules.search}`, JSON.stringify(substructureParams), {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`,
          },
        });
      }
      break;
      
    case 'libraryManagement':
      // Library management scenario
      console.log('Executing library management scenario');
      
      // Use existing molecules or query for new ones
      let moleculeIds = [];
      if (data.initialMolecules.length > 0) {
        // Use initial molecules we prepared during setup
        moleculeIds = data.initialMolecules.slice(0, 10).map(m => m.id);
      } else {
        // Query for some molecules
        const queryForLibrary = queryMolecules(authToken, {
          properties: {
            MW: { min: 100, max: 400 },
          },
          limit: 20,
        });
        
        moleculeIds = queryForLibrary.molecules.map(m => m.id);
      }
      
      // Use an existing library or create a new one
      const libraryId = data.libraryIds.length > 0 && Math.random() < 0.7 
        ? data.libraryIds[Math.floor(Math.random() * data.libraryIds.length)]
        : null;
      
      results.library = manageLibrary(authToken, {
        libraryId,
        moleculeIds,
      });
      
      // If we created a new library, save its ID
      if (results.library.libraryId && !libraryId) {
        data.libraryIds.push(results.library.libraryId);
      }
      break;
      
    case 'submission':
      // CRO submission scenario
      console.log('Executing CRO submission scenario');
      
      // Use existing molecules or query for new ones
      let submissionMoleculeIds = [];
      if (data.initialMolecules.length > 0) {
        // Use initial molecules we prepared during setup
        submissionMoleculeIds = data.initialMolecules.slice(0, 5).map(m => m.id);
      } else {
        // Query for some molecules
        const queryForSubmission = queryMolecules(authToken, {
          properties: {
            MW: { min: 200, max: 500 },
            LogP: { min: 1, max: 4 },
          },
          limit: 10,
        });
        
        submissionMoleculeIds = queryForSubmission.molecules.map(m => m.id);
      }
      
      if (submissionMoleculeIds.length > 0) {
        // Get one of the test submission templates
        const submissionTemplates = data.testData.submissions.testSubmissions;
        const template = submissionTemplates[Math.floor(Math.random() * submissionTemplates.length)];
        
        results.submission = createSubmission(authToken, {
          name: template.name,
          cro_service: template.cro_service,
          molecule_ids: submissionMoleculeIds.slice(0, Math.min(submissionMoleculeIds.length, template.molecule_count)),
        });
      } else {
        console.log('Not enough molecules found for submission');
      }
      break;
      
    default:
      console.error(`Unknown scenario type: ${scenarioType}`);
      results.error = `Unknown scenario type: ${scenarioType}`;
  }
  
  return results;
}

/**
 * Main test function that executes the load test scenario
 */
export default function(data) {
  // Determine which scenario to run based on random selection and scenario weights
  const rand = Math.random();
  const weights = data.scenarioWeights;
  
  let scenarioType;
  let cumulative = 0;
  
  for (const [scenario, weight] of Object.entries(weights)) {
    cumulative += weight;
    if (rand < cumulative) {
      scenarioType = scenario;
      break;
    }
  }
  
  // Execute the selected scenario
  const results = simulateUserScenario(data, scenarioType);
  
  // Add think time to simulate realistic user behavior
  const thinkTime = data.thinkTimeBounds.min + 
    Math.random() * (data.thinkTimeBounds.max - data.thinkTimeBounds.min);
  sleep(thinkTime);
}