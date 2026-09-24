# Orange Data Mining Guide for AromaData

W tym katalogu możesz zapisywać swoje pliki projektowe (`.ows`) dla Orange Data Mining.

## Jak wczytać dane do Orange Data Mining:
1. **Z plików CSV / Excel**:
   - Użyj widgetu **File** w Orange.
   - Wskaż plik z `data/raw/csv/` (np. `orders.csv`, `oils.csv`, `customers.csv`) lub `data/raw/excel/olejki_calosc.xlsx`.
   - Orange automatycznie rozpozna typy kolumn (numeryczne, kategoryczne, tekstowe).
2. **Bezpośrednio z bazy SQLite**:
   - Użyj widgetu **SQL Table** z pakietu Orange Data Mining.
   - Wskaż plik bazy: `data/db/olejki.db`.
   - Możesz wykonywać łączenia tabel (JOIN) lub wybierać pojedyncze tabele do eksploracji.
3. **Analiza asocjacji (Koszzyk zakupowy)**:
   - Połącz `orders.csv` i `order_items.csv` z widgetem **Association Rules** w Orange, aby odkryć które olejki klienci najczęściej kupują razem!
