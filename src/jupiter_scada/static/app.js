/**
 * Jupiter SCADA Frontend Application
 *
 * This script handles the dynamic updates for the SCADA dashboard.
 * It periodically fetches tag data from the backend API and updates the DOM
 * to display the latest values.
 */

document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    // --- Configuration ---
    const API_ENDPOINT = '/api/tags';
    const POLL_INTERVAL_MS = 2000; // Poll every 2 seconds

    // --- DOM Elements ---
    const tagsContainer = document.getElementById('tags-container');
    const statusIndicator = document.getElementById('status-indicator');

    if (!tagsContainer) {
        console.error('Error: The element with ID "tags-container" was not found in the DOM.');
        return;
    }
    if (!statusIndicator) {
        console.warn('Warning: The element with ID "status-indicator" was not found. Status updates will not be displayed.');
    }

    /**
     * Updates the status indicator text and style.
     * @param {string} text - The message to display.
     * @param {boolean} isError - If true, applies an error style.
     */
    const updateStatus = (text, isError = false) => {
        if (statusIndicator) {
            statusIndicator.textContent = text;
            statusIndicator.className = isError ? 'status-error' : 'status-ok';
        }
    };

    /**
     * Fetches the latest tag data from the API.
     * @returns {Promise<Array<Object>>} A promise that resolves to an array of tag objects.
     */
    const fetchTags = async () => {
        const response = await fetch(API_ENDPOINT);

        if (!response.ok) {
            throw new Error(`Network response was not ok. Status: ${response.status}`);
        }

        return await response.json();
    };

    /**
     * Formats a date string into a more readable local time format.
     * @param {string} dateString - The ISO 8601 date string from the server.
     * @returns {string} A formatted date and time string.
     */
    const formatTimestamp = (dateString) => {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            return date.toLocaleString();
        } catch (e) {
            return 'Invalid Date';
        }
    };

    /**
     * Renders the tag data into a table in the DOM.
     * @param {Array<Object>} tags - An array of tag objects from the API.
     */
    const renderTags = (tags) => {
        // If there's no data, display a message and return.
        if (!tags || tags.length === 0) {
            tagsContainer.innerHTML = '<p class="no-tags-message">No tags configured or available from the server.</p>';
            return;
        }

        // Create the table structure using template literals.
        const tableRows = tags.map(tag => {
            // Format value for display, rounding numbers to 2 decimal places.
            const value = (tag.value !== null && typeof tag.value === 'number')
                ? tag.value.toFixed(2)
                : String(tag.value);

            // Apply a CSS class based on the status code for styling.
            const statusClass = (tag.status_code && tag.status_code.toLowerCase() === 'good')
                ? 'status-good'
                : 'status-bad';

            return `
                <tr>
                    <td>${tag.name || 'N/A'}</td>
                    <td>${tag.node_id || 'N/A'}</td>
                    <td class="tag-value">${value}</td>
                    <td class="${statusClass}">${tag.status_code || 'Unknown'}</td>
                    <td>${formatTimestamp(tag.timestamp)}</td>
                </tr>
            `;
        }).join('');

        tagsContainer.innerHTML = `
            <table class="tags-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Node ID</th>
                        <th>Value</th>
                        <th>Status</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        `;
    };

    /**
     * Main polling function. Fetches data and updates the UI.
     * Handles errors gracefully to prevent the polling from stopping.
     */
    const pollData = async () => {
        try {
            const tags = await fetchTags();
            renderTags(tags);
            const lastUpdated = new Date().toLocaleTimeString();
            updateStatus(`Connected. Last updated: ${lastUpdated}`, false);
        } catch (error) {
            console.error('Failed to fetch or render tag data:', error);
            updateStatus(`Connection Error. Retrying...`, true);
        }
    };

    // --- Initialization ---

    // Perform an initial fetch immediately on load to populate the UI.
    updateStatus('Connecting to server...', false);
    pollData();

    // Set up the polling interval to continuously update the data.
    setInterval(pollData, POLL_INTERVAL_MS);
});