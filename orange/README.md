# Orange Data Mining Guide for AromaData

W tym katalogu możesz zapisywać swoje pliki projektowe (`.ows`) dla Orange Data Mining.

## Jak włączyć orange data mining:

Install and run:

```sh
# Anaconda
# Create and activate a conda environment for Orange (optional, but recommended)
# conda create python=3.11 --yes --name orange3
set -h
conda activate orange3
# install
# Add conda-forge to the list of channels you can install packages from (and make it default)

# conda config --add channels conda-forge
# conda config --set channel_priority strict
# conda install orange3
# orange-canvas # when the environment is already activated, or even without activating it first, just run: 
conda run -n orange3 orange-canvas
```


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
