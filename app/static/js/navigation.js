// Professional Navigation System
class Navigation {
  constructor() {
    this.mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    this.mobileMenuOverlay = document.getElementById('mobile-menu-overlay');
    this.mobileMenuPanel = document.getElementById('mobile-menu-panel');
    this.navMenu = document.getElementById('nav-menu');
    this.dropdowns = document.querySelectorAll('.dropdown');
    this.mobileDropdownTriggers = document.querySelectorAll('.mobile-nav-link');
    
    this.isMenuOpen = false;
    this.activeDropdown = null;
    
    this.init();
  }
  
  init() {
    this.setupMobileMenu();
    this.setupDropdowns();
    this.setupMobileDropdowns();
    this.setupKeyboardNavigation();
    this.setupClickOutside();
    this.setupSearchFunctionality();
    this.setupActiveStates();
  }
  
  setupMobileMenu() {
    if (this.mobileMenuToggle) {
      this.mobileMenuToggle.addEventListener('click', (e) => {
        e.preventDefault();
        this.toggleMobileMenu();
      });
    }
    
    if (this.mobileMenuOverlay) {
      this.mobileMenuOverlay.addEventListener('click', () => {
        this.closeMobileMenu();
      });
    }
    
    // Close mobile menu on window resize if viewport becomes desktop
    window.addEventListener('resize', () => {
      if (window.innerWidth >= 768 && this.isMenuOpen) {
        this.closeMobileMenu();
      }
    });
  }
  
  toggleMobileMenu() {
    this.isMenuOpen = !this.isMenuOpen;
    
    if (this.isMenuOpen) {
      this.openMobileMenu();
    } else {
      this.closeMobileMenu();
    }
  }
  
  openMobileMenu() {
    document.body.classList.add('mobile-menu-active');
    this.mobileMenuToggle.setAttribute('aria-expanded', 'true');
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    
    // Focus management
    this.trapFocus(this.mobileMenuPanel);
  }
  
  closeMobileMenu() {
    document.body.classList.remove('mobile-menu-active');
    this.mobileMenuToggle.setAttribute('aria-expanded', 'false');
    this.isMenuOpen = false;
    
    // Restore body scroll
    document.body.style.overflow = '';
    
    // Close all mobile dropdowns
    document.querySelectorAll('.mobile-dropdown.active').forEach(dropdown => {
      dropdown.classList.remove('active');
    });
    
    // Return focus to toggle button
    this.mobileMenuToggle.focus();
  }
  
  setupDropdowns() {
    this.dropdowns.forEach(dropdown => {
      const trigger = dropdown.querySelector('.nav-link');
      const menu = dropdown.querySelector('.dropdown-menu');
      let hoverTimeout;
      
      if (!trigger || !menu) return;
      
      // Mouse events
      dropdown.addEventListener('mouseenter', () => {
        clearTimeout(hoverTimeout);
        this.openDropdown(dropdown);
      });
      
      dropdown.addEventListener('mouseleave', () => {
        hoverTimeout = setTimeout(() => {
          this.closeDropdown(dropdown);
        }, 300); // Delay to allow moving between trigger and menu
      });
      
      // Keyboard events
      trigger.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.toggleDropdown(dropdown);
        } else if (e.key === 'ArrowDown') {
          e.preventDefault();
          this.openDropdown(dropdown);
          this.focusFirstMenuItem(menu);
        }
      });
      
