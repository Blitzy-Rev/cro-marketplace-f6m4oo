import React from 'react'; // React v18.0.0
import ReactDOM from 'react-dom/client'; // React DOM v18.0.0
import App from './App';
// Function to render the app
function renderApp() {
    // Get the root element from the DOM
    const rootElement = document.getElementById('root');
    // Check if the root element exists
    if (!rootElement) {
        console.error('Root element not found in the DOM');
        return;
    }
    // Create a React root
    const root = ReactDOM.createRoot(rootElement);
    // Render the App component wrapped in React.StrictMode
    root.render(React.createElement(React.StrictMode, null,
        React.createElement(App, null)));
}
// Function to set up global error handling
function setupErrorHandling() {
    // Add event listener for 'error' events
    window.addEventListener('error', (event) => {
        // Log the error to the console
        console.error('Unhandled error:', event.error);
        // TODO: Send the error to an error tracking service
    });
}
// Call the renderApp function to render the app
renderApp();
// Call the setupErrorHandling function to set up global error handling
setupErrorHandling();