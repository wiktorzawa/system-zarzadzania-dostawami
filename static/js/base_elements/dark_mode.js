'use strict';

document.addEventListener('DOMContentLoaded', function() {
    // Zabezpieczenie przed wielokrotną inicjalizacją
    if (window.drawerInitialized) return;
    window.drawerInitialized = true;
    
    // Główny przycisk
    const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
    const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');
    const themeToggleBtn = document.getElementById('theme-toggle');
    
    // Przycisk w nawigacji
    const themeToggleDarkIconNav = document.getElementById('theme-toggle-dark-icon-nav');
    const themeToggleLightIconNav = document.getElementById('theme-toggle-light-icon-nav');
    const themeToggleBtnNav = document.getElementById('theme-toggle-nav');
    
    // Funkcja przełączania motywu
    function toggleTheme(darkIcon, lightIcon) {
        darkIcon.classList.toggle('hidden');
        lightIcon.classList.toggle('hidden');
        
        if (localStorage.getItem('color-theme') === 'light') {
            document.documentElement.classList.add('dark');
            localStorage.setItem('color-theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('color-theme', 'light');
        }
    }
    
    // Inicjalizacja stanu ikon
    if (localStorage.getItem('color-theme') === 'dark' || (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        themeToggleLightIcon?.classList.remove('hidden');
        themeToggleLightIconNav?.classList.remove('hidden');
    } else {
        themeToggleDarkIcon?.classList.remove('hidden');
        themeToggleDarkIconNav?.classList.remove('hidden');
    }
    
    // Obsługa kliknięć
    themeToggleBtn?.addEventListener('click', () => toggleTheme(themeToggleDarkIcon, themeToggleLightIcon));
    themeToggleBtnNav?.addEventListener('click', () => toggleTheme(themeToggleDarkIconNav, themeToggleLightIconNav));
}); 