// VectorBid Modern UI JavaScript
class VectorBid {
    constructor() {
        this.init();
    }

    init() {
        this.initDragDrop();
        this.initFormValidation();
        this.initNavigation();
    }

    // Drag and Drop functionality
    initDragDrop() {
        const trips = document.querySelectorAll('.vb-trip');
        let draggedElement = null;

        trips.forEach(trip => {
            trip.addEventListener('dragstart', (e) => {
                draggedElement = e.target;
                e.target.classList.add('dragging');
            });

            trip.addEventListener('dragend', (e) => {
                e.target.classList.remove('dragging');
            });
        });
    }

    // Notification System
    showNotification(type, message, duration = 5000) {
        const notification = document.createElement('div');
        notification.className = 'vb-notification vb-slide-in-right';

        const icon = this.getIcon(type);

        // Create alert container
        const alertDiv = document.createElement('div');
        alertDiv.className = `vb-alert vb-alert-${type}`;

        // Create and append icon
        const iconElement = document.createElement('i');
        iconElement.className = `fas fa-${icon}`;
        alertDiv.appendChild(iconElement);

        // Create content div
        const contentDiv = document.createElement('div');

        // Create and append title
        const titleElement = document.createElement('strong');
        titleElement.textContent = this.getTitle(type);
        contentDiv.appendChild(titleElement);

        // Create and append message
        const messageElement = document.createElement('p');
        messageElement.textContent = message;
        contentDiv.appendChild(messageElement);

        alertDiv.appendChild(contentDiv);
        notification.appendChild(alertDiv);

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, duration);
    }

    getIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    getTitle(type) {
        const titles = {
            success: 'Success!',
            error: 'Error',
            warning: 'Warning',
            info: 'Info'
        };
        return titles[type] || 'Notification';
    }

    // Form validation
    initFormValidation() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const textarea = form.querySelector('textarea[name="preferences"]');
                if (textarea && textarea.value.trim() === '') {
                    e.preventDefault();
                    this.showNotification('warning', 'Please enter your preferences before generating PBS commands.');
                }
            });
        });
    }

    // Navigation functionality
    initNavigation() {
        const navToggle = document.getElementById('navToggle');
        const navLinks = document.getElementById('navLinks');
        
        if (navToggle && navLinks) {
            navToggle.addEventListener('click', () => {
                navLinks.classList.toggle('show');
            });
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.vectorbid = new VectorBid();
});
