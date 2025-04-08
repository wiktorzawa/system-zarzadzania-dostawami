// Wrapper dla simple-datatables.js
// Tworzy globalny obiekt DataTable do użycia z Flowbite Pro

(function() {
    // Sprawdź, czy simpleDatatables jest dostępny
    if (typeof simpleDatatables === 'undefined') {
        console.error('Biblioteka simpleDatatables nie została załadowana!');
        return;
    }

    // Utwórz globalny obiekt DataTable
    window.DataTable = simpleDatatables.DataTable;
    
    console.log('DataTable został pomyślnie zainicjalizowany jako obiekt globalny.');
})(); 