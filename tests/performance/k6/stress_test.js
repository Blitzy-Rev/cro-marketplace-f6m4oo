import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Trend, Rate } from 'k6/metrics';
import { stressTestConfig, thresholds, endpoints, testData } from './config.json';

// Global variables
const API_BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000/api/v1';

// Custom metrics
const csvProcessingTrend = new Trend('csv_processing_time');
const moleculeQueryTrend = new Trend('molecule_query_time');
const submissionTrend = new Trend('submission_creation_time');
const errorRate = new Rate('error_rate');
const timeoutRate = new Rate('timeout_rate');

// Test configuration
export const options = {
  stages: stressTestConfig.stages,
  thresholds: thresholds,
  noConnectionReuse: true,
  userAgent: 'MoleculeFlowStressTest/1.0',
  summaryTimeUnit: 'ms',
};

// Setup function to prepare test data before the test starts
export function setup() {
  console.log('Preparing stress test data...');
  
  // Create multiple user credentials for concurrent authentication tests
  const users = [];
  for (let i = 0; i < 50; i++) {
    users.push({
      username: `stress_test_user_${i}@example.com`,
      password: 'StressTest123!',
    });
  }
  
  // Generate large test CSV data
  const largeCsvData = generateLargeCsvData(testData.csvFiles.large.moleculeCount);
  const extraLargeCsvData = generateLargeCsvData(testData.csvFiles.extraLarge.moleculeCount);
  
  // Create complex filter parameters for intensive queries
  const complexFilters = createComplexFilters();
  
  // Create batch submission data
  const batchSubmissions = createBatchSubmissions(20);
  
  // Authenticate a test user to verify API availability
  const loginUrl = `${API_BASE_URL}${endpoints.auth.login}`;
  const loginPayload = JSON.stringify(testData.users.pharma);
  const params = { headers: { 'Content-Type': 'application/json' } };
  
  const loginResponse = http.post(loginUrl, loginPayload, params);
  check(loginResponse, {
    'Setup authentication successful': (r) => r.status === 200,
  });
  
  if (loginResponse.status !== 200) {
    console.error('Setup failed: API unavailable or authentication failed');
  } else {
    console.log('Setup completed successfully');
  }
  
  // Return test data for use in the test
  return {
    users,
    authToken: loginResponse.json('token'),
    largeCsvData,
    extraLargeCsvData,
    complexFilters,
    batchSubmissions
  };
}

// Teardown function for cleanup after test
export function teardown(data) {
  console.log('Cleaning up after stress test...');
  
  // Log out authenticated sessions if possible
  if (data && data.authToken) {
    const logoutUrl = `${API_BASE_URL}${endpoints.auth.logout}`;
    const params = {
      headers: {
        'Authorization': `Bearer ${data.authToken}`,
        'Content-Type': 'application/json'
      }
    };
    
    http.post(logoutUrl, {}, params);
  }
  
  // Generate summary of stress test results
  console.log('===== Stress Test Summary =====');
  console.log('Breaking points identified:');
  console.log('- Check metrics for error rates during peak load');
  console.log('- Review response times with increasing VU count');
  console.log('- Analyze recovery patterns after stress periods');
  console.log('===============================');
}

// Main function executed for each virtual user
export default function() {
  const data = __ITER === 0 ? setup() : {};
  const thinkTime = Math.floor(Math.random() * 
    (stressTestConfig.thinkTimeBounds.max - stressTestConfig.thinkTimeBounds.min + 1)) + 
    stressTestConfig.thinkTimeBounds.min;
  
  // Determine which stress scenario to run based on VU ID and scenario weights
  const scenarioRandom = Math.random();
  const weights = stressTestConfig.scenarioWeights;
  
  let scenarioType;
  let cumulativeWeight = 0;
  
  for (const [scenario, weight] of Object.entries(weights)) {
    cumulativeWeight += weight;
    if (scenarioRandom <= cumulativeWeight) {
      scenarioType = scenario;
      break;
    }
  }
  
  // Execute the selected stress scenario
  try {
    const result = simulateStressScenario(data, scenarioType);
    
    // Add minimal think time to maximize system load
    sleep(thinkTime);
    
    return result;
  } catch (e) {
    console.error(`Error executing stress scenario ${scenarioType}: ${e.message}`);
    errorRate.add(1);
    return null;
  }
}

