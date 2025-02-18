'use strict';

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 Supplier Controls: Inicjalizacja...');

    // Aktywne linki w sidebarze
    const currentPath = window.location.pathname;
    console.log('📍 Supplier Controls: Aktualna ścieżka:', currentPath);

    const sidebarLinks = document.querySelectorAll('#logo-sidebar a');
    console.log('📍 Supplier Controls: Znaleziono linków w sidebarze:', sidebarLinks.length);

    Array.prototype.forEach.call(sidebarLinks, function(link) {
        const linkPath = link.getAttribute('href');
        console.log('🔍 Supplier Controls: Sprawdzam link:', linkPath);
        
        if (linkPath === currentPath) {
            console.log('✅ Supplier Controls: Znaleziono aktywny link:', linkPath);
            link.classList.add('bg-violet-50', 'text-violet-600', 'dark:bg-violet-900', 'dark:text-violet-300');
        }
    });
}); 