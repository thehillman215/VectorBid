<!-- ============================================
   MAIN.JS - Core JavaScript Functionality
   Place in: src/ui/static/js/main.js
   ============================================ -->
<script>
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
              e.dataTransfer.effectAllowed = 'move';
              e.dataTransfer.setData('text/html', e.target.innerHTML);
          });

          trip.addEventListener('dragend', (e) => {
              e.target.classList.remove('dragging');
          });

          trip.addEventListener('dragover', (e) => {
              if (e.preventDefault) {
                  e.preventDefault();
              }
              e.dataTransfer.dropEffect = 'move';

              const afterElement = this.getDragAfterElement(e.currentTarget.parentNode, e.clientY);
              const dragging = document.querySelector('.dragging');

              if (afterElement == null) {
                  e.currentTarget.parentNode.appendChild(dragging);
              } else {
                  e.currentTarget.parentNode.insertBefore(dragging, afterElement);
              }

              return false;
          });
      });
  }

  getDragAfterElement(container, y) {
      const draggableElements = [...container.querySelectorAll('.vb-trip:not(.dragging)')];

      return draggableElements.reduce((closest, child) => {
          const box = child.getBoundingClientRect();
          const offset = y - box.top - box.height / 2;

          if (offset < 0 && offset > closest.offset) {
              return { offset: offset, element: child };
          } else {
              return closest;
          }
      }, { offset: Number.NEGATIVE_INFINITY }).element;
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
              <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: inherit; cursor: pointer;">
                  <i class="fas fa-times"></i>
              </button>
          </div>
      `;

      document.body.appendChild(notification);

      setTimeout(() => {
          notification.classList.add('fade-out');
          setTimeout(() => notification.remove(), 300);
      }, duration);
  }

  getIcon(type) {
      const icons = {
          success: 'check-circle',
          error: 'exclamation-circle',
          danger: 'exclamation-circle',
          warning: 'exclamation-triangle',
          info: 'info-circle'
      };
      return icons[type] || 'info-circle';
  }

  getTitle(type) {
      const titles = {
          success: 'Success!',
          error: 'Error',
          danger: 'Error',
          warning: 'Warning',
          info: 'Info'
      };
      return titles[type] || 'Notification';
  }

  // Form Validation
  initFormValidation() {
      const forms = document.querySelectorAll('form[data-validate]');

      forms.forEach(form => {
          form.addEventListener('submit', (e) => {
              if (!this.validateForm(form)) {
                  e.preventDefault();
                  e.stopPropagation();
              }
          });

          // Real-time validation
          const inputs = form.querySelectorAll('.vb-input, .vb-select, .vb-textarea');
          inputs.forEach(input => {
              input.addEventListener('blur', () => {
                  this.validateField(input);
              });
          });
      });
  }

  validateForm(form) {
      let isValid = true;
      const inputs = form.querySelectorAll('[required]');

      inputs.forEach(input => {
          if (!this.validateField(input)) {
              isValid = false;
          }
      });

      return isValid;
  }

  validateField(field) {
      const value = field.value.trim();
      const isRequired = field.hasAttribute('required');

      // Remove previous validation states
      field.classList.remove('is-invalid', 'is-valid');

      if (isRequired && !value) {
          field.classList.add('is-invalid');
          this.showFieldError(field, 'This field is required');
          return false;
      }

      // Email validation
      if (field.type === 'email' && value) {
          const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
          if (!emailRegex.test(value)) {
              field.classList.add('is-invalid');
              this.showFieldError(field, 'Please enter a valid email');
              return false;
          }
      }

      field.classList.add('is-valid');
      this.removeFieldError(field);
      return true;
  }

  showFieldError(field, message) {
      this.removeFieldError(field);

      const error = document.createElement('div');
      error.className = 'vb-form-error';
      error.textContent = message;

      field.parentNode.appendChild(error);
  }

  removeFieldError(field) {
      const error = field.parentNode.querySelector('.vb-form-error');
      if (error) {
          error.remove();
      }
  }

  // Tooltips
  initTooltips() {
      const elements = document.querySelectorAll('[data-tooltip]');

      elements.forEach(element => {
          element.addEventListener('mouseenter', (e) => {
              const text = e.target.getAttribute('data-tooltip');
              this.showTooltip(e.target, text);
          });

          element.addEventListener('mouseleave', () => {
              this.hideTooltip();
          });
      });
  }

  showTooltip(element, text) {
      this.hideTooltip();

      const tooltip = document.createElement('div');
      tooltip.className = 'vb-tooltip';
      tooltip.textContent = text;
      tooltip.style.cssText = `
          position: absolute;
          background: var(--vb-gray-900);
          color: white;
          padding: 0.5rem 0.75rem;
          border-radius: var(--vb-radius-md);
          font-size: var(--vb-font-size-sm);
          z-index: var(--vb-z-tooltip);
          pointer-events: none;
      `;

      document.body.appendChild(tooltip);

      const rect = element.getBoundingClientRect();
      tooltip.style.top = `${rect.top - tooltip.offsetHeight - 8}px`;
      tooltip.style.left = `${rect.left + (rect.width - tooltip.offsetWidth) / 2}px`;
  }

  hideTooltip() {
      const tooltip = document.querySelector('.vb-tooltip');
      if (tooltip) {
          tooltip.remove();
      }
  }

  // Modals
  initModals() {
      const triggers = document.querySelectorAll('[data-modal]');

      triggers.forEach(trigger => {
          trigger.addEventListener('click', (e) => {
              e.preventDefault();
              const modalId = e.currentTarget.getAttribute('data-modal');
              this.openModal(modalId);
          });
      });

      // Close modals on backdrop click
      document.addEventListener('click', (e) => {
          if (e.target.classList.contains('vb-modal-backdrop')) {
              this.closeModal();
          }
      });

      // Close on ESC key
      document.addEventListener('keydown', (e) => {
          if (e.key === 'Escape') {
              this.closeModal();
          }
      });
  }

  openModal(modalId) {
      const modal = document.getElementById(modalId);
      if (modal) {
          modal.style.display = 'block';
          document.body.style.overflow = 'hidden';
      }
  }

  closeModal() {
      const modals = document.querySelectorAll('[id$="Modal"]');
      modals.forEach(modal => {
          modal.style.display = 'none';
      });
      document.body.style.overflow = '';
  }

  // API Helpers
  async fetchAPI(url, options = {}) {
      try {
          const response = await fetch(url, {
              headers: {
                  'Content-Type': 'application/json',
                  ...options.headers
              },
              ...options
          });

          if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
          }

          return await response.json();
      } catch (error) {
          console.error('API Error:', error);
          this.showNotification('error', 'An error occurred. Please try again.');
          throw error;
      }
  }

  // Utility Functions
  debounce(func, wait) {
      let timeout;
      return function executedFunction(...args) {
          const later = () => {
              clearTimeout(timeout);
              func(...args);
          };
          clearTimeout(timeout);
          timeout = setTimeout(later, wait);
      };
  }

  formatDate(date) {
      const options = { year: 'numeric', month: 'short', day: 'numeric' };
      return new Date(date).toLocaleDateString('en-US', options);
  }

  formatTime(date) {
      const options = { hour: '2-digit', minute: '2-digit' };
      return new Date(date).toLocaleTimeString('en-US', options);
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.vectorbid = new VectorBid();
});

// Export for use in other scripts
window.VectorBid = VectorBid;
</script>

<!-- ============================================
   COMPONENTS/TRIP_CARD.HTML - Reusable Trip Card
   Place in: src/ui/templates/components/trip_card.html
   ============================================ -->
<div class="vb-trip" draggable="true" data-trip-id="{{ trip.id }}">
  <div class="vb-trip-header">
      <div>
          <div class="vb-trip-id">Trip {{ trip.number }}</div>
          <div class="vb-trip-route">
              <i class="fas fa-plane text-muted"></i>
              {{ trip.route }}
          </div>
      </div>
      <span class="vb-trip-score vb-score-{{ trip.score_class }}">
          <i class="fas fa-{{ trip.score_icon }}"></i>
          {{ trip.match_percentage }}% match
      </span>
  </div>
  <div class="vb-trip-tags">
      <span class="vb-tag">
          <i class="fas fa-calendar-day"></i>
          {{ trip.duration }}-day trip
      </span>
      <span class="vb-tag">
          <i class="fas fa-clock"></i>
          {{ trip.block_hours }} block
      </span>
      <span class="vb-tag">
          <i class="fas fa-dollar-sign"></i>
          {{ trip.credit_hours }} credit
      </span>
      {% if trip.layovers %}
      <span class="vb-tag">
          <i class="fas fa-bed"></i>
          {{ trip.layovers }}
      </span>
      {% endif %}
      {% for tag in trip.additional_tags %}
      <span class="vb-tag">{{ tag }}</span>
      {% endfor %}
  </div>
</div>

<!-- ============================================
   COMPONENTS/METRIC_CARD.HTML - Reusable Metric
   Place in: src/ui/templates/components/metric_card.html
   ============================================ -->
<div class="vb-metric">
  <div class="vb-metric-value">{{ value }}</div>
  <div class="vb-metric-label">{{ label }}</div>
  {% if trend %}
  <div class="vb-metric-trend {{ trend.direction }}">
      <i class="fas fa-arrow-{{ trend.direction }}"></i>
      {{ trend.value }}% {{ trend.text }}
  </div>
  {% elif status %}
  <div class="vb-status {{ status.type }}">
      <span class="vb-status-dot"></span>
      {{ status.text }}
  </div>
  {% endif %}
</div>

<!-- ============================================
   COMPONENTS/NOTIFICATION.HTML - Toast Notification
   Place in: src/ui/templates/components/notification.html
   ============================================ -->
<div class="vb-notification vb-slide-in-right">
  <div class="vb-alert vb-alert-{{ type }}">
      <i class="fas fa-{{ icon }}"></i>
      <div>
          <strong>{{ title }}</strong>
          <p>{{ message }}</p>
      </div>
      <button class="vb-notification-close">
          <i class="fas fa-times"></i>
      </button>
  </div>
</div>

<!-- ============================================
   PREFERENCES.HTML - User Preferences Page
   Place in: src/ui/templates/preferences.html
   ============================================ -->
{% extends "base.html" %}

{% block title %}Preferences - VectorBid{% endblock %}

{% block content %}
<div class="vb-container">
  <div class="vb-mb-4">
      <h1>Flight Preferences</h1>
      <p class="vb-text-muted">Customize your bidding preferences</p>
  </div>

  <div class="row">
      <!-- Profile Settings -->
      <div class="col-md-4">
          <div class="vb-card">
              <div class="vb-card-header">
                  <h3 class="vb-card-title">Profile</h3>
              </div>

              <div class="vb-form-group">
                  <label class="vb-label">Airline</label>
                  <select class="vb-select">
                      <option>United Airlines</option>
                      <option>American Airlines</option>
                      <option>Delta Airlines</option>
                  </select>
              </div>

              <div class="vb-form-group">
                  <label class="vb-label">Base</label>
                  <select class="vb-select">
                      <option>ORD - Chicago</option>
                      <option>DEN - Denver</option>
                      <option>IAH - Houston</option>
                      <option>LAX - Los Angeles</option>
                  </select>
              </div>

              <div class="vb-form-group">
                  <label class="vb-label">Position</label>
                  <select class="vb-select">
                      <option>Captain</option>
                      <option>First Officer</option>
                  </select>
              </div>

              <div class="vb-form-group">
                  <label class="vb-label">Equipment</label>
                  <div class="vb-mt-2">
                      <label class="vb-checkbox">
                          <input type="checkbox" checked> B737
                      </label>
                      <label class="vb-checkbox">
                          <input type="checkbox"> B787
                      </label>
                      <label class="vb-checkbox">
                          <input type="checkbox"> B777
                      </label>
                  </div>
              </div>
          </div>
      </div>

      <!-- Trip Preferences -->
      <div class="col-md-8">
          <div class="vb-card">
              <div class="vb-card-header">
                  <h3 class="vb-card-title">Trip Preferences</h3>
              </div>

              <div class="row">
                  <div class="col-md-6">
                      <div class="vb-form-group">
                          <label class="vb-label">Preferred Trip Length</label>
                          <select class="vb-select">
                              <option>1-2 days</option>
                              <option>3-4 days</option>
                              <option>5+ days</option>
                              <option>No preference</option>
                          </select>
                      </div>
                  </div>

                  <div class="col-md-6">
                      <div class="vb-form-group">
                          <label class="vb-label">Days Off Priority</label>
                          <select class="vb-select">
                              <option>Weekends</option>
                              <option>Weekdays</option>
                              <option>Specific dates</option>
                              <option>Maximum total</option>
                          </select>
                      </div>
                  </div>
              </div>

              <div class="vb-form-group">
                  <label class="vb-label">Avoid These</label>
                  <div class="vb-chip-group vb-mt-2">
                      <span class="vb-chip active">Red-eyes</span>
                      <span class="vb-chip">Early shows</span>
                      <span class="vb-chip">Late finishes</span>
                      <span class="vb-chip active">Stand-ups</span>
                      <span class="vb-chip">International</span>
                      <span class="vb-chip">Deadheads</span>
                  </div>
              </div>

              <div class="vb-form-group">
                  <label class="vb-label">Preferred Layover Cities</label>
                  <input type="text" class="vb-input" placeholder="e.g., SAN, MIA, AUS" value="{{ preferences.layover_cities }}">
              </div>

              <div class="vb-form-group">
                  <label class="vb-label">Additional Notes</label>
                  <textarea class="vb-textarea" rows="3" placeholder="Any other preferences or constraints...">{{ preferences.notes }}</textarea>
              </div>

              <div class="vb-btn-group">
                  <button class="vb-btn vb-btn-primary">
                      <i class="fas fa-save"></i>
                      Save Preferences
                  </button>
                  <button class="vb-btn vb-btn-secondary">
                      <i class="fas fa-undo"></i>
                      Reset to Default
                  </button>
              </div>
          </div>
      </div>
  </div>
</div>
{% endblock %}

{% block extra_scripts %}
<script>
// Chip selection
document.querySelectorAll('.vb-chip').forEach(chip => {
  chip.addEventListener('click', function() {
      this.classList.toggle('active');
  });
});
</script>
{% endblock %}