// Simulate concurrent authentication
function authenticateConcurrently(credentials) {
  const loginUrl = `${API_BASE_URL}${endpoints.auth.login}`;
  const payload = JSON.stringify({
    username: credentials.username,
    password: credentials.password,
  });
  
  const params = { 
    headers: { 'Content-Type': 'application/json' },
    timeout: '10s'  // Set longer timeout for stress conditions
  };
  
  let response;
  try {
    response = http.post(loginUrl, payload, params);
    
    // Check authentication success
    const success = check(response, {
      'Authentication successful': (r) => r.status === 200,
      'Token received': (r) => r.json('token') !== undefined,
    });
    
    if (!success) {
      errorRate.add(1);
      return null;
    }
    
    return response.json('token');
  } catch (e) {
    console.error(`Authentication failed: ${e.message}`);
    if (e.message.includes('timeout')) {
      timeoutRate.add(1);
    }
    errorRate.add(1);
    return null;
  }
}

// Upload large CSV file with molecule data
function uploadLargeCSV(authToken, csvData) {
  const uploadUrl = `${API_BASE_URL}${endpoints.molecules.upload}`;
  
  const payload = {
    file: http.file(csvData, 'large_molecule_data.csv', 'text/csv'),
  };
  
  const params = {
    headers: {
      'Authorization': `Bearer ${authToken}`,
    },
    timeout: '60s'  // Extend timeout for large file uploads
  };
  
  let startTime = new Date().getTime();
  
  try {
    const response = http.post(uploadUrl, payload, params);
    
    const success = check(response, {
      'CSV upload accepted': (r) => r.status === 202,
      'Job ID received': (r) => r.json('job_id') !== undefined,
    });
    
    if (!success) {
      errorRate.add(1);
      return null;
    }
    
    const jobId = response.json('job_id');
    
    // Poll for job completion (with a timeout limit)
    const maxPollAttempts = 10;
    let pollAttempt = 0;
    let jobComplete = false;
    
    while (pollAttempt < maxPollAttempts && !jobComplete) {
      sleep(3); // Wait between polls
      pollAttempt++;
      
      const statusUrl = `${API_BASE_URL}${endpoints.molecules.status.replace('{id}', jobId)}`;
      const statusResponse = http.get(statusUrl, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        }
      });
      
      if (check(statusResponse, {
        'Status check successful': (r) => r.status === 200,
      })) {
        const status = statusResponse.json('status');
        if (status === 'completed') {
          jobComplete = true;
        } else if (status === 'failed') {
          errorRate.add(1);
          break;
        }
      } else {
        errorRate.add(1);
      }
    }
    
    // Record processing time
    const endTime = new Date().getTime();
    const processingTime = endTime - startTime;
    csvProcessingTrend.add(processingTime);
    
    if (!jobComplete) {
      timeoutRate.add(1);
    }
    
    return {
      jobId,
      processingTime,
      completed: jobComplete
    };
  } catch (e) {
    console.error(`CSV upload failed: ${e.message}`);
    if (e.message.includes('timeout')) {
      timeoutRate.add(1);
    }
    errorRate.add(1);
    return null;
  }
}

// Execute complex molecule queries with multiple filters
function executeComplexQuery(authToken, complexFilterParams) {
  const queryUrl = `${API_BASE_URL}${endpoints.molecules.filter}`;
  
  const payload = JSON.stringify(complexFilterParams);
  
  const params = {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    },
    timeout: '30s'  // Extend timeout for complex queries
  };
  
  let startTime = new Date().getTime();
  
  try {
    const response = http.post(queryUrl, payload, params);
    
    const success = check(response, {
      'Query successful': (r) => r.status === 200,
      'Results returned': (r) => r.json('results') !== undefined,
    });
    
    if (!success) {
      errorRate.add(1);
      return null;
    }
    
    // Record query time
    const endTime = new Date().getTime();
    const queryTime = endTime - startTime;
    moleculeQueryTrend.add(queryTime);
    
    return {
      results: response.json('results'),
      count: response.json('count'),
      queryTime
    };
  } catch (e) {
    console.error(`Complex query failed: ${e.message}`);
    if (e.message.includes('timeout')) {
      timeoutRate.add(1);
    }
    errorRate.add(1);
    return null;
  }
}

