// VectorBid Modern UI JavaScript
class VectorBid {
    constructor() {
        this.init();
    }

    init() {
        this.initDragDrop();
        this.initNotifications();
        this.initFormValidation();
        this.initTooltips();
        this.initModals();
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

        notification.innerHTML = `
            <div class="vb-alert vb-alert-${type}">
                <i class="fas fa-${icon}"></i>
                <div>
                    <strong>${this.getTitle(type)}</strong>
                    <p>${message}</p>
                </div>
            </div>
        `;

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
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.vectorbid = new VectorBid();
});
