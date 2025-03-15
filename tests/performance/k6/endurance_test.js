import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Trend, Rate } from 'k6/metrics';
import { enduranceTestConfig, thresholds, endpoints, testData } from './config.json';

// Define the API base URL
const API_BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000/api/v1';

// Custom metrics to track specific performance aspects over time
const csvProcessingTrend = new Trend('csv_processing_time');
const moleculeQueryTrend = new Trend('molecule_query_time');
const submissionTrend = new Trend('submission_creation_time');
const responseTimeDegradation = new Trend('response_time_degradation');
const memoryLeakIndicator = new Trend('memory_leak_indicator');

// Test configuration
export const options = {
  stages: enduranceTestConfig.stages,
  thresholds: thresholds,
  noConnectionReuse: true, // More realistic behavior for endurance testing
  userAgent: 'MolecularPlatform-EnduranceTest/1.0',
  summaryTimeUnit: 'min', // Better for long-running tests
  duration: enduranceTestConfig.duration, // 24h
};

// Setup function to prepare test data
export function setup() {
  console.log('Starting endurance test setup');
  
  // Generate test user credentials for sustained usage
  const users = [];
  for (let i = 0; i < 10; i++) {
    users.push({
      username: `endurance_test_user_${i}`,
      password: 'TestPassword123!',
      role: i % 3 === 0 ? 'pharma_scientist' : (i % 3 === 1 ? 'cro_technician' : 'system_administrator')
    });
  }

  // Create test CSV data with various molecule counts
  const csvData = {
    small: generateCsvData(testData.csvFiles.small.moleculeCount, testData.csvFiles.small.properties),
    medium: generateCsvData(testData.csvFiles.medium.moleculeCount, testData.csvFiles.medium.properties),
    large: generateCsvData(testData.csvFiles.large.moleculeCount, testData.csvFiles.large.properties),
  };
  
  // Prepare query patterns of varying complexity
  const queryPatterns = [];
  for (const [type, pattern] of Object.entries(testData.queryPatterns)) {
    queryPatterns.push({
      type,
      properties: pattern.properties,
      limit: pattern.limit,
      substructure: pattern.substructure || false
    });
  }
  
  // Set up periodic submission schedules
  const submissionSchedules = [
    { interval: 60 * 60, count: 5 },     // Every hour, 5 molecules
    { interval: 4 * 60 * 60, count: 10 }, // Every 4 hours, 10 molecules
    { interval: 8 * 60 * 60, count: 20 }, // Every 8 hours, 20 molecules
  ];
  
  // Initialize metrics for tracking performance degradation
  const baselineMetrics = {
    authResponseTime: 0,
    csvProcessingTime: 0,
    queryResponseTime: 0,
    submissionTime: 0,
    memoryBaseline: 0
  };
  
  console.log('Endurance test setup complete');
  
  return {
    testStartTime: Date.now(),
    users,
    csvData,
    queryPatterns,
    submissionSchedules,
    baselineMetrics,
    executionTimes: {
      lastCsvUpload: {},
      lastQuery: {},
      lastSubmission: {},
      lastAuthRefresh: {}
    }
  };
}