// Create multiple CRO submissions concurrently
function createConcurrentSubmissions(authToken, batchSubmissionData) {
  const submissionUrl = `${API_BASE_URL}${endpoints.submissions.create}`;
  const responses = [];
  
  const params = {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    },
    timeout: '20s'
  };
  
  let startTime = new Date().getTime();
  
  try {
    // Create array of requests for batch sending
    const requests = batchSubmissionData.map(submission => {
      return ['POST', submissionUrl, JSON.stringify(submission), params];
    });
    
    // Send all requests in batch
    const batchResponses = http.batch(requests);
    
    // Process each response
    batchResponses.forEach((response, index) => {
      const success = check(response, {
        [`Submission ${index+1} created`]: (r) => r.status === 201,
        [`Submission ${index+1} ID received`]: (r) => r.json('id') !== undefined,
      });
      
      if (success) {
        responses.push({
          id: response.json('id'),
          status: response.json('status')
        });
      } else {
        errorRate.add(1);
      }
    });
    
    // Record submission creation time
    const endTime = new Date().getTime();
    const submissionTime = endTime - startTime;
    submissionTrend.add(submissionTime);
    
    return {
      submissions: responses,
      submissionTime
    };
  } catch (e) {
    console.error(`Concurrent submissions failed: ${e.message}`);
    if (e.message.includes('timeout')) {
      timeoutRate.add(1);
    }
    errorRate.add(1);
    return null;
  }
}

// Monitor system recovery after peak load
function monitorSystemRecovery(authToken, recoveryPeriod) {
  const recoveryMetrics = {
    responseTimes: [],
    errorCounts: [],
    recoveryComplete: false
  };
  
  // Make periodic lightweight requests to monitor recovery
  for (let i = 0; i < recoveryPeriod; i++) {
    // Simple molecule list request
    const url = `${API_BASE_URL}${endpoints.molecules.filter}`;
    const payload = JSON.stringify({
      properties: { MW: { min: 100, max: 200 } },
      limit: 10
    });
    
    const params = {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    };
    
    const startTime = new Date().getTime();
    const response = http.post(url, payload, params);
    const responseTime = new Date().getTime() - startTime;
    
    recoveryMetrics.responseTimes.push(responseTime);
    
    // Check for errors
    const success = response.status === 200;
    recoveryMetrics.errorCounts.push(success ? 0 : 1);
    
    // If response time is back to normal, consider recovery complete
    if (i > 3 && responseTime < 500 && success) {
      recoveryMetrics.recoveryComplete = true;
      break;
    }
    
    sleep(2);
  }
  
  return recoveryMetrics;
}

// Simulate a specific stress scenario
function simulateStressScenario(data, scenarioType) {
  // Authenticate first to get a valid token
  let authToken = data.authToken;
  if (!authToken) {
    // Use a random user from the generated list
    const userIndex = Math.floor(Math.random() * data.users.length);
    authToken = authenticateConcurrently(data.users[userIndex]);
    
    if (!authToken) {
      console.log('Authentication failed, cannot proceed with scenario');
      return null;
    }
  }
  
  // Execute scenario based on type
  let result = null;
  
  group(`Stress Scenario: ${scenarioType}`, () => {
    switch (scenarioType) {
      case 'concurrentAuth':
        // Simulate multiple concurrent authentication attempts
        const userIndex = Math.floor(Math.random() * data.users.length);
        result = authenticateConcurrently(data.users[userIndex]);
        break;
        
      case 'largeCSVUpload':
        // Upload large CSV with molecule data
        const csvData = Math.random() > 0.3 ? data.largeCsvData : data.extraLargeCsvData;
        result = uploadLargeCSV(authToken, csvData);
        break;
        
      case 'complexQuery':
        // Execute complex query with multiple filters
        const filterIndex = Math.floor(Math.random() * data.complexFilters.length);
        result = executeComplexQuery(authToken, data.complexFilters[filterIndex]);
        break;
        
      case 'concurrentSubmissions':
        // Create multiple submissions concurrently
        result = createConcurrentSubmissions(authToken, data.batchSubmissions);
        break;
        
      default:
        console.error(`Unknown scenario type: ${scenarioType}`);
        break;
    }
  });
  
  // For some of the requests, monitor recovery after the stress operation
  if (Math.random() < 0.1) {
    group('Recovery Monitoring', () => {
      const recoveryMetrics = monitorSystemRecovery(authToken, 5);
      // We don't return the recovery metrics but they're useful for analysis
    });
  }
  
  return result;
}

