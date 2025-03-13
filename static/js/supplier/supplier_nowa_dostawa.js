/**
 * Moduł obsługujący dostawy w panelu dostawcy
 */

const SupplierDelivery = {
    /**
     * SEKCJA 1: KONFIGURACJA
     */
    config: {
        // Stałe kalkulacyjne
        VAT_RATES: {
            "23": 0.23,
            "0": 0
        },
        SUPPORTED_CURRENCIES: ["PLN", "EUR"],
        DEFAULT_CURRENCY: "PLN",

        // Konfiguracja plików
        maxFileSize: 10 * 1024 * 1024, // 10MB
        allowedExtensions: {
            data: ["xlsx", "xls", "csv"],
            documents: ["pdf", "doc", "docx"]
        },
        
        // Endpointy API
        apiEndpoints: {
            processExcel: '/supplier/api/process-excel',
            saveDelivery: '/supplier/api/save-delivery',
            refreshSession: '/supplier/api/refresh-session'
        },

        // Konfiguracja kroków
        steps: {
            current: 1,
            total: 4,
            names: {
                1: "Informacje podstawowe",
                2: "Dokumenty",
                3: "Szczegóły dostawy",
                4: "Podsumowanie"
            }
        },

        // Konfiguracja formularza
        form: {
            categories: [
                { value: "MIX", label: "MIX" },
                { value: "Elektronika", label: "Elektronika" },
                { value: "AGD", label: "AGD" },
                { value: "Meble", label: "Meble" },
                { value: "Ogród", label: "Ogród" },
                { value: "other", label: "Inne" }
            ],
            productClasses: [
                { value: "mix_abc", label: "Mix ABC" },
                { value: "class_a", label: "Klasa A" }
            ],
            currencies: [
                { value: "PLN", label: "PLN" },
                { value: "EUR", label: "EUR" }
            ]
        },

        // Konfiguracja UI
        ui: {
            notifications: {
                duration: 5000,
                position: 'top-right'
            },
            loading: {
                defaultMessage: "Proszę czekać...",
                saveMessage: "Zapisywanie dostawy...",
                uploadMessage: "Przetwarzanie plików..."
            },
            valueSlider: {
                min: 1,
                max: 100,
                default: 50,
                step: 1
            }
        },

        // Konfiguracja sesji
        session: {
            refreshInterval: 300000, // 5 minut
            redirectUrl: '/supplier/login'
        },

        // Konfiguracja walidacji
        validation: {
            requiredFields: {
                step1: [
                    "delivery_date",
                    "delivery_category",
                    "product_class",
                    "currency"
                ],
                step3: [
                    "summary_lot_number",
                    "summary_pallet_number"
                ],
                step4: [
                    "accept_terms"
                ]
            }
        },

        // Konfiguracja debugowania
        debug: {
            enabled: true,
            logLevel: 'info', // 'error' | 'warn' | 'info' | 'debug'
            exportToWindow: true
        }
    },

    /**
     * SEKCJA 2: REFERENCJE DO ELEMENTÓW DOM
     */
    elements: {
        init() {
            // Formularze
            this.forms = {
                deliveryForm: document.getElementById('deliveryForm'),
                step1: document.getElementById('step1Form'),
                step2: document.getElementById('step2Form'),
                step3: document.getElementById('step3Form'),
                step4: document.getElementById('step4Form')
            };

            // Elementy plików
            this.fileInputs = {
                dropzone: document.getElementById('dropzone-file'),
                dropzoneLabel: document.querySelector('label[for="dropzone-file"]'),
                fileList: document.getElementById('file-list')
            };

            // Przyciski nawigacji
            this.navigationButtons = {};
            for (let i = 1; i <= 4; i++) {
                this.navigationButtons[i] = {
                    next: document.getElementById(`step${i}NextButton`),
                    prev: document.getElementById(`step${i}PrevButton`)
                };
            }

            // Pola formularza
            this.formFields = {
                deliveryDate: document.getElementById('delivery_date'),
                category: document.getElementById('delivery_category'),
                otherCategory: document.getElementById('other_category'),
                productClass: document.getElementById('product_class'),
                currency: document.getElementById('currency'),
                exchangeRate: document.getElementById('exchange_rate'),
                vatRadios: document.querySelectorAll('input[name="vat_rate"]'),
                priceTypeRadios: document.querySelectorAll('input[name="price_type"]'),
                valuePercentage: document.getElementById('value_percentage'),
                valuePercentageDisplay: document.getElementById('value_percentage_display')
            };

            // Elementy podsumowania
            this.summaryElements = {
                lotNumber: document.getElementById('summary_lot_number'),
                palletNumber: document.getElementById('summary_pallet_number'),
                deliveryDate: document.getElementById('summary_delivery_date'),
                category: document.getElementById('summary_delivery_category'),
                productClass: document.getElementById('summary_product_class'),
                currency: document.getElementById('summary_currency'),
                exchangeRate: document.getElementById('summary_exchange_rate'),
                vat: document.getElementById('summary_vat'),
                priceType: document.getElementById('summary_price_type'),
                valuePercentage: document.getElementById('summary_value_percentage'),
                productsCount: document.getElementById('products_count'),
                totalValue: document.getElementById('total_value'),
                lotsCount: document.getElementById('lots_count'),
                palletsCount: document.getElementById('pallets_count')
            };

            // Kontenery
            this.containers = {
                otherCategory: document.getElementById('other_category_container'),
                exchangeRate: document.getElementById('exchange_rate_container'),
                priceType: document.getElementById('price_type_container'),
                summaryExchangeRate: document.getElementById('summary_exchange_rate_container')
            };

            // Popup
            this.popup = {
                container: document.getElementById('missing_data_popup'),
                lotSection: document.getElementById('missing_lot_section'),
                palletSection: document.getElementById('missing_pallet_section'),
                lotInput: document.getElementById('popup_lot_number'),
                palletInput: document.getElementById('popup_pallet_number'),
                confirmButton: document.getElementById('confirm_missing_data'),
                closeButton: document.getElementById('close_missing_data')
            };
        }
    },

    /**
     * SEKCJA 3: OBSŁUGA KROKÓW
     */
    stepper: {
        currentStep: 1,
        totalSteps: 4,
        
        showStep(step) {
            console.log('Pokazuję krok:', step);
            
            if (step < 1 || step > this.totalSteps) {
                console.error('Nieprawidłowy numer kroku:', step);
                return;
            }
            
            // Ukryj wszystkie kroki
            for (let i = 1; i <= this.totalSteps; i++) {
                const stepElement = document.getElementById(`step${i}`);
                if (stepElement) {
                    stepElement.classList.add('hidden');
                } else {
                    console.error(`Nie znaleziono elementu dla kroku ${i}`);
                }
            }
            
            // Pokaż wybrany krok
            const currentStepElement = document.getElementById(`step${step}`);
            if (currentStepElement) {
                currentStepElement.classList.remove('hidden');
                this.currentStep = step;
                
                // Specjalna obsługa dla kroku 3
                if (step === 3) {
                    console.log('Inicjalizacja kroku 3...');
                    
                    // Sprawdź czy mamy przetworzone dane
                    if (SupplierDelivery.fileHandler.processedData) {
                        console.log('Znaleziono przetworzone dane:', SupplierDelivery.fileHandler.processedData);
                        SupplierDelivery.fileHandler.updateDeliveryData(SupplierDelivery.fileHandler.processedData);
                    } else {
                        console.warn('Brak przetworzonych danych dla kroku 3!');
                        SupplierDelivery.ui.showNotification('Najpierw wgraj plik z danymi w kroku 2', 'warning');
                    }
                    
                    // Aktualizuj podsumowanie z kroku 1
                    SupplierDelivery.ui.updateStep3Summary();
                }
                
                // Specjalna obsługa dla kroku 4
                if (step === 4) {
                    console.log('Inicjalizacja kroku 4...');
                    SupplierDelivery.ui.updateSummary();
                }
                
                this.updateStepperUI();
            } else {
                console.error('Nie znaleziono elementu dla kroku:', step);
            }
        },

        nextStep() {
            console.log('Rozpoczynam przejście do następnego kroku. Obecny krok:', this.currentStep);
            
            // Walidacja przed przejściem do następnego kroku
            if (!SupplierDelivery.validator.validateStep(this.currentStep)) {
                console.log('Walidacja kroku nie powiodła się');
                return;
            }

            // Jeśli przechodzimy do kroku 3
            if (this.currentStep === 2) {
                console.log('Przechodzę do kroku 3, sprawdzam dane...');
                
                // Sprawdź czy mamy przetworzone dane
                if (!SupplierDelivery.fileHandler.processedData) {
                    console.warn('Brak przetworzonych danych - wymagane wgranie pliku');
                    SupplierDelivery.ui.showNotification('Najpierw wgraj plik z danymi', 'warning');
                    return;
                }
                
                // Aktualizuj dane z kroku 1 i pokaż krok 3
                SupplierDelivery.ui.updateStep3Summary();
                this.showStep(3);
                return;
            }
            
            // Jeśli przechodzimy do kroku 4
            if (this.currentStep === 3) {
                console.log('Przechodzę do kroku 4, sprawdzam dane produktów...');
                
                // Sprawdź czy tabela produktów ma dane
                const productsTable = document.getElementById('products-table-body');
                if (!productsTable || !productsTable.getElementsByTagName('tr').length) {
                    console.warn('Brak danych w tabeli produktów');
                    SupplierDelivery.ui.showNotification('Brak danych w tabeli produktów', 'warning');
                    return;
                }
                
                // Aktualizuj podsumowanie i pokaż krok 4
                SupplierDelivery.ui.updateSummary();
                this.showStep(4);
                return;
            }

            // Dla pozostałych kroków
            this.showStep(this.currentStep + 1);
        },

        previousStep() {
            if (this.currentStep > 1) {
                this.showStep(this.currentStep - 1);
            }
        },

        validateCurrentStep() {
            console.log('Walidacja kroku:', this.currentStep);
            return SupplierDelivery.validator.validateStep(this.currentStep);
        },

        updateStepperUI() {
            console.log('Aktualizacja UI steppera dla kroku:', this.currentStep);
            
            // Aktualizacja przycisków nawigacji
            const prevButton = document.getElementById(`step${this.currentStep}PrevButton`);
            const nextButton = document.getElementById(`step${this.currentStep}NextButton`);
            
            if (prevButton) {
                if (this.currentStep === 1) {
                    prevButton.style.display = 'none';
                } else {
                    prevButton.style.display = 'block';
                }
            }
            
            if (nextButton) {
                if (this.currentStep === this.totalSteps) {
                    nextButton.style.display = 'none';
                } else {
                    nextButton.style.display = 'block';
                }
            }
        }
    },

    /**
     * SEKCJA 4: KALKULACJE
     */
    calculator: {
        validateCurrency(currency) {
            if (!currency || typeof currency !== 'string') {
                console.warn("Nieprawidłowy typ lub brak kodu waluty. Używam domyślnej waluty:", SupplierDelivery.config.DEFAULT_CURRENCY);
                return SupplierDelivery.config.DEFAULT_CURRENCY;
            }

            const normalizedCurrency = currency.trim().toUpperCase();
            if (normalizedCurrency.length !== 3) {
                console.warn(`Nieprawidłowa długość kodu waluty: "${currency}". Używam domyślnej waluty:`, SupplierDelivery.config.DEFAULT_CURRENCY);
                return SupplierDelivery.config.DEFAULT_CURRENCY;
            }

            if (!SupplierDelivery.config.SUPPORTED_CURRENCIES.includes(normalizedCurrency)) {
                console.warn(`Nieobsługiwany kod waluty: "${normalizedCurrency}". Używam domyślnej waluty:`, SupplierDelivery.config.DEFAULT_CURRENCY);
                return SupplierDelivery.config.DEFAULT_CURRENCY;
            }

            return normalizedCurrency;
        },

        parseNumber(value) {
            if (!value || value === "") return 0;
            
            let str = String(value).trim();
            
            if (str.includes("e")) {
                return parseFloat(str) || 0;
            }
            
            str = str.replace(/[^\d.,\-]/g, "");
            
            if (!str) return 0;
            
            if (str.includes(",") && str.includes(".")) {
                str = str.replace(/\./g, "").replace(",", ".");
            } else {
                str = str.replace(",", ".");
            }
            
            const result = parseFloat(str);
            return isNaN(result) ? 0 : result;
        },

        formatCurrency(value, currency) {
            const validCurrency = this.validateCurrency(currency);
            
            try {
                const formatter = new Intl.NumberFormat("pl-PL", {
                    style: "currency",
                    currency: validCurrency,
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                });
                return formatter.format(parseFloat(value) || 0);
            } catch (error) {
                console.error(`Błąd formatowania waluty: ${error.message}. Używam domyślnego formatowania.`);
                return `${parseFloat(value || 0).toFixed(2)} ${validCurrency}`;
            }
        },

        calculateDeliveryValue(marketValue, percentage, currency, exchangeRate = 1, vatRate = "23", priceType = "net") {
            const marketValuePLN = currency === "EUR" ? marketValue * exchangeRate : marketValue;
            const percentageValue = percentage / 100;
            let lotPrice = marketValuePLN * percentageValue;
            
            if (priceType === "net" && vatRate === "23") {
                lotPrice = lotPrice * (1 + SupplierDelivery.config.VAT_RATES["23"]);
            }
            
            return {
                marketValueOriginal: marketValue,
                marketValuePLN: marketValuePLN,
                deliveryValue: lotPrice,
                vatAmount: priceType === "net" ? 
                    (lotPrice / (1 + SupplierDelivery.config.VAT_RATES[vatRate])) * 
                    SupplierDelivery.config.VAT_RATES[vatRate] : 0
            };
        }
    },

    /**
     * SEKCJA 5: WALIDACJA
     */
    validator: {
        validateStep(step) {
            console.log('Walidacja kroku:', step);
            
            switch(step) {
                case 1:
                    return this.validateStep1();
                case 2:
                    return this.validateStep2();
                case 3:
                    return this.validateStep3();
                case 4:
                    return this.validateStep4();
                default:
                    return false;
            }
        },

        validateStep1() {
            const fields = SupplierDelivery.elements.formFields;
            
            console.log("Walidacja kroku 1:", {
                deliveryDate: fields.deliveryDate?.value,
                category: fields.category?.value,
                otherCategory: fields.otherCategory?.value,
                productClass: fields.productClass?.value,
                currency: fields.currency?.value,
                vatChecked: Array.from(fields.vatRadios).some(radio => radio.checked),
                priceTypeChecked: Array.from(fields.priceTypeRadios).some(radio => radio.checked)
            });
            
            // Sprawdź wymagane pola
            if (!fields.deliveryDate.value) {
                SupplierDelivery.ui.showNotification("Wybierz datę dostawy", "error");
                return false;
            }

            if (!fields.category.value) {
                SupplierDelivery.ui.showNotification("Wybierz kategorię dostawy", "error");
                return false;
            }

            if (fields.category.value === "other" && !fields.otherCategory.value) {
                SupplierDelivery.ui.showNotification("Wprowadź własną kategorię", "error");
                return false;
            }

            if (!fields.productClass.value) {
                SupplierDelivery.ui.showNotification("Wybierz klasę produktów", "error");
                return false;
            }

            if (!fields.currency.value) {
                SupplierDelivery.ui.showNotification("Wybierz walutę", "error");
                return false;
            }

            // Sprawdź kurs EUR
            if (fields.currency.value === "EUR" && !fields.exchangeRate.value) {
                SupplierDelivery.ui.showNotification("Wprowadź kurs EUR", "error");
                return false;
            }

            // Sprawdź VAT
            const vatChecked = Array.from(fields.vatRadios).some(radio => radio.checked);
            if (!vatChecked) {
                SupplierDelivery.ui.showNotification("Wybierz stawkę VAT", "error");
                return false;
            }

            // Sprawdź typ ceny dla VAT 23%
            const vat23Checked = document.getElementById("vat_23")?.checked;
            if (vat23Checked) {
                const priceTypeChecked = Array.from(fields.priceTypeRadios).some(radio => radio.checked);
                if (!priceTypeChecked) {
                    SupplierDelivery.ui.showNotification("Wybierz typ ceny dla VAT 23%", "error");
                    return false;
                }
            }

            // Sprawdź procent wartości
            const valuePercentage = parseInt(fields.valuePercentage.value);
            if (!valuePercentage || valuePercentage < 1 || valuePercentage > 100) {
                SupplierDelivery.ui.showNotification("Wybierz procent wartości (1-100)", "error");
                return false;
            }

            return true;
        },

        validateStep2() {
            // Sprawdź czy jest przynajmniej jeden plik
            const fileList = SupplierDelivery.elements.fileInputs.fileList;
            console.log("Walidacja kroku 2:", {
                fileListExists: !!fileList,
                fileCount: fileList?.children?.length || 0,
                hasEmptyMessage: !!fileList?.querySelector('td[colspan="5"]')
            });
            
            if (!fileList || !fileList.children.length || fileList.querySelector('td[colspan="5"]')) {
                SupplierDelivery.ui.showNotification("Dodaj przynajmniej jeden plik", "error");
                return false;
            }
            return true;
        },

        validateStep3() {
            console.log('Walidacja kroku 3...');
            // Sprawdź czy dane zostały przetworzone
            const productsTable = document.getElementById('products-table-body');
            const hasRows = productsTable && productsTable.getElementsByTagName('tr').length > 0;
            
            console.log('Stan tabeli produktów:', {
                tableExists: !!productsTable,
                rowCount: productsTable?.getElementsByTagName('tr').length || 0
            });
            
            if (!hasRows) {
                SupplierDelivery.ui.showNotification("Brak danych w tabeli produktów", "error");
                return false;
            }
            return true;
        },

        validateStep4() {
            const termsAccepted = document.getElementById("accept_terms");
            if (!termsAccepted?.checked) {
                SupplierDelivery.ui.showNotification("Zaakceptuj warunki", "error");
                return false;
            }
            return true;
        },

        checkFormCompleteness() {
            const missingFields = [];
            const elements = SupplierDelivery.elements;

            // Sprawdź podstawowe pola
            if (!elements.formFields.deliveryDate.value) missingFields.push("Data dostawy");
            if (!elements.formFields.category.value) missingFields.push("Kategoria dostawy");
            if (!elements.formFields.productClass.value) missingFields.push("Klasa produktów");
            if (!elements.formFields.currency.value) missingFields.push("Waluta");

            // Sprawdź pliki
            if (!elements.fileInputs.fileList.children.length) missingFields.push("Pliki");

            // Sprawdź numery LOT i palety
            if (!elements.summaryElements.lotNumber.value) missingFields.push("Numer LOT");
            if (!elements.summaryElements.palletNumber.value) missingFields.push("Numer palety");

            return {
                isComplete: missingFields.length === 0,
                missingFields
            };
        }
    },
    /**
     * SEKCJA 6: OBSŁUGA PLIKÓW
     */
    fileHandler: {
        setupFileHandling() {
            const elements = SupplierDelivery.elements.fileInputs;
            const dropzoneLabel = elements.dropzoneLabel;
            const dropzone = elements.dropzone;

            // Obsługa przeciągania plików
            dropzoneLabel.addEventListener("dragenter", (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzoneLabel.classList.add("border-purple-500", "bg-violet-50", "dark:bg-violet-900");
            });

            dropzoneLabel.addEventListener("dragleave", (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzoneLabel.classList.remove("border-purple-500", "bg-violet-50", "dark:bg-violet-900");
            });

            dropzoneLabel.addEventListener("dragover", (e) => {
                e.preventDefault();
                e.stopPropagation();
            });

            dropzoneLabel.addEventListener("drop", (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzoneLabel.classList.remove("border-purple-500", "bg-violet-50", "dark:bg-violet-900");
                this.handleFiles(e.dataTransfer.files);
            });

            // Obsługa wyboru plików przez input
            dropzone.addEventListener("change", (e) => {
                this.handleFiles(e.target.files);
            });
        },

        displayFileInTable(file) {
            const fileList = SupplierDelivery.elements.fileInputs.fileList;
            const row = document.createElement('tr');
            row.className = 'bg-white border-b dark:bg-gray-800 dark:border-gray-700';
            
            // Formatowanie rozmiaru pliku
            const fileSize = SupplierDelivery.utils.formatFileSize(file.size);
            
            // Pobierz rozszerzenie pliku
            const extension = file.name.split('.').pop().toUpperCase();
            
            row.innerHTML = `
                <td class="px-6 py-4 font-medium text-gray-900 dark:text-white">${file.name}</td>
                <td class="px-6 py-4">${fileSize}</td>
                <td class="px-6 py-4">${extension}</td>
                <td class="px-6 py-4 text-center">
                    <span class="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded dark:bg-green-900 dark:text-green-300">
                        Gotowy
                    </span>
                </td>
                <td class="px-6 py-4">
                    <button type="button" class="font-medium text-red-600 dark:text-red-500 hover:underline">
                        Usuń
                    </button>
                </td>
            `;
            
            // Dodaj obsługę usuwania pliku
            const deleteButton = row.querySelector('button');
            deleteButton.addEventListener('click', () => {
                row.remove();
                // Sprawdź czy tabela jest pusta
                if (fileList.children.length === 0) {
                    fileList.innerHTML = `
                        <tr class="bg-white dark:bg-gray-800">
                            <td colspan="5" class="px-6 py-4 text-center text-gray-500 dark:text-gray-400">
                                Brak wgranych plików
                            </td>
                        </tr>
                    `;
                }
            });
            
            // Usuń komunikat o braku plików jeśli istnieje
            if (fileList.querySelector('td[colspan="5"]')) {
                fileList.innerHTML = '';
            }
            
            fileList.appendChild(row);
        },

        async handleFiles(files) {
            console.log('Rozpoczynam przetwarzanie plików...');
            
            if (!files || !files.length) {
                console.error('Nie wybrano plików');
                SupplierDelivery.ui.showNotification('Wybierz plik do wgrania', 'error');
                return;
            }

            // Pobierz CSRF token
            const csrfToken = this.getCsrfToken();
            console.log('CSRF Token:', csrfToken ? 'Token znaleziony' : 'Token nie znaleziony');
            
            if (!csrfToken) {
                console.error('Nie znaleziono tokenu CSRF w dokumencie');
                SupplierDelivery.ui.showNotification('Błąd: Brak tokenu CSRF - odśwież stronę', 'error');
                return;
            }

            for (const file of files) {
                try {
                    // Sprawdź rozszerzenie pliku
                    const fileExtension = file.name.split('.').pop().toLowerCase();
                    const allowedExtensions = ['xlsx', 'xls', 'csv'];
                    
                    if (!allowedExtensions.includes(fileExtension)) {
                        throw new Error(`Nieobsługiwany format pliku. Dozwolone formaty: ${allowedExtensions.join(', ')}`);
                    }

                    // Sprawdź rozmiar pliku
                    if (file.size > SupplierDelivery.config.maxFileSize) {
                        throw new Error('Plik przekracza maksymalny rozmiar 10MB');
                    }

                    // Przygotuj dane do wysłania
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('csrf_token', csrfToken);
                    
                    // Dodaj delivery_id jeśli istnieje
                    if (this.processedData && this.processedData.delivery_id) {
                        formData.append('delivery_id', this.processedData.delivery_id);
                    }

                    console.log('Przygotowano FormData z tokenem CSRF');

                    // Pokaż loader
                    SupplierDelivery.ui.showLoading('Przetwarzanie pliku...');

                    try {
                        console.log('Wysyłanie żądania do:', SupplierDelivery.config.apiEndpoints.processExcel);
                        
                        // Wyślij plik do API
                        const response = await fetch(SupplierDelivery.config.apiEndpoints.processExcel, {
                            method: 'POST',
                            body: formData,
                            headers: {
                                'X-CSRFToken': csrfToken,
                                'X-Requested-With': 'XMLHttpRequest'
                            },
                            credentials: 'same-origin'
                        });

                        // Sprawdź typ odpowiedzi
                        const contentType = response.headers.get("content-type");
                        
                        // Próbuj pobrać dane JSON niezależnie od statusu odpowiedzi
                        let responseData;
                        try {
                            if (contentType && contentType.includes("application/json")) {
                                responseData = await response.json();
                            }
                        } catch (e) {
                            console.error('Błąd parsowania JSON:', e);
                            throw new Error('Błąd podczas przetwarzania odpowiedzi serwera');
                        }

                        if (!response.ok) {
                            // Użyj komunikatu z odpowiedzi JSON jeśli jest dostępny
                            const errorMessage = responseData?.message || `Błąd serwera: ${response.status} ${response.statusText}`;
                            throw new Error(errorMessage);
                        }

                        if (!responseData) {
                            throw new Error('Nieoczekiwany format odpowiedzi z serwera');
                        }

                        if (!responseData.success) {
                            throw new Error(responseData.message || 'Wystąpił błąd podczas przetwarzania pliku');
                        }

                        // Zapisz przetworzone dane
                        this.processedData = responseData.data;
                        
                        // Wyświetl plik w tabeli
                        this.displayFileInTable(file);
                        
                        // Aktualizuj dane dostawy
                        await this.handleLotAnalysis(responseData.data.lot_analysis);
                        this.updateDeliveryData(responseData.data);
                        
                        SupplierDelivery.ui.showNotification('Plik został pomyślnie przetworzony', 'success');
                        
                    } catch (error) {
                        console.error('Błąd podczas przetwarzania pliku:', error);
                        SupplierDelivery.ui.showNotification(error.message || 'Wystąpił nieoczekiwany błąd', 'error');
                        
                        // Usuń plik z tabeli w przypadku błędu
                        const fileList = document.getElementById('file-list');
                        const existingRow = fileList.querySelector(`[data-filename="${file.name}"]`);
                        if (existingRow) {
                            existingRow.remove();
                        }
                        
                        // Sprawdź czy tabela jest pusta i dodaj komunikat
                        if (fileList && (!fileList.children.length || fileList.children.length === 0)) {
                            fileList.innerHTML = `
                                <tr class="bg-white dark:bg-gray-800">
                                    <td colspan="5" class="px-6 py-4 text-center text-gray-500 dark:text-gray-400">
                                        Brak wgranych plików
                                    </td>
                                </tr>
                            `;
                        }
                    } finally {
                        SupplierDelivery.ui.hideLoading();
                    }
                } catch (error) {
                    console.error('Błąd podczas przetwarzania pliku:', error);
                    SupplierDelivery.ui.showNotification(error.message || 'Wystąpił nieoczekiwany błąd', 'error');
                    
                    // Usuń plik z tabeli w przypadku błędu
                    const fileList = document.getElementById('file-list');
                    const existingRow = fileList.querySelector(`[data-filename="${file.name}"]`);
                    if (existingRow) {
                        existingRow.remove();
                    }
                    
                    // Sprawdź czy tabela jest pusta i dodaj komunikat
                    if (fileList && (!fileList.children.length || fileList.children.length === 0)) {
                        fileList.innerHTML = `
                            <tr class="bg-white dark:bg-gray-800">
                                <td colspan="5" class="px-6 py-4 text-center text-gray-500 dark:text-gray-400">
                                    Brak wgranych plików
                                </td>
                            </tr>
                        `;
                    }
                }
            }
        },

        async handleLotAnalysis(lotAnalysis) {
            console.log('Otrzymano analizę LOT z backendu:', lotAnalysis);
            
            const elements = SupplierDelivery.elements.summaryElements;
            const popup = SupplierDelivery.elements.popup;
            
            // Jeśli są numery LOT w tabeli, użyj ich
            if (lotAnalysis.has_lot_column && lotAnalysis.lots && lotAnalysis.lots.length > 0 && !lotAnalysis.all_empty) {
                console.log('Używam numerów LOT z tabeli:', lotAnalysis.lots);
                elements.lotNumber.value = lotAnalysis.lots.join(', ');
                SupplierDelivery.ui.updateSummary();
                return;
            }
            
            // Jeśli nie ma numerów LOT w tabeli, użyj numeru z nazwy pliku
            if (lotAnalysis.found_in_filename) {
                console.log('Używam numeru LOT z nazwy pliku:', lotAnalysis.found_in_filename);
                elements.lotNumber.value = lotAnalysis.found_in_filename;
                SupplierDelivery.ui.updateSummary();
                return;
            }

            // Jeśli nie ma LOT ani w tabeli ani w nazwie pliku, pokaż pop-up
            console.log('Brak numerów LOT, pokazuję pop-up');
            popup.container.classList.remove('invisible', 'opacity-0');
            popup.lotSection.classList.remove('hidden');
            popup.palletSection.classList.remove('hidden');

            // Obsługa przycisku potwierdzenia
            popup.confirmButton.onclick = () => {
                const lotNumber = popup.lotInput.value;
                const palletNumber = popup.palletInput.value;

                if (lotNumber) {
                    elements.lotNumber.value = lotNumber;
                }
                if (palletNumber) {
                    elements.palletNumber.value = palletNumber;
                }

                popup.container.classList.add('invisible', 'opacity-0');
                SupplierDelivery.ui.updateSummary();
            };

            // Obsługa przycisku zamknięcia
            popup.closeButton.onclick = () => {
                popup.container.classList.add('invisible', 'opacity-0');
            };
        },

        updateDeliveryData(data) {
            console.log('Rozpoczynam aktualizację danych dostawy:', data);
            
            const elements = SupplierDelivery.elements.summaryElements;
            
            if (!data) {
                console.error('Brak danych do aktualizacji!');
                return;
            }
            
            // Aktualizacja statystyk
            if (data.summary) {
                console.log('Aktualizuję podsumowanie:', data.summary);
                
                // Aktualizacja liczby produktów
                if (data.summary.total_rows) {
                    elements.productsCount.textContent = data.summary.total_rows;
                    document.getElementById('items_count').textContent = data.summary.total_rows;
                }
                
                // Aktualizacja wartości
                if (data.summary.total_value) {
                    const formattedValue = parseFloat(data.summary.total_value).toFixed(2);
                    elements.totalValue.textContent = formattedValue;
                    document.getElementById('total_value').textContent = formattedValue;
                }
                
                // Aktualizacja LOT
                if (data.summary.lots) {
                    elements.lotsCount.textContent = data.summary.lots.length;
                    elements.lotNumber.value = data.summary.lots.join(", ");
                    document.getElementById('lots_count').textContent = data.summary.lots.length;
                }
                
                // Aktualizacja palet
                if (data.summary.pallets) {
                    elements.palletsCount.textContent = data.summary.pallets.length;
                    elements.palletNumber.value = data.summary.pallets.join(", ");
                    document.getElementById('pallets_count').textContent = data.summary.pallets.length;
                }
            }
            
            // Aktualizacja tabeli produktów
            if (data.headers && data.rows) {
                const tableBody = document.getElementById('products-table-body');
                const tableHead = document.querySelector('#products-table thead');
                
                if (!tableBody || !tableHead) {
                    console.error('Nie znaleziono elementów tabeli!');
                    return;
                }
                
                // Mapowanie kolumn
                const columnMapping = {
                    'WARTOSC': 'Wartość',
                    'Nr Lot': 'LOT',
                    'NR Palety': 'Paleta',
                    'Item Desc': 'Nazwa produktu',
                    'EAN': 'EAN',
                    'ASIN': 'ASIN',
                    'ilosc': 'Ilość',
                    'CENA': 'Cena',
                    'WALUTA': 'Waluta',
                    'JEDNOSTKA': 'Jednostka'
                };
                
                // Aktualizacja nagłówków z mapowaniem
                tableHead.innerHTML = `
                    <tr class="text-xs text-gray-700 uppercase bg-gradient-to-r from-purple-50 to-purple-100 dark:from-purple-900 dark:to-purple-800 sticky top-0">
                        ${data.headers.map(header => `
                            <th scope="col" class="px-4 py-3 font-bold text-violet-900 dark:text-violet-200">
                                ${columnMapping[header] || header}
                            </th>
                        `).join('')}
                    </tr>
                `;
                
                // Aktualizacja wierszy
                tableBody.innerHTML = data.rows.map(row => {
                    return `
                        <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700">
                            ${data.headers.map(header => `
                                <td class="px-4 py-3 text-gray-900 dark:text-gray-300">
                                    ${row[header] !== null && row[header] !== undefined ? row[header] : ''}
                                </td>
                            `).join('')}
                        </tr>
                    `;
                }).join('');
            }
            
            // Po aktualizacji danych, odśwież podsumowanie w kroku 4
            if (SupplierDelivery.stepper.currentStep === 3) {
                SupplierDelivery.ui.updateSummary();
            }
        },

        getCsrfToken() {
            // Najpierw spróbuj pobrać z meta tagu
            const metaToken = document.querySelector('meta[name="csrf-token"]')?.content;
            if (metaToken) {
                return metaToken;
            }
            
            // Jeśli nie ma w meta, spróbuj pobrać z ukrytego pola formularza
            const formToken = document.querySelector('input[name="csrf_token"]')?.value;
            if (formToken) {
                return formToken;
            }
            
            // Jeśli nie znaleziono tokenu, zwróć null
            return null;
        },

        formatFileSize(size) {
            if (size < 1024) {
                return size + ' B';
            } else if (size < 1024 * 1024) {
                return (size / 1024).toFixed(2) + ' KB';
            } else {
                return (size / (1024 * 1024)).toFixed(2) + ' MB';
            }
        },

        updateSummary() {
            console.log('Aktualizacja podsumowania...');
            
            const elements = SupplierDelivery.elements.summaryElements;
            const fields = SupplierDelivery.elements.formFields;
            
            // Pobierz wartości
            const marketValue = parseFloat(elements.totalValue.textContent) || 0;
            const currency = fields.currency.value;
            const exchangeRate = parseFloat(fields.exchangeRate.value) || 1;
            const percentage = parseInt(fields.valuePercentage.value) || 0;
            const vatRate = document.querySelector('input[name="vat_rate"]:checked')?.value || '23';
            const priceType = document.querySelector('input[name="price_type"]:checked')?.value || 'net';
            
            console.log('Wartości do kalkulacji:', {
                marketValue,
                currency,
                exchangeRate,
                percentage,
                vatRate,
                priceType
            });
            
            // Oblicz wartości
            const marketValuePLN = currency === 'EUR' ? marketValue * exchangeRate : marketValue;
            const percentageValue = percentage / 100;
            let lotPrice = marketValuePLN * percentageValue;
            
            if (priceType === 'net' && vatRate === '23') {
                lotPrice = lotPrice * (1 + 0.23); // Dodaj VAT
            }
            
            // Aktualizuj pola w tabeli podsumowania
            document.getElementById('summary_table_lot').textContent = elements.lotNumber.value || '-';
            document.getElementById('summary_table_pallets').textContent = elements.palletNumber.value || '-';
            document.getElementById('summary_table_category').textContent = fields.category.value === 'other' ? fields.otherCategory.value : fields.category.value;
            document.getElementById('summary_table_class').textContent = fields.productClass.value;
            document.getElementById('summary_table_products').textContent = elements.productsCount.textContent;
            document.getElementById('summary_table_vat').textContent = vatRate + '%';
            document.getElementById('summary_table_percentage').textContent = percentage + '%';
            document.getElementById('summary_table_market_value').textContent = this.formatCurrency(marketValue, currency);
            document.getElementById('summary_table_market_value_pln').textContent = this.formatCurrency(marketValuePLN, 'PLN');
            document.getElementById('summary_table_lot_price').textContent = this.formatCurrency(lotPrice, 'PLN');
            document.getElementById('summary_table_currency').textContent = currency;
            
            if (currency === 'EUR') {
                document.getElementById('summary_table_exchange_rate').textContent = exchangeRate;
                document.getElementById('exchange_rate_header').classList.remove('hidden');
                document.getElementById('summary_table_exchange_rate').classList.remove('hidden');
            } else {
                document.getElementById('exchange_rate_header').classList.add('hidden');
                document.getElementById('summary_table_exchange_rate').classList.add('hidden');
            }
            
            console.log('Podsumowanie zaktualizowane');
        }
    },

    /**
     * SEKCJA 9: INNE
     */
    utils: {
        getCsrfToken() {
            // Implementacja pobierania CSRF tokenu
            return 'CSRF_TOKEN';
        },

        formatFileSize(size) {
            if (size < 1024) {
                return size + ' B';
            } else if (size < 1024 * 1024) {
                return (size / 1024).toFixed(2) + ' KB';
            } else {
                return (size / (1024 * 1024)).toFixed(2) + ' MB';
            }
        }
    },

    formHandler: {
        setupEventListeners() {
            console.log('Inicjalizacja event listenerów...');
            
            // Obsługa zmiany waluty
            const currencySelect = document.getElementById('currency');
            const exchangeRateContainer = document.getElementById('exchange_rate_container');
            
            console.log('Elementy waluty:', {
                currencySelect: !!currencySelect,
                exchangeRateContainer: !!exchangeRateContainer
            });
            
            if (currencySelect && exchangeRateContainer) {
                currencySelect.addEventListener('change', (e) => {
                    console.log('Zmiana waluty:', e.target.value);
                    if (e.target.value === 'EUR') {
                        console.log('Pokazuję pole kursu EUR');
                        exchangeRateContainer.classList.remove('hidden');
                    } else {
                        console.log('Ukrywam pole kursu EUR');
                        exchangeRateContainer.classList.add('hidden');
                    }
                });
                console.log('Dodano listener do selecta waluty');
            }

            // Obsługa kategorii "Inne"
            const categorySelect = document.getElementById('delivery_category');
            const otherCategoryContainer = document.getElementById('other_category_container');
            
            if (categorySelect && otherCategoryContainer) {
                categorySelect.addEventListener('change', (e) => {
                    if (e.target.value === 'other') {
                        otherCategoryContainer.classList.remove('hidden');
                    } else {
                        otherCategoryContainer.classList.add('hidden');
                    }
                });
            }

            // Obsługa VAT 23%
            const vatRadios = document.querySelectorAll('input[name="vat_rate"]');
            const priceTypeContainer = document.getElementById('price_type_container');
            
            if (vatRadios && priceTypeContainer) {
                vatRadios.forEach(radio => {
                    radio.addEventListener('change', (e) => {
                        if (e.target.value === '23') {
                            priceTypeContainer.classList.remove('hidden');
                        } else {
                            priceTypeContainer.classList.add('hidden');
                        }
                    });
                });
            }

            // Obsługa suwaka procentowego
            const valuePercentage = document.getElementById('value_percentage');
            const valuePercentageDisplay = document.getElementById('value_percentage_display');
            
            if (valuePercentage && valuePercentageDisplay) {
                valuePercentage.addEventListener('input', (e) => {
                    valuePercentageDisplay.textContent = e.target.value;
                });
            }

            // Obsługa formularza głównego
            const deliveryForm = document.getElementById('deliveryForm');
            if (deliveryForm) {
                deliveryForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    try {
                        SupplierDelivery.ui.showLoading('Zapisywanie dostawy...');
                        
                        // Pobierz token CSRF
                        const csrfToken = SupplierDelivery.fileHandler.getCsrfToken();
                        if (!csrfToken) {
                            throw new Error('Brak tokenu CSRF - odśwież stronę');
                        }
                        
                        // Przygotuj dane do wysłania
                        const formData = {
                            delivery_id: SupplierDelivery.fileHandler.processedData?.delivery_id,
                            delivery_date: document.getElementById('delivery_date').value,
                            delivery_category: document.getElementById('delivery_category').value,
                            other_category: document.getElementById('other_category').value,
                            product_class: document.getElementById('product_class').value,
                            currency: document.getElementById('currency').value,
                            exchange_rate: document.getElementById('exchange_rate').value,
                            vat_rate: document.querySelector('input[name="vat_rate"]:checked')?.value,
                            price_type: document.querySelector('input[name="price_type"]:checked')?.value,
                            value_percentage: document.getElementById('value_percentage').value,
                            lot_number: document.getElementById('summary_lot_number').value,
                            pallet_number: document.getElementById('summary_pallet_number').value,
                            total_value: parseFloat(document.getElementById('total_value').textContent),
                            items_count: parseInt(document.getElementById('items_count').textContent),
                            lots_count: parseInt(document.getElementById('lots_count').textContent),
                            pallets_count: parseInt(document.getElementById('pallets_count').textContent)
                        };
                        
                        console.log('Wysyłam dane dostawy:', formData);
                        
                        // Wyślij żądanie
                        const response = await fetch(deliveryForm.action, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrfToken
                            },
                            body: JSON.stringify(formData)
                        });
                        
                        if (!response.ok) {
                            const errorData = await response.json();
                            throw new Error(errorData.message || 'Błąd podczas zapisywania dostawy');
                        }
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            SupplierDelivery.ui.showNotification('Dostawa została zapisana pomyślnie', 'success');
                            // Przekieruj do listy dostaw po 2 sekundach
                            setTimeout(() => {
                                window.location.href = '/supplier/deliveries';
                            }, 2000);
                        } else {
                            throw new Error(result.message || 'Błąd podczas zapisywania dostawy');
                        }
                    } catch (error) {
                        console.error('Błąd podczas zapisywania dostawy:', error);
                        SupplierDelivery.ui.showNotification(error.message || 'Wystąpił błąd podczas zapisywania dostawy', 'error');
                    } finally {
                        SupplierDelivery.ui.hideLoading();
                    }
                });
            }

            // Obsługa przycisków nawigacji
            const step1NextButton = document.getElementById('step1NextButton');
            if (step1NextButton) {
                step1NextButton.addEventListener('click', () => {
                    console.log('Kliknięto przycisk Dalej w kroku 1');
                    SupplierDelivery.stepper.nextStep();
                });
            }

            const step2NextButton = document.getElementById('step2NextButton');
            const step2PrevButton = document.getElementById('step2PrevButton');
            if (step2NextButton && step2PrevButton) {
                step2NextButton.addEventListener('click', () => SupplierDelivery.stepper.nextStep());
                step2PrevButton.addEventListener('click', () => SupplierDelivery.stepper.previousStep());
            }

            const step3NextButton = document.getElementById('step3NextButton');
            const step3PrevButton = document.getElementById('step3PrevButton');
            if (step3NextButton && step3PrevButton) {
                step3NextButton.addEventListener('click', () => SupplierDelivery.stepper.nextStep());
                step3PrevButton.addEventListener('click', () => SupplierDelivery.stepper.previousStep());
            }

            const step4PrevButton = document.getElementById('step4PrevButton');
            if (step4PrevButton) {
                step4PrevButton.addEventListener('click', () => SupplierDelivery.stepper.previousStep());
            }
        }
    },

    ui: {
        showNotification(message, type = 'info') {
            console.log('Pokazuję powiadomienie:', { message, type });
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-all duration-300 ease-in-out transform translate-x-full ${
                type === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100' :
                type === 'error' ? 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100' :
                type === 'warning' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100' :
                'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100'
            }`;
            
            notification.innerHTML = `
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        ${type === 'success' ? '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>' :
                        type === 'error' ? '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>' :
                        type === 'warning' ? '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>' :
                        '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path></svg>'}
                    </div>
                    <div class="ml-3">
                        <p class="text-sm font-medium">${message}</p>
                    </div>
                </div>
            `;
            
            document.body.appendChild(notification);
            
            // Animacja wejścia
            setTimeout(() => {
                notification.classList.remove('translate-x-full');
            }, 100);
            
            // Automatyczne zamknięcie
            setTimeout(() => {
                notification.classList.add('translate-x-full');
                setTimeout(() => {
                    notification.remove();
                }, 300);
            }, 5000);
        },

        showLoading(message = 'Proszę czekać...') {
            console.log('Pokazuję loader:', message);
            const loader = document.createElement('div');
            loader.id = 'loading-overlay';
            loader.className = 'fixed inset-0 bg-gray-900/50 dark:bg-gray-900/80 z-50 flex items-center justify-center';
            loader.innerHTML = `
                <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-xl flex items-center space-x-4">
                    <div class="animate-spin rounded-full h-8 w-8 border-4 border-violet-500 border-t-transparent"></div>
                    <p class="text-gray-900 dark:text-white">${message}</p>
                </div>
            `;
            document.body.appendChild(loader);
        },

        hideLoading() {
            console.log('Ukrywam loader');
            const loader = document.getElementById('loading-overlay');
            if (loader) {
                loader.remove();
            }
        },

        updateStep3Summary() {
            console.log('Aktualizuję podsumowanie kroku 3');
            const elements = SupplierDelivery.elements;
            
            // Aktualizuj pola podsumowania
            elements.summaryElements.deliveryDate.value = elements.formFields.deliveryDate.value;
            elements.summaryElements.category.value = elements.formFields.category.value === 'other' ? 
                elements.formFields.otherCategory.value : 
                elements.formFields.category.value;
            elements.summaryElements.productClass.value = elements.formFields.productClass.value;
            elements.summaryElements.currency.value = elements.formFields.currency.value;
            elements.summaryElements.exchangeRate.value = elements.formFields.exchangeRate.value;
            elements.summaryElements.vat.value = Array.from(elements.formFields.vatRadios).find(radio => radio.checked)?.value || '';
            elements.summaryElements.priceType.value = Array.from(elements.formFields.priceTypeRadios).find(radio => radio.checked)?.value || '';
            elements.summaryElements.valuePercentage.value = elements.formFields.valuePercentage.value;
        },

        updateSummary() {
            console.log('Aktualizacja podsumowania...');
            
            const elements = SupplierDelivery.elements.summaryElements;
            const fields = SupplierDelivery.elements.formFields;
            
            // Pobierz wartości
            const marketValue = parseFloat(elements.totalValue.textContent) || 0;
            const currency = fields.currency.value;
            const exchangeRate = parseFloat(fields.exchangeRate.value) || 1;
            const percentage = parseInt(fields.valuePercentage.value) || 0;
            const vatRate = document.querySelector('input[name="vat_rate"]:checked')?.value || '23';
            const priceType = document.querySelector('input[name="price_type"]:checked')?.value || 'net';
            
            console.log('Wartości do kalkulacji:', {
                marketValue,
                currency,
                exchangeRate,
                percentage,
                vatRate,
                priceType
            });
            
            // Oblicz wartości
            const marketValuePLN = currency === 'EUR' ? marketValue * exchangeRate : marketValue;
            const percentageValue = percentage / 100;
            let lotPrice = marketValuePLN * percentageValue;
            
            if (priceType === 'net' && vatRate === '23') {
                lotPrice = lotPrice * (1 + 0.23); // Dodaj VAT
            }
            
            // Aktualizuj pola w tabeli podsumowania
            document.getElementById('summary_table_lot').textContent = elements.lotNumber.value || '-';
            document.getElementById('summary_table_pallets').textContent = elements.palletNumber.value || '-';
            document.getElementById('summary_table_category').textContent = fields.category.value === 'other' ? fields.otherCategory.value : fields.category.value;
            document.getElementById('summary_table_class').textContent = fields.productClass.value;
            document.getElementById('summary_table_products').textContent = elements.productsCount.textContent;
            document.getElementById('summary_table_vat').textContent = vatRate + '%';
            document.getElementById('summary_table_percentage').textContent = percentage + '%';
            document.getElementById('summary_table_market_value').textContent = this.formatCurrency(marketValue, currency);
            document.getElementById('summary_table_market_value_pln').textContent = this.formatCurrency(marketValuePLN, 'PLN');
            document.getElementById('summary_table_lot_price').textContent = this.formatCurrency(lotPrice, 'PLN');
            document.getElementById('summary_table_currency').textContent = currency;
            
            if (currency === 'EUR') {
                document.getElementById('summary_table_exchange_rate').textContent = exchangeRate;
                document.getElementById('exchange_rate_header').classList.remove('hidden');
                document.getElementById('summary_table_exchange_rate').classList.remove('hidden');
            } else {
                document.getElementById('exchange_rate_header').classList.add('hidden');
                document.getElementById('summary_table_exchange_rate').classList.add('hidden');
            }
            
            console.log('Podsumowanie zaktualizowane');
        },

        formatCurrency(value, currency) {
            return new Intl.NumberFormat('pl-PL', {
                style: 'currency',
                currency: currency,
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(value);
        }
    }
};

// Inicjalizacja przy załadowaniu strony
document.addEventListener('DOMContentLoaded', () => {
    console.log('Inicjalizacja aplikacji...');
    
    // Inicjalizacja elementów
    SupplierDelivery.elements.init();
    console.log('Elementy zainicjalizowane');
    
    // Inicjalizacja event listenerów
    SupplierDelivery.formHandler.setupEventListeners();
    console.log('Event listenery zainicjalizowane');
    
    // Inicjalizacja obsługi plików
    SupplierDelivery.fileHandler.setupFileHandling();
    console.log('Obsługa plików zainicjalizowana');
    
    // Pokaż pierwszy krok
    SupplierDelivery.stepper.showStep(1);
    console.log('Pierwszy krok wyświetlony');
});