if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/sw.js').then(function(registration) {
            // Registration was successful
            console.log('ServiceWorker registration successful with scope: ', registration.scope);
        }, function(err) {
            // registration failed :(
            console.log('ServiceWorker registration failed: ', err);
        });
    });
}

// Socket.IO Client-side Logic
document.addEventListener('DOMContentLoaded', function() {
    const socket = io(); // Connect to the Socket.IO server

    // Function to display a Bootstrap Toast notification
    function showToast(message, title = 'Notification', category = 'info') {
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            console.error('Toast container not found!');
            return;
        }

        const toastId = `toast-${Date.now()}`;
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${category} border-0" role="alert" aria-live="assertive" aria-atomic="true" id="${toastId}">
                <div class="d-flex">
                    <div class="toast-body">
                        <strong>${title}:</strong> ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();

        // Remove toast element from DOM after it's hidden
        toastElement.addEventListener('hidden.bs.toast', function () {
            toastElement.remove();
        });
    }

    // Listen for 'update_notification_count' event
    socket.on('update_notification_count', function(data) {
        const badge = document.getElementById('unread-notifications-badge');
        if (badge) {
            if (data.count > 0) {
                badge.textContent = data.count;
                badge.classList.remove('d-none');
            } else {
                badge.classList.add('d-none');
            }
        }
    });

    // Listen for 'new_message' event
    socket.on('new_message', function(data) {
        // Only show toast if the message is not from the current user (to avoid self-notifications)
        // You might need to pass current_user.id from Flask to JS for this check
        // For now, assuming 'from_self' flag is reliable
        if (!data.from_self) {
            showToast(`New message from ${data.sender_username || 'someone'}`, 'New Message', 'primary');
        }
    });

    // Listen for 'new_review' event
    socket.on('new_review', function(data) {
        showToast(`You received a new review with rating ${data.rating} stars!`, 'New Review', 'success');
    });

    // Listen for 'saved_search_match' event
    socket.on('saved_search_match', function(data) {
        showToast(`New listing matching your saved search: ${data.listing_title || 'New Item'}`, 'Saved Search Match', 'info');
    });

    // You can add more event listeners for other notification types (e.g., swap requests, offers)
    // socket.on('new_swap_request', function(data) { ... });
});