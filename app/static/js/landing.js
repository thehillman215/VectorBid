// VectorBid Landing Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // FAQ Toggle functionality
    const faqQuestions = document.querySelectorAll('.faq-question');
    
    faqQuestions.forEach(question => {
        question.addEventListener('click', function() {
            const answer = this.nextElementSibling;
            const isActive = answer.classList.contains('active');
            
            // Close all FAQ answers
            document.querySelectorAll('.faq-answer').forEach(ans => {
                ans.classList.remove('active');
            });
            
            // Toggle current answer
            if (!isActive) {
                answer.classList.add('active');
            }
        });
    });
    
    // Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('a[href^="#"]');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe all fade-in-up elements
    const fadeElements = document.querySelectorAll('.fade-in-up');
    fadeElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
        observer.observe(el);
    });
    
    // Analytics tracking function
    window.track = function(event, properties = {}) {
        console.log('Analytics Event:', event, properties);
        
        // Here you would integrate with your analytics service
        // Examples: Google Analytics, Mixpanel, Amplitude, etc.
        
        // Google Analytics 4 example:
        // gtag('event', event, properties);
        
        // Mixpanel example:
        // mixpanel.track(event, properties);
        
        // For now, just log to console
        if (typeof gtag !== 'undefined') {
            gtag('event', event, properties);
        }
    };
    
    // Track page load
    track('landing_page_view', {
        page: window.location.pathname,
        referrer: document.referrer
    });
    
    // Track CTA button clicks
    const ctaButtons = document.querySelectorAll('.btn-primary');
    ctaButtons.forEach(button => {
        button.addEventListener('click', function() {
            track('cta_click', {
                button_text: this.textContent.trim(),
                button_location: this.closest('section')?.className || 'unknown'
            });
        });
    });
    
    // Track demo button clicks
    const demoButtons = document.querySelectorAll('a[href="/demo"], a[href*="demo"]');
    demoButtons.forEach(button => {
        button.addEventListener('click', function() {
            track('demo_click', {
                button_text: this.textContent.trim(),
                button_location: this.closest('section')?.className || 'unknown'
            });
        });
    });
    
    // Track section visibility
    const sections = document.querySelectorAll('section[id]');
    const sectionObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                track('section_view', {
                    section: entry.target.id
                });
            }
        });
    }, { threshold: 0.5 });
    
    sections.forEach(section => {
        sectionObserver.observe(section);
    });
    
    // Mobile menu toggle (if needed in the future)
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('active');
        });
    }
    
    // Newsletter signup form handler (if added)
    const newsletterForm = document.getElementById('newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = this.querySelector('input[type="email"]').value;
            
            track('newsletter_signup', { email: email });
            
            // Here you would handle the actual signup
            alert('Thank you for subscribing! We\'ll keep you updated on VectorBid.');
        });
    }
    
    // Pricing plan selection tracking
    const pricingButtons = document.querySelectorAll('#pricing .btn-primary, #pricing .btn-secondary');
    pricingButtons.forEach(button => {
        button.addEventListener('click', function() {
            const card = this.closest('.pricing-card');
            const planName = card.querySelector('h3').textContent;
            const price = card.querySelector('.price').textContent;
            
            track('pricing_plan_click', {
                plan: planName,
                price: price
            });
        });
    });
});

// Utility functions
function debounce(func, wait) {
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

// Scroll progress indicator (optional enhancement)
function initScrollProgress() {
    const progressBar = document.createElement('div');
    progressBar.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 0%;
        height: 3px;
        background: linear-gradient(90deg, #3b82f6, #1d4ed8);
        z-index: 9999;
        transition: width 0.1s ease;
    `;
    document.body.appendChild(progressBar);
    
    window.addEventListener('scroll', debounce(() => {
        const scrollTop = window.pageYOffset;
        const docHeight = document.body.scrollHeight - window.innerHeight;
        const scrollPercent = (scrollTop / docHeight) * 100;
        progressBar.style.width = scrollPercent + '%';
    }, 10));
}

// Initialize scroll progress on load
// initScrollProgress();
