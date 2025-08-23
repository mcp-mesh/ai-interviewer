// Careers Wireframe JavaScript - Simulating State Management

// Simulated user states
let currentUser = {
    isLoggedIn: false,
    hasResume: false,
    hasInterviewPending: false,
    name: 'Dhyan Raj',
    email: 'dhyan.raj@gmail.com',
    pendingInterviews: 0
};

// Initialize page state on load
document.addEventListener('DOMContentLoaded', function() {
    // Check URL parameters for demo states
    const urlParams = new URLSearchParams(window.location.search);
    const demoState = urlParams.get('state');
    
    if (demoState) {
        switch(demoState) {
            case 'logged-in':
                currentUser.isLoggedIn = true;
                currentUser.hasResume = false;
                break;
            case 'has-resume':
                currentUser.isLoggedIn = true;
                currentUser.hasResume = true;
                break;
            case 'interview-ready':
                currentUser.isLoggedIn = true;
                currentUser.hasResume = true;
                currentUser.hasInterviewPending = true;
                break;
        }
    }
    
    updateUIState();
});

// Update UI based on current user state
function updateUIState() {
    // Toggle navigation
    const authActions = document.getElementById('auth-actions');
    const userActions = document.getElementById('user-actions');
    
    if (currentUser.isLoggedIn) {
        authActions?.classList.add('hidden');
        userActions?.classList.remove('hidden');
    } else {
        authActions?.classList.remove('hidden');
        userActions?.classList.add('hidden');
    }
    
    // Toggle hero actions
    const guestActions = document.getElementById('guest-actions');
    const noResumeActions = document.getElementById('no-resume-actions');
    const hasResumeActions = document.getElementById('has-resume-actions');
    const interviewAvailable = document.getElementById('interview-available');
    
    // Hide all first
    [guestActions, noResumeActions, hasResumeActions, interviewAvailable].forEach(el => {
        el?.classList.add('hidden');
    });
    
    // Show appropriate action based on state
    if (!currentUser.isLoggedIn) {
        guestActions?.classList.remove('hidden');
    } else if (currentUser.hasInterviewPending) {
        interviewAvailable?.classList.remove('hidden');
    } else if (currentUser.hasResume) {
        hasResumeActions?.classList.remove('hidden');
    } else {
        noResumeActions?.classList.remove('hidden');
    }
}

// Auth functions
function showLogin() {
    window.location.href = 'index-loggedin.html';
}

function hideLogin() {
    const modal = document.getElementById('login-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.style.display = 'none';
    }
}

function loginWith(provider) {
    console.log(`Logging in with ${provider}`);
    
    // Simulate login
    currentUser.isLoggedIn = true;
    hideLogin();
    updateUIState();
    
    // Show success message
    showNotification(`Successfully signed in with ${provider}!`, 'success');
}

function logout() {
    currentUser.isLoggedIn = false;
    currentUser.hasResume = false;
    currentUser.hasInterviewPending = false;
    updateUIState();
    showNotification('Successfully signed out', 'info');
}

// Demo state functions for wireframe testing
function setDemoState(state) {
    const url = new URL(window.location);
    url.searchParams.set('state', state);
    window.location.href = url.toString();
}

function toggleResumeState() {
    currentUser.hasResume = !currentUser.hasResume;
    updateUIState();
}

function toggleInterviewState() {
    currentUser.hasInterviewPending = !currentUser.hasInterviewPending;
    updateUIState();
}

// Notification system
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 2rem;
        right: 2rem;
        z-index: 1000;
        min-width: 300px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Navigation helpers
function navigateTo(path) {
    // For wireframes, we'll just update the URL without actually navigating
    console.log(`Navigating to: ${path}`);
    showNotification(`Navigation: ${path}`, 'info');
}

// Form helpers for application flow
function simulateResumeUpload() {
    showNotification('Resume uploaded successfully!', 'success');
    currentUser.hasResume = true;
    updateUIState();
}

function simulateJobApplication() {
    showNotification('Application submitted! AI analysis in progress...', 'success');
    // Simulate interview eligibility after application
    setTimeout(() => {
        currentUser.hasInterviewPending = true;
        updateUIState();
        showNotification('You are eligible for an AI interview!', 'success');
    }, 2000);
}

// Search and filter functions
function performSearch(query) {
    console.log(`Searching for: ${query}`);
    showNotification(`Searching for "${query}"...`, 'info');
}

function applyFilters(filters) {
    console.log('Applying filters:', filters);
    showNotification('Filters applied', 'info');
}

// Keyboard shortcuts for demo
document.addEventListener('keydown', function(e) {
    // Alt + number keys for quick demo state changes
    if (e.altKey) {
        switch(e.key) {
            case '1':
                e.preventDefault();
                setDemoState('guest');
                break;
            case '2':
                e.preventDefault();
                setDemoState('logged-in');
                break;
            case '3':
                e.preventDefault();
                setDemoState('has-resume');
                break;
            case '4':
                e.preventDefault();
                setDemoState('interview-ready');
                break;
        }
    }
});

// Add demo controls for wireframe testing
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // Add floating demo controls
    const demoControls = document.createElement('div');
    demoControls.innerHTML = `
        <div style="position: fixed; bottom: 1rem; left: 1rem; background: white; padding: 1rem; border-radius: 0.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); z-index: 1000; font-size: 0.875rem;">
            <h4 style="margin-bottom: 0.5rem; font-weight: 600;">Demo Controls</h4>
            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                <button onclick="setDemoState('')" class="btn btn-secondary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">Guest User</button>
                <button onclick="setDemoState('logged-in')" class="btn btn-secondary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">Logged In</button>
                <button onclick="setDemoState('has-resume')" class="btn btn-secondary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">Has Resume</button>
                <button onclick="setDemoState('interview-ready')" class="btn btn-secondary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">Interview Ready</button>
            </div>
            <p style="margin-top: 0.5rem; color: #6b7280; font-size: 0.75rem;">Alt+1-4 for quick switch</p>
        </div>
    `;
    document.body.appendChild(demoControls);
}