// Helper function to generate large CSV data
function generateLargeCsvData(moleculeCount) {
  let csvContent = 'SMILES,MW,LogP,TPSA,HBD,HBA,RotBonds,AromaticRings\n';
  
  const sampleSmiles = testData.molecules.sampleSmiles;
  
  // Generate rows
  for (let i = 0; i < moleculeCount; i++) {
    // Use one of the sample SMILES or generate a variation
    const smileIndex = i % sampleSmiles.length;
    const smiles = sampleSmiles[smileIndex] + (i > sampleSmiles.length ? `C${i % 10}` : '');
    
    // Generate random property values
    const mw = 100 + Math.random() * 400;
    const logP = -2 + Math.random() * 7;
    const tpsa = Math.random() * 140;
    const hbd = Math.floor(Math.random() * 6);
    const hba = Math.floor(Math.random() * 11);
    const rotBonds = Math.floor(Math.random() * 15);
    const aromaticRings = Math.floor(Math.random() * 5);
    
    csvContent += `${smiles},${mw.toFixed(2)},${logP.toFixed(2)},${tpsa.toFixed(2)},${hbd},${hba},${rotBonds},${aromaticRings}\n`;
    
    // Limit actual generation for testing purposes
    if (i >= 1000) {
      // K6 doesn't need the full file, just a representative sample
      break;
    }
  }
  
  return csvContent;
}

// Helper function to create complex filters for queries
function createComplexFilters() {
  const filters = [];
  
  // Create 10 different complex filter combinations
  for (let i = 0; i < 10; i++) {
    const ranges = testData.molecules.propertyRanges;
    
    // Create increasingly complex filters
    const filter = {
      properties: {
        MW: { 
          min: ranges.MW.min + (Math.random() * 50), 
          max: ranges.MW.max - (Math.random() * 50) 
        },
        LogP: { 
          min: ranges.LogP.min + (Math.random() * 1), 
          max: ranges.LogP.max - (Math.random() * 1) 
        },
        TPSA: { 
          min: ranges.TPSA.min + (Math.random() * 20), 
          max: ranges.TPSA.max - (Math.random() * 20) 
        }
      },
      limit: 500 + (i * 100),
      offset: i * 50
    };
    
    // Add more filter complexity for some filters
    if (i % 2 === 0) {
      filter.properties.HBD = { 
        min: ranges.HBD.min, 
        max: ranges.HBD.max - Math.floor(Math.random() * 2) 
      };
      filter.properties.HBA = { 
        min: ranges.HBA.min, 
        max: ranges.HBA.max - Math.floor(Math.random() * 3) 
      };
    }
    
    // Add substructure search for some filters (most intensive)
    if (i % 3 === 0) {
      const substructureIndex = Math.floor(Math.random() * testData.molecules.sampleSmiles.length);
      filter.substructure = testData.molecules.sampleSmiles[substructureIndex].substring(0, 3);
    }
    
    filters.push(filter);
  }
  
  return filters;
}

// Helper function to create batch submission data
function createBatchSubmissions(count) {
  const submissions = [];
  
  for (let i = 0; i < count; i++) {
    // Create a submission with randomized properties
    const submission = {
      name: `Stress Test Submission ${i+1}`,
      cro_service_id: `service-${i % 3 + 1}`,
      molecules: [],
      specifications: {
        concentration: 10 + (i % 5) * 10,
        replicates: 3,
        notes: `Stress test submission created by virtual user ${__VU}`
      }
    };
    
    // Add molecules to the submission
    const moleculeCount = 5 + (i % 10);
    for (let j = 0; j < moleculeCount; j++) {
      submission.molecules.push(`mol-${i}-${j}`);
    }
    
    submissions.push(submission);
  }
  
  return submissions;
}