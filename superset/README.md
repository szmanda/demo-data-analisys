# Apache Superset Setup Guide for AromaData

Ten katalog przygotowuje integrację bazy danych "Olejki" z Apache Superset.

## Opcja 1: SQLite (Najszybsza do lokalnego testowania)
1. Baza danych SQLite znajduje się w pliku: `data/db/olejki.db`.
2. W Apache Superset przejdź do: **Settings** -> **Database Connections** -> **+ Database**.
3. Wybierz typ: **SQLite**.
4. Wpisz SQLAlchemy URI:
   ```
   sqlite:////bezwzgledna/sciezka/do/data-analisys/data/db/olejki.db
   ```
5. Przetestuj połączenie i zapisz. Wszystkie tabele (`orders`, `order_items`, `oils`, `customers`, etc.) będą natychmiast dostępne do tworzenia wykresów, dashboardów i zapytań SQL Lab.

## Opcja 2: PostgreSQL (Zalecana produkcyjnie)
1. W katalogu `data/raw/postgres/` wygenerowany jest gotowy zrzut DDL/DML: `aroma_dump_postgres.sql`.
2. Zaimportuj go do swojej bazy PostgreSQL:
   ```bash
   psql -h localhost -U postgres -d moja_baza -f data/raw/postgres/aroma_dump_postgres.sql
   ```
3. W Superset połącz się przez PostgreSQL URI:
   ```
   postgresql://postgres:haslo@localhost:5432/moja_baza
   ```
