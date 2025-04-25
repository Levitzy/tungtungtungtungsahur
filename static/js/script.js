/**
 * FB Authentication System - Main Script
 * Handles login functionality and UI interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const loginForm = document.getElementById('login-form');
    const loginStatus = document.getElementById('login-status');
    const loginProgress = document.getElementById('login-progress');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const togglePasswordButton = document.querySelector('.toggle-password');
    
    // Progress bars
    const progress1 = document.getElementById('progress-1');
    const progress2 = document.getElementById('progress-2');
    const progress3 = document.getElementById('progress-3');
    
    // Check if there's a session already
    checkExistingSession();
    
    // Add event listeners
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    if (togglePasswordButton) {
        togglePasswordButton.addEventListener('click', togglePasswordVisibility);
    }
    
    /**
     * Check if user has an existing session
     */
    function checkExistingSession() {
        const sessionId = localStorage.getItem('fb_auth_session_id');
        const email = localStorage.getItem('fb_auth_email');
        
        if (sessionId && email) {
            // Verify if the session is still valid
            fetch(`/api/sessions/${sessionId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Session is valid, redirect to dashboard
                        window.location.href = '/dashboard';
                    } else {
                        // Session is invalid, clear local storage
                        localStorage.removeItem('fb_auth_session_id');
                        localStorage.removeItem('fb_auth_email');
                    }
                })
                .catch(error => {
                    console.error('Error checking session:', error);
                    // Clear local storage on error
                    localStorage.removeItem('fb_auth_session_id');
                    localStorage.removeItem('fb_auth_email');
                });
        }
    }
    
    /**
     * Handle login form submission
     * @param {Event} event - Form submit event
     */
    function handleLogin(event) {
        event.preventDefault();
        
        // Get form data
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        
        // Basic validation
        if (!email || !password) {
            showStatus('error', 'Please enter both email and password');
            return;
        }
        
        // Email validation
        if (!isValidEmail(email)) {
            showStatus('error', 'Please enter a valid email address');
            return;
        }
        
        // Show loading state
        setLoading(true);
        showProgress();
        
        // Start simulating progress
        simulateProgress();
        
        // Make API request
        fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Login successful
                completeProgress();
                showStatus('success', 'Login successful! Redirecting to dashboard...');
                
                // Save session data
                localStorage.setItem('fb_auth_session_id', data.session_id);
                localStorage.setItem('fb_auth_email', email);
                
                // Redirect to dashboard after a short delay
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1500);
            } else {
                // Login failed
                resetProgress();
                setLoading(false);
                showStatus('error', data.message || 'Login failed. Please check your credentials.');
            }
        })
        .catch(error => {
            console.error('Login error:', error);
            resetProgress();
            setLoading(false);
            showStatus('error', 'A network error occurred. Please try again.');
        });
    }
    
    /**
     * Toggle password visibility
     */
    function togglePasswordVisibility() {
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            togglePasswordButton.classList.remove('fa-eye');
            togglePasswordButton.classList.add('fa-eye-slash');
        } else {
            passwordInput.type = 'password';
            togglePasswordButton.classList.remove('fa-eye-slash');
            togglePasswordButton.classList.add('fa-eye');
        }
    }
    
    /**
     * Display status message
     * @param {string} type - Status type (success, error, warning, info)
     * @param {string} message - Status message
     */
    function showStatus(type, message) {
        if (!loginStatus) return;
        
        // Create status content
        let icon = '';
        
        switch (type) {
            case 'success':
                icon = '<i class="fas fa-check-circle text-green-500 mr-2"></i>';
                break;
            case 'error':
                icon = '<i class="fas fa-exclamation-circle text-red-500 mr-2"></i>';
                break;
            case 'warning':
                icon = '<i class="fas fa-exclamation-triangle text-yellow-500 mr-2"></i>';
                break;
            case 'info':
                icon = '<i class="fas fa-info-circle text-blue-500 mr-2"></i>';
                break;
        }
        
        // Set status content
        loginStatus.innerHTML = `
            <div class="status-${type} p-3 rounded">
                <div class="flex items-center">
                    ${icon}
                    <span>${message}</span>
                </div>
            </div>
        `;
        
        // Show status
        loginStatus.classList.remove('hidden');
        loginStatus.classList.add('fade-in');
    }
    
    /**
     * Set loading state
     * @param {boolean} isLoading - Whether loading is active
     */
    function setLoading(isLoading) {
        const loginText = document.querySelector('.login-text');
        const loginSpinner = document.querySelector('.login-spinner');
        
        if (isLoading) {
            loginText.classList.add('hidden');
            loginSpinner.classList.remove('hidden');
            emailInput.disabled = true;
            passwordInput.disabled = true;
        } else {
            loginText.classList.remove('hidden');
            loginSpinner.classList.add('hidden');
            emailInput.disabled = false;
            passwordInput.disabled = false;
        }
    }
    
    /**
     * Show progress indicators
     */
    function showProgress() {
        if (!loginProgress) return;
        
        loginProgress.classList.remove('hidden');
        loginProgress.classList.add('slide-up');
    }
    
    /**
     * Simulate progress during authentication
     */
    function simulateProgress() {
        // Reset progress
        progress1.style.width = '0%';
        progress2.style.width = '0%';
        progress3.style.width = '0%';
        
        // Simulate environment preparation (fast)
        let width1 = 0;
        const interval1 = setInterval(() => {
            if (width1 >= 100) {
                clearInterval(interval1);
                
                // Start authentication process progress
                simulateStep2();
            } else {
                width1 += 4;
                progress1.style.width = width1 + '%';
            }
        }, 50);
        
        /**
         * Simulate authentication process (slower)
         */
        function simulateStep2() {
            let width2 = 0;
            const interval2 = setInterval(() => {
                if (width2 >= 60) {
                    clearInterval(interval2);
                    // Don't complete this step yet, wait for actual response
                } else {
                    width2 += 1;
                    progress2.style.width = width2 + '%';
                }
            }, 100);
        }
    }
    
    /**
     * Complete progress animation on success
     */
    function completeProgress() {
        // Complete auth process
        let width2 = parseInt(progress2.style.width) || 60;
        const interval2 = setInterval(() => {
            if (width2 >= 100) {
                clearInterval(interval2);
                
                // Start session creation progress
                let width3 = 0;
                const interval3 = setInterval(() => {
                    if (width3 >= 100) {
                        clearInterval(interval3);
                    } else {
                        width3 += 5;
                        progress3.style.width = width3 + '%';
                    }
                }, 30);
                
            } else {
                width2 += 4;
                progress2.style.width = width2 + '%';
            }
        }, 30);
    }
    
    /**
     * Reset progress on failure
     */
    function resetProgress() {
        if (!loginProgress) return;
        
        setTimeout(() => {
            loginProgress.classList.add('hidden');
        }, 500);
    }
    
    /**
     * Validate email format
     * @param {string} email - Email to validate
     * @returns {boolean} - Whether email is valid
     */
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
});