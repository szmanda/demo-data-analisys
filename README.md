# AromaData — Generator Danych Biznesowych (Olejki)

System do generowania realistycznych, organicznych danych syntetycznych symulujących e-commerce i sieć sprzedaży olejków eterycznych, kosmetycznych i aromaterapeutycznych ("Olejki").

Projekt zaprojektowany pod kątem analizy danych, uczenia maszynowego oraz data miningu w **Orange Data Mining** i **Apache Superset**.

---

## 🚀 Szybki start

### 1. Generowanie danych
Możesz wygenerować dane bezpośrednio przy użyciu skryptu `run.sh`:

```bash
# Szybki test małej skali (scale = 0.05)
./run.sh --scale 0.05 --seed 42

# Średnia skala (rekomendowana do głębszej analizy: ~250 produktów, ~3000 klientów, ~15000 zamówień)
./run.sh --scale 1.0 --seed 42

# Wygenerowanie tylko wybranych formatów (np. CSV i SQLite):
./run.sh --scale 0.1 --formats csv sqlite
```

### 2. Formaty wyjściowe (Schema-agnostic exporters)
Wszystkie eksportery działają bezpośrednio na deklaratywnym schemacie bazy bez zaśmiecania kodu:
- **CSV**: `data/raw/csv/*.csv` (oddzielny plik dla każdej z 12 tabel, kodowanie UTF-8)
- **Excel**: `data/raw/excel/olejki_calosc.xlsx` (jeden plik wieloarkuszowy ze wszystkimi tabelami i zamrożonymi nagłówkami) oraz oddzielne pliki `.xlsx` dla każdej tabeli
- **SQLite**: `data/db/olejki.db` (kompletna relacyjna baza z kluczami obcymi i indeksami analitycznymi)
- **PostgreSQL**: `data/raw/postgres/aroma_dump_postgres.sql` (gotowy skrypt DDL i zrzut DML transakcyjny do zaimportowania do Superset)

---

## 📊 Organiczność danych i prawa potęgowe (Power Laws)

Dane **nie są losowane jednostajnie**, lecz odzwierciedlają realne zachowania konsumenckie i rynkowe:
1. **Popularność produktów (Zasada Pareto / Prawo Zipfa)**:
   - ~20% flagowych produktów generuje ~80% całkowitej sprzedaży (lawenda, drzewo herbaciane, mieszanki autorskie).
2. **Lojalność klientów (Rozkład Pareto)**:
   - Długi ogon: większość klientów kupuje 1-2 razy, podczas gdy stały segment lojalny i salony SPA dokonują regularnych, powtarzalnych zamówień.
3. **Wielkość koszyka (Rozkład geometryczny)**:
   - Przeważają koszyki 1-2 produktowe, z rzadkimi dużymi zamówieniami hurtowymi.
4. **Ceny produktów (Rozkład log-normalny)**:
   - Ceny bazowe skupione wokół 25-50 PLN z długim ogonem rzadkich, drogich esencji (np. Róża Damasceńska, Neroli). Naturalne końcówki cenowe (.99, .50, .00).
5. **Sezonowość i cykle dobowe**:
   - Wyraźne piki sprzedażowe w IV kwartale (Black Friday, Święta), wiosenne wzrosty (Walentynki, Dzień Kobiet) oraz godziny zakupów skupione w paśmie wieczornym (18:00–22:00).
6. **Demografia i geografia**:
   - Polskie imiona, nazwiska (z poprawną fleksją żeńską: *-ska*, *-cka*), polskie miasta z wagami ludnościowymi i odpowiednimi prefiksami kodów pocztowych.

---

## 🗄️ Model danych (12 tabel)

- `bases` — bazy i nośniki olejków (olej jojoba, arganowy, alkohol, hydrolaty).
- `ingredients` — czyste esencje botaniczne z nazwami łacińskimi, krajami pochodzenia i nutami zapachowymi.
- `tags` — tagi marketingowo-kategoryzacyjne (relaks, cera trądzikowa, sen, medytacja).
- `actions` — działania lecznicze, aromaterapeutyczne i kosmetyczne.
- `oils` — gotowe produkty handlowe (pojemności, ceny, koszty produkcji, SKU, daty wprowadzenia).
- `oil_ingredients` — receptury i proporcje składników w każdym olejku.
- `oil_tags` — relacja wiele-do-wielu: olejki ↔ tagi.
- `oil_actions` — relacja wiele-do-wielu z siłą działania w skali 1-5.
- `customers` — klienci podzieleni na segmenty rynkowe.
- `orders` — zamówienia ze statusami, kanałami sprzedaży, płatnościami i kodami rabatowymi.
- `order_items` — pozycje w zamówieniach.
- `reviews` — organiczne oceny i opinie klientów z pozytywnym skosem rynkowym.

---

## 🧪 Testy jednostkowe

Projekt posiada pełną baterię testów automatycznych w `tests/`:
```bash
./venv/bin/pytest -v
```
