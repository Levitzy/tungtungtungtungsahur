/**
 * FB Authentication System - Dashboard Script
 * Handles dashboard functionality and data display
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    const sessionId = localStorage.getItem('fb_auth_session_id');
    const email = localStorage.getItem('fb_auth_email');
    
    if (!sessionId || !email) {
        // Not logged in, redirect to login page
        window.location.href = '/';
        return;
    }
    
    // DOM elements
    const userInitial = document.getElementById('user-initial');
    const sessionEmail = document.getElementById('session-email');
    const sessionIdElement = document.getElementById('session-id');
    const cookiesCount = document.getElementById('cookies-count');
    const sessionAge = document.getElementById('session-age');
    const logoutButton = document.getElementById('logout-button');
    const sessionsTableBody = document.getElementById('sessions-table-body');
    const cookiesTableBody = document.getElementById('cookies-table-body');
    
    // Initialize charts
    initializeCharts();
    
    // Load session data
    loadSessionData();
    
    // Load sessions list
    loadSessions();
    
    // Set up logout button
    if (logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
    }
    
    /**
     * Load the current session data
     */
    function loadSessionData() {
        fetch(`/api/sessions/${sessionId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update UI with session info
                    updateSessionInfo(data.session);
                    
                    // Load cookies for this session
                    loadCookies(sessionId);
                } else {
                    // Session not found or expired
                    handleInvalidSession();
                }
            })
            .catch(error => {
                console.error('Error loading session data:', error);
                showError('Failed to load session data. Please try refreshing the page.');
            });
    }
    
    /**
     * Update session information in the UI
     * @param {Object} session - Session data
     */
    function updateSessionInfo(session) {
        // Set user initial
        if (userInitial && session.email) {
            userInitial.textContent = session.email.charAt(0).toUpperCase();
        }
        
        // Set email
        if (sessionEmail) {
            sessionEmail.textContent = session.email;
        }
        
        // Set session ID
        if (sessionIdElement) {
            sessionIdElement.textContent = `Session ID: ${session.session_id}`;
        }
        
        // Set cookies count
        if (cookiesCount && session.cookies) {
            cookiesCount.textContent = session.cookies.length;
        }
        
        // Calculate and set session age
        if (sessionAge && session.created_at) {
            const createdDate = new Date(session.created_at);
            const now = new Date();
            const ageMs = now - createdDate;
            
            if (ageMs < 60000) { // Less than a minute
                sessionAge.textContent = 'Just created';
            } else if (ageMs < 3600000) { // Less than an hour
                const minutes = Math.floor(ageMs / 60000);
                sessionAge.textContent = `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} old`;
            } else if (ageMs < 86400000) { // Less than a day
                const hours = Math.floor(ageMs / 3600000);
                sessionAge.textContent = `${hours} ${hours === 1 ? 'hour' : 'hours'} old`;
            } else { // More than a day
                const days = Math.floor(ageMs / 86400000);
                sessionAge.textContent = `${days} ${days === 1 ? 'day' : 'days'} old`;
            }
        }
    }
    
    /**
     * Handle invalid or expired session
     */
    function handleInvalidSession() {
        Swal.fire({
            title: 'Session Expired',
            text: 'Your session has expired or is invalid. Please log in again.',
            icon: 'warning',
            confirmButtonText: 'Go to Login',
            confirmButtonColor: '#4f46e5'
        }).then(() => {
            // Clear local storage
            localStorage.removeItem('fb_auth_session_id');
            localStorage.removeItem('fb_auth_email');
            
            // Redirect to login page
            window.location.href = '/';
        });
    }
    
    /**
     * Load all sessions
     */
    function loadSessions() {
        fetch('/api/sessions')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.sessions) {
                    // Update sessions table
                    updateSessionsTable(data.sessions);
                }
            })
            .catch(error => {
                console.error('Error loading sessions:', error);
                
                if (sessionsTableBody) {
                    sessionsTableBody.innerHTML = `
                        <tr>
                            <td colspan="6" class="px-6 py-4 text-center text-red-500">
                                <i class="fas fa-exclamation-circle mr-2"></i> 
                                Failed to load sessions
                            </td>
                        </tr>
                    `;
                }
            });
    }
    
    /**
     * Update the sessions table
     * @param {Array} sessions - List of session objects
     */
    function updateSessionsTable(sessions) {
        if (!sessionsTableBody) return;
        
        if (sessions.length === 0) {
            sessionsTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="px-6 py-4 text-center text-gray-500">
                        No active sessions found
                    </td>
                </tr>
            `;
            return;
        }
        
        // Sort sessions by last used (most recent first)
        sessions.sort((a, b) => {
            return new Date(b.last_used) - new Date(a.last_used);
        });
        
        // Generate table rows
        const rows = sessions.map(session => {
            const isCurrentSession = session.session_id === sessionId;
            const createdDate = formatDate(session.created_at);
            const lastUsedDate = formatDate(session.last_used);
            
            return `
                <tr class="${isCurrentSession ? 'bg-indigo-50' : ''}">
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="flex items-center">
                            ${isCurrentSession ? '<span class="inline-block w-2 h-2 mr-2 bg-green-500 rounded-full"></span>' : ''}
                            <span class="text-sm font-medium ${isCurrentSession ? 'text-indigo-600' : 'text-gray-900'}">${session.session_id}</span>
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900">${session.email}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-500">${createdDate}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-500">${lastUsedDate}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${isCurrentSession ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}">
                            ${isCurrentSession ? 'Current' : 'Active'}
                        </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div class="flex space-x-2">
                            <button class="text-indigo-600 hover:text-indigo-900" data-session-id="${session.session_id}">
                                <i class="fas fa-info-circle"></i>
                            </button>
                            ${!isCurrentSession ? `
                            <button class="text-red-600 hover:text-red-900 delete-session" data-session-id="${session.session_id}">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                            ` : ''}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
        // Update table
        sessionsTableBody.innerHTML = rows;
        
        // Add event listeners to delete buttons
        document.querySelectorAll('.delete-session').forEach(button => {
            button.addEventListener('click', function() {
                const sessionToDelete = this.getAttribute('data-session-id');
                deleteSession(sessionToDelete);
            });
        });
    }
    
    /**
     * Load cookies for a session
     * @param {string} sessionId - Session ID
     */
    function loadCookies(sessionId) {
        fetch(`/api/cookies/${sessionId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.cookies) {
                    // Update cookies table
                    updateCookiesTable(data.cookies);
                }
            })
            .catch(error => {
                console.error('Error loading cookies:', error);
                
                if (cookiesTableBody) {
                    cookiesTableBody.innerHTML = `
                        <tr>
                            <td colspan="5" class="px-6 py-4 text-center text-red-500">
                                <i class="fas fa-exclamation-circle mr-2"></i> 
                                Failed to load cookies
                            </td>
                        </tr>
                    `;
                }
            });
    }
    
    /**
     * Update cookies table
     * @param {Array} cookies - List of cookie objects
     */
    function updateCookiesTable(cookies) {
        if (!cookiesTableBody) return;
        
        if (cookies.length === 0) {
            cookiesTableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="px-6 py-4 text-center text-gray-500">
                        No cookies found for this session
                    </td>
                </tr>
            `;
            return;
        }
        
        // Define essential cookies
        const essentialCookies = ['c_user', 'xs', 'fr', 'datr'];
        
        // Generate table rows
        const rows = cookies.map(cookie => {
            const isEssential = essentialCookies.includes(cookie.name);
            const cookieType = getCookieType(cookie.name);
            
            // Truncate long cookie values
            let cookieValue = cookie.value;
            if (cookieValue && cookieValue.length > 30) {
                cookieValue = cookieValue.substring(0, 30) + '...';
            }
            
            return `
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="flex items-center">
                            <span class="text-sm font-medium ${isEssential ? 'text-indigo-600 font-semibold' : 'text-gray-900'}">${cookie.name}</span>
                            ${isEssential ? '<span class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">Essential</span>' : ''}
                        </div>
                    </td>
                    <td class="px-6 py-4">
                        <div class="text-sm text-gray-500 max-w-xs truncate" title="${cookie.value}">${cookieValue}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-500">${cookie.domain || '.facebook.com'}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-500">${cookie.path || '/'}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCookieTypeColor(cookieType)}">
                            ${cookieType}
                        </span>
                    </td>
                </tr>
            `;
        }).join('');
        
        // Update table
        cookiesTableBody.innerHTML = rows;
    }
    
    /**
     * Get the cookie type based on its name
     * @param {string} name - Cookie name
     * @returns {string} - Cookie type
     */
    function getCookieType(name) {
        const authCookies = ['c_user', 'xs', 'sb', 'datr'];
        const functionalCookies = ['locale', 'wd', 'dpr', 'presence'];
        const trackerCookies = ['fr', 'm_pixel_ratio', '_fbp'];
        
        if (authCookies.includes(name)) {
            return 'Authentication';
        } else if (functionalCookies.includes(name)) {
            return 'Functional';
        } else if (trackerCookies.includes(name)) {
            return 'Tracking';
        } else {
            return 'Other';
        }
    }
    
    /**
     * Get color class for cookie type
     * @param {string} type - Cookie type
     * @returns {string} - Tailwind color classes
     */
    function getCookieTypeColor(type) {
        switch (type) {
            case 'Authentication':
                return 'bg-indigo-100 text-indigo-800';
            case 'Functional':
                return 'bg-green-100 text-green-800';
            case 'Tracking':
                return 'bg-yellow-100 text-yellow-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }
    
    /**
     * Format a date string for display
     * @param {string} dateString - ISO date string
     * @returns {string} - Formatted date
     */
    function formatDate(dateString) {
        if (!dateString) return 'Unknown';
        
        try {
            // Use moment.js for better date formatting
            return moment(dateString).format('MMM D, YYYY h:mm A');
        } catch (error) {
            // Fallback to basic formatting
            const date = new Date(dateString);
            return date.toLocaleString();
        }
    }
    
    /**
     * Delete a session
     * @param {string} sessionToDelete - Session ID to delete
     */
    function deleteSession(sessionToDelete) {
        Swal.fire({
            title: 'Delete Session',
            text: 'Are you sure you want to delete this session? This cannot be undone.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Delete',
            confirmButtonColor: '#ef4444',
            cancelButtonText: 'Cancel',
            cancelButtonColor: '#6b7280'
        }).then((result) => {
            if (result.isConfirmed) {
                fetch(`/api/sessions/${sessionToDelete}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Reload sessions list
                        loadSessions();
                        
                        Swal.fire({
                            title: 'Session Deleted',
                            text: 'The session has been successfully deleted.',
                            icon: 'success',
                            confirmButtonColor: '#4f46e5'
                        });
                    } else {
                        showError('Failed to delete session. Please try again.');
                    }
                })
                .catch(error => {
                    console.error('Error deleting session:', error);
                    showError('A network error occurred while deleting the session.');
                });
            }
        });
    }
    
    /**
     * Initialize dashboard charts
     */
    function initializeCharts() {
        // Session Health Chart (donut chart)
        const sessionHealthCtx = document.getElementById('sessionHealthChart');
        if (sessionHealthCtx) {
            new Chart(sessionHealthCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Authentication', 'Functional', 'Tracking', 'Other'],
                    datasets: [{
                        data: [4, 3, 2, 1],
                        backgroundColor: [
                            'rgba(79, 70, 229, 0.8)', // Indigo
                            'rgba(16, 185, 129, 0.8)', // Green
                            'rgba(245, 158, 11, 0.8)', // Yellow
                            'rgba(156, 163, 175, 0.8)'  // Gray
                        ],
                        borderWidth: 1,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    return `${label}: ${value} cookies`;
                                }
                            }
                        }
                    },
                    cutout: '70%'
                }
            });
        }
        
        // Activity Timeline Chart (line chart)
        const activityChartCtx = document.getElementById('activityChart');
        if (activityChartCtx) {
            // Generate some sample data
            const dates = [];
            const data = [];
            
            const now = new Date();
            for (let i = 6; i >= 0; i--) {
                const date = new Date(now);
                date.setDate(date.getDate() - i);
                dates.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
                
                // Random value from 60-100 for active session status
                data.push(Math.floor(Math.random() * 40) + 60);
            }
            
            new Chart(activityChartCtx, {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: [{
                        label: 'Session Health',
                        data: data,
                        borderColor: 'rgba(79, 70, 229, 1)',
                        backgroundColor: 'rgba(79, 70, 229, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: 'rgba(79, 70, 229, 1)',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = context.parsed.y || 0;
                                    return `Health: ${value}%`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            min: 50,
                            max: 100,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    }
                }
            });
        }
    }
    
    /**
     * Handle logout button click
     */
    function handleLogout() {
        Swal.fire({
            title: 'Logout',
            text: 'Are you sure you want to log out?',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Logout',
            confirmButtonColor: '#4f46e5',
            cancelButtonText: 'Cancel',
            cancelButtonColor: '#6b7280'
        }).then((result) => {
            if (result.isConfirmed) {
                // Clear session data
                localStorage.removeItem('fb_auth_session_id');
                localStorage.removeItem('fb_auth_email');
                
                // Redirect to login page
                window.location.href = '/';
            }
        });
    }
    
    /**
     * Show an error message using SweetAlert
     * @param {string} message - Error message
     */
    function showError(message) {
        Swal.fire({
            title: 'Error',
            text: message,
            icon: 'error',
            confirmButtonColor: '#4f46e5'
        });
    }
});