// Teardown function to clean up after endurance test completes
export function teardown(data) {
  console.log('Starting endurance test teardown');
  
  // Log out authenticated sessions
  for (let i = 0; i < data.users.length; i++) {
    try {
      const logoutUrl = `${API_BASE_URL}${endpoints.auth.logout}`;
      http.post(logoutUrl, {}, {
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (e) {
      console.error(`Error logging out user: ${e}`);
    }
  }
  
  // Generate summary of endurance test results
  console.log('=== Endurance Test Results Summary ===');
  console.log(`Test duration: ${(Date.now() - data.testStartTime) / (1000 * 60 * 60)} hours`);
  
  // Analyze performance degradation patterns
  if (responseTimeDegradation.values && responseTimeDegradation.values.avg !== undefined) {
    console.log(`Average response time degradation: ${responseTimeDegradation.values.avg.toFixed(2)}%`);
    console.log(`Max response time degradation: ${responseTimeDegradation.values.max.toFixed(2)}%`);
  }
  
  // Document any identified resource leaks or degradation
  if (memoryLeakIndicator.values && memoryLeakIndicator.values.avg !== undefined) {
    const memLeakAvg = memoryLeakIndicator.values.avg;
    console.log(`Memory leak indicator: ${memLeakAvg.toFixed(4)}`);
    
    if (memLeakAvg > 0.1) {
      console.log('WARNING: Potential memory leak detected. Further investigation recommended.');
    } else {
      console.log('No significant memory leaks detected.');
    }
  }
  
  console.log('Endurance test teardown complete');
}

// Helper function to generate test CSV data
function generateCsvData(count, properties) {
  // Generate a CSV string with SMILES and properties
  // This is a simplified version - in a real test, this would generate valid molecule data
  let csv = 'SMILES,' + properties.join(',') + '\n';
  
  const sampleSmiles = testData.molecules.sampleSmiles;
  
  for (let i = 0; i < Math.min(count, 20); i++) {
    // Generate a row with a sample SMILES and random property values
    const smiles = sampleSmiles[i % sampleSmiles.length];
    let row = smiles;
    
    for (const prop of properties) {
      if (prop === 'MW') {
        row += `,${Math.random() * (testData.molecules.propertyRanges.MW.max - testData.molecules.propertyRanges.MW.min) + testData.molecules.propertyRanges.MW.min}`;
      } else if (prop === 'LogP') {
        row += `,${Math.random() * (testData.molecules.propertyRanges.LogP.max - testData.molecules.propertyRanges.LogP.min) + testData.molecules.propertyRanges.LogP.min}`;
      } else {
        row += `,${Math.random() * 10}`; // Default random value for other properties
      }
    }
    
    csv += row + '\n';
  }
  
  // Note: This returns a simplified CSV - for actual testing, we'd generate count rows
  // but for memory efficiency in the test script, we're just returning a sample
  return {
    count,
    properties,
    data: csv
  };
}

// Authenticate user and handle token refresh over extended periods
function authenticateWithRefresh(credentials, refreshInterval) {
  const loginUrl = `${API_BASE_URL}${endpoints.auth.login}`;
  const payload = JSON.stringify({
    username: credentials.username,
    password: credentials.password
  });
  
  const params = {
    headers: { 'Content-Type': 'application/json' },
  };
  
  // Measure authentication time for performance tracking
  const startTime = Date.now();
  const loginResponse = http.post(loginUrl, payload, params);
  const authResponseTime = Date.now() - startTime;
  
  const authSuccessful = check(loginResponse, {
    'Authentication successful': (r) => r.status === 200,
    'Access token received': (r) => JSON.parse(r.body).access_token !== undefined,
    'Refresh token received': (r) => JSON.parse(r.body).refresh_token !== undefined,
  });
  
  if (!authSuccessful) {
    console.error(`Authentication failed: ${loginResponse.status} ${loginResponse.body}`);
    return null;
  }
  
  const tokens = JSON.parse(loginResponse.body);
  
  // Track authentication response times over test duration
  // This helps identify potential degradation in the auth system
  responseTimeDegradation.add(authResponseTime);
  
  // Setup token refresh mechanism
  const refreshToken = function() {
    const refreshUrl = `${API_BASE_URL}${endpoints.auth.refresh}`;
    const refreshPayload = JSON.stringify({
      refresh_token: tokens.refresh_token
    });
    
    const refreshResponse = http.post(refreshUrl, refreshPayload, params);
    
    if (refreshResponse.status === 200) {
      const newTokens = JSON.parse(refreshResponse.body);
      tokens.access_token = newTokens.access_token;
      tokens.refresh_token = newTokens.refresh_token || tokens.refresh_token;
      return true;
    } else {
      console.error(`Token refresh failed: ${refreshResponse.status} ${refreshResponse.body}`);
      return false;
    }
  };
  
  // Add refresh function to tokens object
  tokens.refresh = refreshToken;
  
  return tokens;
}

// Upload CSV files periodically to simulate regular data imports
function uploadPeriodicCSV(authToken, csvData, frequency) {
  const uploadUrl = `${API_BASE_URL}${endpoints.molecules.upload}`;
  
  // Prepare CSV upload request with mapping
  const requestBody = {
    file: csvData.data,
    mapping: {}
  };
  
  // Create mapping for each property in the CSV
  requestBody.mapping['SMILES'] = 'SMILES';
  for (const prop of csvData.properties) {
    if (prop === 'MW') {
      requestBody.mapping[prop] = 'Molecular Weight';
    } else if (prop === 'LogP') {
      requestBody.mapping[prop] = 'LogP';
    } else if (prop === 'TPSA') {
      requestBody.mapping[prop] = 'Topological Polar Surface Area';
    } else {
      requestBody.mapping[prop] = prop; // Default mapping
    }
  }
  
  const payload = JSON.stringify(requestBody);
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
  };
  
  const startTime = Date.now();
  const response = http.post(uploadUrl, payload, params);
  
  const uploadSuccessful = check(response, {
    'CSV upload accepted': (r) => r.status === 202,
    'Job ID returned': (r) => JSON.parse(r.body).job_id !== undefined,
  });
  
  if (!uploadSuccessful) {
    console.error(`CSV upload failed: ${response.status} ${response.body}`);
    return null;
  }
  
  const jobId = JSON.parse(response.body).job_id;
  
  // Poll job status until complete or timeout
  let jobComplete = false;
  let attempts = 0;
  let jobStatus;
  
  while (!jobComplete && attempts < 60) { // Max 5 minutes (60 * 5s)
    sleep(5); // Wait 5 seconds between status checks
    attempts++;
    
    const statusUrl = `${API_BASE_URL}${endpoints.molecules.status.replace('{id}', jobId)}`;
    const statusResponse = http.get(statusUrl, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    
    if (statusResponse.status === 200) {
      jobStatus = JSON.parse(statusResponse.body);
      jobComplete = jobStatus.status === 'completed' || jobStatus.status === 'failed';
    }
  }
  
  const processingTime = Date.now() - startTime;
  
  // Record processing time for performance tracking
  if (jobStatus && jobStatus.status === 'completed') {
    csvProcessingTrend.add(processingTime);
    
    // Track for degradation over time
    responseTimeDegradation.add(processingTime / csvData.count * 10000); // Normalize to processing time per 10K molecules
  }
  
  return {
    jobId,
    status: jobStatus ? jobStatus.status : 'unknown',
    processingTime,
    moleculesProcessed: jobStatus ? jobStatus.molecules_processed : 0
  };
}

// Execute molecule queries consistently over time with varying patterns
function executeConsistentQueries(authToken, queryPatterns) {
  // Select a query pattern from available patterns
  const patternIndex = Math.floor(Math.random() * queryPatterns.length);
  const selectedPattern = queryPatterns[patternIndex];
  
  const queryUrl = `${API_BASE_URL}${endpoints.molecules.filter}`;
  
  // Prepare filter parameters based on selected pattern
  const requestBody = {
    filters: {
      properties: {}
    },
    limit: selectedPattern.limit,
    offset: 0
  };
  
  // Add property filters based on pattern
  selectedPattern.properties.forEach(prop => {
    if (prop === 'MW') {
      requestBody.filters.properties.MW = { 
        min: testData.molecules.propertyRanges.MW.min, 
        max: testData.molecules.propertyRanges.MW.max 
      };
    } else if (prop === 'LogP') {
      requestBody.filters.properties.LogP = { 
        min: testData.molecules.propertyRanges.LogP.min, 
        max: testData.molecules.propertyRanges.LogP.max 
      };
    } else if (prop === 'TPSA') {
      requestBody.filters.properties.TPSA = { min: 0, max: 140 };
    } else if (prop === 'HBD') {
      requestBody.filters.properties.HBD = { min: 0, max: 5 };
    } else if (prop === 'HBA') {
      requestBody.filters.properties.HBA = { min: 0, max: 10 };
    }
  });
  
  // Add substructure search if specified in the pattern
  if (selectedPattern.substructure) {
    requestBody.filters.substructure = testData.molecules.sampleSmiles[0];
  }
  
  const payload = JSON.stringify(requestBody);
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
  };
  
  const startTime = Date.now();
  const response = http.post(queryUrl, payload, params);
  const queryTime = Date.now() - startTime;
  
  const querySuccessful = check(response, {
    'Query successful': (r) => r.status === 200,
    'Results returned': (r) => JSON.parse(r.body).molecules !== undefined,
  });
  
  if (querySuccessful) {
    moleculeQueryTrend.add(queryTime);
    
    // Track for degradation over time
    // Weight by query complexity - complex queries naturally take longer
    const complexityFactor = selectedPattern.type === 'simple' ? 1 : 
                            (selectedPattern.type === 'moderate' ? 1.5 : 2);
    responseTimeDegradation.add(queryTime / complexityFactor);
  }
  
  return {
    status: response.status,
    queryTime,
    resultCount: querySuccessful ? JSON.parse(response.body).molecules.length : 0,
    patternType: selectedPattern.type
  };
}

// Create CRO submissions periodically to simulate regular workflow
function createPeriodicSubmissions(authToken, submissionData, frequency) {
  const submissionUrl = `${API_BASE_URL}${endpoints.submissions.create}`;
  
  // Prepare submission request with specified molecules
  const requestBody = {
    name: `Endurance Test Submission - ${Date.now()}`,
    cro_service_id: submissionData.cro_service,
    description: "Automated endurance test submission",
    molecules: [], // Would include actual molecule IDs in a real test
    specifications: {
      timeline: "Standard",
      special_requirements: "Endurance test submission"
    }
  };
  
  // Add placeholder molecule IDs - in a real test, these would be actual IDs from the database
  for (let i = 0; i < submissionData.molecule_count; i++) {
    requestBody.molecules.push(`molecule-${Date.now()}-${i}`);
  }
  
  const payload = JSON.stringify(requestBody);
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
  };
  
  const startTime = Date.now();
  const response = http.post(submissionUrl, payload, params);
  const submissionTime = Date.now() - startTime;
  
  const submissionSuccessful = check(response, {
    'Submission created': (r) => r.status === 201,
    'Submission ID returned': (r) => JSON.parse(r.body).id !== undefined,
  });
  
  if (submissionSuccessful) {
    submissionTrend.add(submissionTime);
    
    // Track for degradation over time
    responseTimeDegradation.add(submissionTime);
  }
  
  return {
    status: response.status,
    submissionTime,
    submissionId: submissionSuccessful ? JSON.parse(response.body).id : null
  };
}

// Track performance metrics over time to identify degradation patterns
function trackPerformanceDegradation(baselineMetrics, currentMetrics) {
  const degradation = {};
  const degradationThresholds = enduranceTestConfig.degradationThresholds;
  
  // Calculate percentage degradation for each metric compared to baseline
  for (const [key, value] of Object.entries(currentMetrics)) {
    if (baselineMetrics[key] && baselineMetrics[key] > 0) {
      degradation[key] = ((value - baselineMetrics[key]) / baselineMetrics[key]) * 100;
    } else {
      // If baseline not yet established, set current value as baseline
      baselineMetrics[key] = value;
      degradation[key] = 0;
    }
  }
  
  // Track memory usage patterns over time to identify potential leaks
  // This is a simplified approach - in a real test, this would use actual memory metrics
  let memoryLeakScore = 0;
  
  // Calculate a memory leak score based on response time degradation patterns
  // Consistent increases in response time can indicate memory problems
  if (degradation.authResponseTime > degradationThresholds.responseTime * 100) {
    memoryLeakScore += 0.2;
  }
  
  if (degradation.csvProcessingTime > degradationThresholds.responseTime * 100) {
    memoryLeakScore += 0.3;
  }
  
  if (degradation.queryResponseTime > degradationThresholds.responseTime * 100) {
    memoryLeakScore += 0.3;
  }
  
  if (degradation.submissionTime > degradationThresholds.responseTime * 100) {
    memoryLeakScore += 0.2;
  }
  
  memoryLeakIndicator.add(memoryLeakScore);
  
  return {
    degradation,
    memoryLeakScore
  };
}

// Simulate a specific user scenario for endurance testing
function simulateEnduranceScenario(data, scenarioType, executionTime) {
  // Get user based on VU ID for consistent user behavior
  const userIndex = __VU % data.users.length;
  const user = data.users[userIndex];
  
  // Default auth token refresh interval (15 minutes)
  const refreshInterval = 15 * 60;
  
  // Ensure last execution times are initialized for this VU
  if (!data.executionTimes.lastCsvUpload[__VU]) {
    data.executionTimes.lastCsvUpload[__VU] = 0;
  }
  
  if (!data.executionTimes.lastQuery[__VU]) {
    data.executionTimes.lastQuery[__VU] = 0;
  }
  
  if (!data.executionTimes.lastSubmission[__VU]) {
    data.executionTimes.lastSubmission[__VU] = 0;
  }
  
  if (!data.executionTimes.lastAuthRefresh[__VU]) {
    data.executionTimes.lastAuthRefresh[__VU] = 0;
  }
  
  switch (scenarioType) {
    case 'authentication':
      // Authentication scenario with token refresh
      group('Authentication Scenario', () => {
        const auth = authenticateWithRefresh(user, refreshInterval);
        
        if (auth) {
          // Periodically refresh token to simulate long-running sessions
          if (executionTime - data.executionTimes.lastAuthRefresh[__VU] > refreshInterval) {
            auth.refresh();
            data.executionTimes.lastAuthRefresh[__VU] = executionTime;
          }
          
          // Track authentication performance
          const currentMetrics = {
            authResponseTime: responseTimeDegradation.values.avg || 0
          };
          
          trackPerformanceDegradation(data.baselineMetrics, currentMetrics);
        }
      });
      break;
      
    case 'periodicCSVUpload':
      // Periodic CSV uploads to test data processing over time
      group('CSV Upload Scenario', () => {
        const auth = authenticateWithRefresh(user, refreshInterval);
        
        if (auth) {
          // Upload CSV files at specified intervals based on test duration
          const hoursSinceLastUpload = (executionTime - data.executionTimes.lastCsvUpload[__VU]) / 3600;
          
          // Upload frequency varies based on CSV size
          // Small CSVs: every 1-2 hours, Medium: every 4-6 hours, Large: every 8-12 hours
          if ((hoursSinceLastUpload > 1 && Math.random() < 0.5) || hoursSinceLastUpload > 2) {
            // Select CSV size - weighted toward smaller files
            const rand = Math.random();
            let csvType = 'small';
            
            if (rand > 0.7 && rand <= 0.95) {
              csvType = 'medium';
            } else if (rand > 0.95) {
              csvType = 'large';
            }
            
            const uploadResult = uploadPeriodicCSV(auth.access_token, data.csvData[csvType], csvType);
            data.executionTimes.lastCsvUpload[__VU] = executionTime;
            
            if (uploadResult) {
              const currentMetrics = {
                csvProcessingTime: uploadResult.processingTime
              };
              
              trackPerformanceDegradation(data.baselineMetrics, currentMetrics);
            }
          }
        }
      });
      break;
      
    case 'consistentQueries':
      // Consistent querying to test database performance over time
      group('Query Scenario', () => {
        const auth = authenticateWithRefresh(user, refreshInterval);
        
        if (auth) {
          // Execute queries at a consistent pace
          // Vary the timing a bit to simulate real user behavior
          const queryResult = executeConsistentQueries(auth.access_token, data.queryPatterns);
          
          if (queryResult) {
            const currentMetrics = {
              queryResponseTime: queryResult.queryTime
            };
            
            trackPerformanceDegradation(data.baselineMetrics, currentMetrics);
          }
        }
      });
      break;
      
    case 'periodicSubmissions':
      // Periodic CRO submissions to test workflow processing
      group('CRO Submission Scenario', () => {
        const auth = authenticateWithRefresh(user, refreshInterval);
        
        if (auth) {
          // Create submissions at specified intervals
          const hoursSinceLastSubmission = (executionTime - data.executionTimes.lastSubmission[__VU]) / 3600;
          
          // Submissions happen less frequently than queries
          // Target about 6 submissions per day per user
          if (hoursSinceLastSubmission > 4) {
            const submissionIndex = Math.floor(Math.random() * testData.submissions.testSubmissions.length);
            const submissionData = testData.submissions.testSubmissions[submissionIndex];
            
            const submissionResult = createPeriodicSubmissions(auth.access_token, submissionData, '4h');
            data.executionTimes.lastSubmission[__VU] = executionTime;
            
            if (submissionResult) {
              const currentMetrics = {
                submissionTime: submissionResult.submissionTime
              };
              
              trackPerformanceDegradation(data.baselineMetrics, currentMetrics);
            }
          }
        }
      });
      break;
      
    default:
      console.error(`Unknown scenario type: ${scenarioType}`);
  }
}

// Main test function executed by k6
export default function() {
  // Get test data from setup and ensure we persist state between iterations
  const data = __ENV.SHARED_ITERATIONS ? __ITER === 0 ? setup() : global.testData : global.testData || (global.testData = setup());
  
  // Calculate execution time in seconds since test start
  const executionTime = (Date.now() - data.testStartTime) / 1000;
  
  // Determine scenario type based on weighted distribution
  const scenarioWeights = enduranceTestConfig.scenarioWeights;
  const scenarioTypes = Object.keys(scenarioWeights);
  
  // Weighted random selection of scenario
  let selectedScenario;
  const random = Math.random();
  let cumulativeWeight = 0;
  
  for (const type of scenarioTypes) {
    cumulativeWeight += scenarioWeights[type];
    if (random < cumulativeWeight) {
      selectedScenario = type;
      break;
    }
  }
  
  // Execute the selected scenario
  simulateEnduranceScenario(data, selectedScenario, executionTime);
  
  // Add realistic think time between actions
  const thinkTime = Math.random() * 
    (enduranceTestConfig.thinkTimeBounds.max - enduranceTestConfig.thinkTimeBounds.min) + 
    enduranceTestConfig.thinkTimeBounds.min;
  
  sleep(thinkTime);
}