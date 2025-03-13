from lot_analyzer import LotAnalyzer

def test_lot_formatting():
    # Lista przypadków testowych: (wejście, oczekiwane_wyjście)
    test_cases = [
        ("LOT 526555585", "LOT526555585"),           # ze spacją
        ("lot526555585", "LOT526555585"),            # małe litery
        ("Lot 526555585", "LOT526555585"),           # mieszane litery i spacja
        ("526555585", "LOT526555585"),               # tylko numer
        ("LOT526555585_230506", "LOT526555585_230506"),  # z datą
        ("LOT 526555585 230506", "LOT526555585_230506"), # z datą i spacjami
        ("lot pl 526555585", "LOT526555585"),        # z "PL" w środku
        ("LOTPL526555585", "LOT526555585"),          # z "PL" bez spacji
        ("", None),                                   # pusty string
        ("LOT123", None),                            # za krótki numer
        ("LOT12345678901", None),                    # za długi numer
        ("ABC526555585", None),                      # nieprawidłowy prefix
    ]

    print("\nTesty formatowania numerów LOT:")
    print("-" * 50)
    
    for i, (input_lot, expected) in enumerate(test_cases, 1):
        result = LotAnalyzer.format_lot_number(input_lot)
        status = "✅" if result == expected else "❌"
        print(f"{status} Test {i:2d}: '{input_lot}' -> '{result}'")
        if result != expected:
            print(f"   Oczekiwano: '{expected}'")
    
    print("-" * 50)

if __name__ == "__main__":
    test_lot_formatting() 