      // Setup menu item navigation
      this.setupMenuNavigation(menu);
    });
  }
  
  setupMenuNavigation(menu) {
    const menuItems = menu.querySelectorAll('.dropdown-link, .dropdown-mega-link');
    
    menuItems.forEach((item, index) => {
      item.addEventListener('keydown', (e) => {
        switch (e.key) {
          case 'ArrowDown':
            e.preventDefault();
            this.focusMenuItem(menuItems, index + 1);
            break;
          case 'ArrowUp':
            e.preventDefault();
            this.focusMenuItem(menuItems, index - 1);
            break;
          case 'Escape':
            e.preventDefault();
            this.closeAllDropdowns();
            break;
          case 'Tab':
            if (e.shiftKey && index === 0) {
              this.closeAllDropdowns();
            } else if (!e.shiftKey && index === menuItems.length - 1) {
              this.closeAllDropdowns();
            }
            break;
        }
      });
    });
  }
  
  setupMobileDropdowns() {
    this.mobileDropdownTriggers.forEach(trigger => {
      const chevron = trigger.querySelector('i');
      const dropdown = trigger.nextElementSibling;
      
      if (!dropdown || !dropdown.classList.contains('mobile-dropdown')) return;
      
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        
        const isActive = dropdown.classList.contains('active');
        
        // Close other dropdowns
        document.querySelectorAll('.mobile-dropdown.active').forEach(dd => {
          if (dd !== dropdown) {
            dd.classList.remove('active');
            const trigger = dd.previousElementSibling.querySelector('i');
            if (trigger) trigger.style.transform = 'rotate(0deg)';
          }
        });
        
        // Toggle current dropdown
        dropdown.classList.toggle('active', !isActive);
        if (chevron) {
          chevron.style.transform = isActive ? 'rotate(0deg)' : 'rotate(90deg)';
        }
      });
    });
  }
  
  openDropdown(dropdown) {
    this.closeAllDropdowns();
    this.activeDropdown = dropdown;
    
    const trigger = dropdown.querySelector('.nav-link');
    const menu = dropdown.querySelector('.dropdown-menu');
    
    if (trigger) trigger.setAttribute('aria-expanded', 'true');
    if (menu) menu.setAttribute('aria-hidden', 'false');
  }
  
  closeDropdown(dropdown) {
    const trigger = dropdown.querySelector('.nav-link');
    const menu = dropdown.querySelector('.dropdown-menu');
    
    if (trigger) trigger.setAttribute('aria-expanded', 'false');
    if (menu) menu.setAttribute('aria-hidden', 'true');
    
    if (this.activeDropdown === dropdown) {
      this.activeDropdown = null;
    }
  }
  
  toggleDropdown(dropdown) {
    if (this.activeDropdown === dropdown) {
      this.closeDropdown(dropdown);
    } else {
      this.openDropdown(dropdown);
    }
  }
  
  closeAllDropdowns() {
    this.dropdowns.forEach(dropdown => {
      this.closeDropdown(dropdown);
    });
  }
  
  focusFirstMenuItem(menu) {
    const firstItem = menu.querySelector('.dropdown-link, .dropdown-mega-link');
    if (firstItem) firstItem.focus();
  }
  
  focusMenuItem(menuItems, index) {
    const clampedIndex = Math.max(0, Math.min(index, menuItems.length - 1));
    menuItems[clampedIndex].focus();
  }
  
  setupKeyboardNavigation() {
    document.addEventListener('keydown', (e) => {
      switch (e.key) {
        case 'Escape':
          if (this.isMenuOpen) {
            this.closeMobileMenu();
          } else {
            this.closeAllDropdowns();
          }
          break;
        case 'Tab':
          // Close dropdowns when tabbing away from navigation
          if (!e.target.closest('.nav-menu')) {
            this.closeAllDropdowns();
          }
          break;
      }
    });
  }
  
  setupClickOutside() {
    document.addEventListener('click', (e) => {
      // Close dropdowns when clicking outside
      if (!e.target.closest('.dropdown')) {
        this.closeAllDropdowns();
      }
      
      // Close mobile menu when clicking outside
      if (this.isMenuOpen && !e.target.closest('.primary-nav')) {
        this.closeMobileMenu();
      }
    });
  }
  
  setupSearchFunctionality() {
    const searchInputs = document.querySelectorAll('.nav-search-input');
    
    searchInputs.forEach(input => {
      input.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        if (query.length > 2) {
          this.performSearch(query);
        }
      });
      
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const query = e.target.value.trim();
          if (query) {
            window.location.href = `/search?q=${encodeURIComponent(query)}`;
          }
        }
      });
    });
  }
  
  performSearch(query) {
    // Debounced search functionality
    clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(() => {
      // Implement search suggestions or redirect
      console.log('Searching for:', query);
      // You can implement autocomplete suggestions here
    }, 300);
  }
  
  setupActiveStates() {
    // Highlight current page in navigation
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link, .mobile-nav-link');
    
    navLinks.forEach(link => {
      const href = link.getAttribute('href');
      if (href && this.isActiveLink(href, currentPath)) {
        link.closest('.nav-item, .mobile-nav-item')?.classList.add('active');
      }
    });
  }
  
  isActiveLink(href, currentPath) {
    // Exact match
    if (href === currentPath) return true;
    
    // Partial match for section pages
    if (href !== '/' && currentPath.startsWith(href)) return true;
    
    return false;
  }
  
  trapFocus(element) {
    const focusableElements = element.querySelectorAll(
      'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select'
    );
    
    const firstFocusableElement = focusableElements[0];
    const lastFocusableElement = focusableElements[focusableElements.length - 1];
    
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstFocusableElement) {
            lastFocusableElement.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastFocusableElement) {
            firstFocusableElement.focus();
            e.preventDefault();
          }
        }
      }
    });
    
    firstFocusableElement.focus();
  }
}

// Smooth scroll for anchor links
class SmoothScroll {
  constructor() {
    this.init();
  }
  
  init() {
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href^="#"]');
      if (!link) return;
      
      const targetId = link.getAttribute('href').substring(1);
      const targetElement = document.getElementById(targetId);
      
      if (targetElement) {
        e.preventDefault();
        this.scrollToElement(targetElement);
      }
    });
  }
  
  scrollToElement(element) {
    const headerHeight = document.querySelector('.site-header')?.offsetHeight || 0;
    const targetPosition = element.offsetTop - headerHeight - 20;
    
    window.scrollTo({
      top: targetPosition,
      behavior: 'smooth'
    });
  }
}

// Scroll direction detection for header
class ScrollHandler {
  constructor() {
    this.lastScrollY = window.scrollY;
    this.header = document.querySelector('.site-header');
    this.init();
  }
  
  init() {
    window.addEventListener('scroll', () => {
      this.handleScroll();
    });
  }
  
  handleScroll() {
    const currentScrollY = window.scrollY;
    
    if (currentScrollY > 100) {
      this.header?.classList.add('scrolled');
    } else {
      this.header?.classList.remove('scrolled');
    }
    
    this.lastScrollY = currentScrollY;
  }
}

// Initialize navigation when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new Navigation();
  new SmoothScroll();
  new ScrollHandler();
});

// Export for testing purposes
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { Navigation, SmoothScroll, ScrollHandler };
}
