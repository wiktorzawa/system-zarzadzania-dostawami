document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 Drawer.js: Inicjalizacja...');

    // Funkcja inicjalizująca sidebar
    function initSidebar() {
        console.log('🎯 Drawer.js: Inicjalizacja sidebara...');
        const sidebarTrigger = document.querySelector('[data-drawer-target="logo-sidebar"]');
        const sidebar = document.getElementById('logo-sidebar');
        
        console.log('📍 Drawer.js: Sprawdzam elementy sidebara:', {
            trigger: sidebarTrigger ? 'znaleziony' : 'brak',
            sidebar: sidebar ? 'znaleziony' : 'brak'
        });

        if (sidebarTrigger && sidebar) {
            const options = {
                placement: sidebarTrigger.getAttribute('data-drawer-placement') || 'left',
                backdrop: sidebarTrigger.getAttribute('data-drawer-backdrop') === 'true',
                bodyScrolling: false,
                edge: true,
                edgeOffset: '0px',
                onHide: () => {
                    console.log('🚫 Drawer.js: Sidebar został ukryty');
                    removeBackdrop();
                },
                onShow: () => {
                    console.log('👁️ Drawer.js: Sidebar został pokazany');
                    if (options.backdrop) {
                        addBackdrop(() => {
                            const drawer = new Drawer(sidebar);
                            drawer.hide();
                        });
                    }
                }
            };

            // Inicjalizacja sidebara z Flowbite
            const drawer = new Drawer(sidebar, options);

            // Obsługa kliknięcia przycisku sidebara
            sidebarTrigger.addEventListener('click', (e) => {
                console.log('🖱️ Drawer.js: Kliknięcie przycisku sidebara');
                e.preventDefault();
                drawer.toggle();
            });

            // Zamykanie po kliknięciu w link w menu (na mobile)
            sidebar.querySelectorAll('a').forEach(link => {
                link.addEventListener('click', () => {
                    if (window.innerWidth < 640) {
                        console.log('📱 Drawer.js: Zamykanie sidebara na mobile po kliknięciu w link');
                        drawer.hide();
                    }
                });
            });
        }
    }

    // Funkcja inicjalizująca navbar dropdown
    function initNavbarDropdown() {
        console.log('🎯 Drawer.js: Inicjalizacja dropdowna w navbarze...');
        const dropdownTrigger = document.querySelector('[data-dropdown-toggle="dropdown-user"]');
        const dropdownMenu = document.getElementById('dropdown-user');

        console.log('📍 Drawer.js: Sprawdzam elementy dropdowna:', {
            trigger: dropdownTrigger ? 'znaleziony' : 'brak',
            menu: dropdownMenu ? 'znaleziony' : 'brak'
        });

        if (dropdownTrigger && dropdownMenu) {
            // Inicjalizacja dropdowna z Flowbite
            const dropdown = new Dropdown(dropdownMenu, dropdownTrigger, {
                placement: 'bottom-end',
                triggerType: 'click',
                offsetSkidding: 0,
                offsetDistance: 10,
                onHide: () => {
                    console.log('🚫 Drawer.js: Dropdown został ukryty');
                },
                onShow: () => {
                    console.log('👁️ Drawer.js: Dropdown został pokazany');
                }
            });

            // Zamykanie dropdowna po kliknięciu poza nim
            document.addEventListener('click', (e) => {
                if (!dropdownTrigger.contains(e.target) && !dropdownMenu.contains(e.target)) {
                    console.log('🔙 Drawer.js: Zamykanie dropdowna po kliknięciu poza');
                    dropdown.hide();
                }
            });

            // Zamykanie po kliknięciu w link
            dropdownMenu.querySelectorAll('a').forEach(link => {
                link.addEventListener('click', () => {
                    console.log('🔙 Drawer.js: Zamykanie dropdowna po kliknięciu w link');
                    dropdown.hide();
                });
            });
        }
    }

    // Funkcje pomocnicze dla backdrop
    function addBackdrop(onClickCallback) {
        const backdrop = document.createElement('div');
        backdrop.classList.add('bg-gray-900', 'bg-opacity-50', 'dark:bg-opacity-80', 'fixed', 'inset-0', 'z-30', 'drawer-backdrop');
        document.body.appendChild(backdrop);
        
        backdrop.addEventListener('click', () => {
            console.log('🔙 Drawer.js: Kliknięcie w backdrop');
            if (onClickCallback) onClickCallback();
        });
    }

    function removeBackdrop() {
        const backdrop = document.querySelector('.drawer-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
    }

    // Upewnij się, że Flowbite jest załadowany
    if (typeof Drawer === 'undefined' || typeof Dropdown === 'undefined') {
        console.error('❌ Drawer.js: Flowbite nie jest załadowany!');
        return;
    }

    // Inicjalizacja komponentów
    initSidebar();
    initNavbarDropdown();
}); 