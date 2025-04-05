// Main JavaScript file for Academic Progress Hub

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Initialize popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));

    // Flash messages auto-dismiss
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.click();
            }
        }, 5000);
    });

    // Handle confirmed actions (like delete)
    const confirmActions = document.querySelectorAll('[data-confirm]');
    confirmActions.forEach(button => {
        button.addEventListener('click', function(event) {
            if (!confirm(this.getAttribute('data-confirm') || 'Are you sure?')) {
                event.preventDefault();
            }
        });
    });

    // Theme toggle functionality
    const themeToggle = document.getElementById('themeToggle');
    const htmlElement = document.documentElement;
    const themeIconDark = document.querySelector('.theme-icon-dark');
    const themeIconLight = document.querySelector('.theme-icon-light');
    
    // Check if theme preference exists in localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        htmlElement.setAttribute('data-bs-theme', savedTheme);
        updateThemeIcon(savedTheme);
    }
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = htmlElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            htmlElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            updateThemeIcon(newTheme);

            // Update Chart.js theme colors when theme changes
            Chart.defaults.color = newTheme === 'dark' ? '#f8f9fa' : '#212529';
            Chart.defaults.borderColor = newTheme === 'dark' ? '#495057' : '#dee2e6';
        });
    }
    
    function updateThemeIcon(theme) {
        if (themeIconDark && themeIconLight) {
            if (theme === 'dark') {
                themeIconDark.classList.add('d-none');
                themeIconLight.classList.remove('d-none');
            } else {
                themeIconDark.classList.remove('d-none');
                themeIconLight.classList.add('d-none');
            }
        }
    }

    // Timetable filter functionality
    const timetableFilter = document.getElementById('timetableFilter');
    if (timetableFilter) {
        timetableFilter.addEventListener('change', function() {
            const day = this.value;
            const rows = document.querySelectorAll('.timetable-row');
            
            if (day === 'all') {
                rows.forEach(row => row.style.display = '');
            } else {
                rows.forEach(row => {
                    const rowDay = row.getAttribute('data-day');
                    row.style.display = (rowDay === day) ? '' : 'none';
                });
            }
        });
    }

    // Make notification items interactive
    const notificationItems = document.querySelectorAll('.notification-item');
    notificationItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(5px)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
        });
    });
    
    // Initialize Chart.js with proper theme
    Chart.defaults.color = htmlElement.getAttribute('data-bs-theme') === 'dark' ? '#f8f9fa' : '#212529';
    Chart.defaults.borderColor = htmlElement.getAttribute('data-bs-theme') === 'dark' ? '#495057' : '#dee2e6';
});
