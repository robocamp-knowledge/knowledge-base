# RoboCamp Blog Cleaner & Sync Tool

Moduł odpowiedzialny za **ręczne, kontrolowane pobieranie, czyszczenie i archiwizację artykułów blogowych RoboCamp** do publicznego repozytorium wiedzy (`robocamp-knowledge / knowledge-base`).

Ten moduł jest **częścią Blog Publisher – Justyna**, ale działa jako **deterministyczny skrypt**, a nie Custom GPT.

---

## Cel systemu

Celem jest stworzenie **jednego, stabilnego źródła prawdy (single source of truth)** dla artykułów blogowych, które:

- są autorstwa RoboCamp,
- istnieją już w repozytorium strony (`robocamp-new-web`),
- mają być:
  - archiwizowane,
  - analizowane przez LLM,
  - dzielone na chapters przez Custom GPT „Justyna”.

Efektem działania systemu jest **oczyszczony, zunifikowany Markdown (`full.md`)**, gotowy do dalszego przetwarzania.

---

## Architektura (wysoki poziom)

System składa się z dwóch elementów:

1. **GitHub Action (workflow)**  
   Odpowiada za:
   - ręczne uruchamianie procesu,
   - zebranie metadanych artykułu,
   - wywołanie skryptu czyszczącego,
   - commit wyniku do repozytorium wiedzy.

2. **Skrypt Python (`clean_one.py`)**  
   Odpowiada za:
   - pobranie treści artykułu z `robocamp-new-web`,
   - czyszczenie Markdown,
   - normalizację struktury,
   - wygenerowanie `full.md`.

---

## Lokalizacja plików w repozytorium

### Workflow (GitHub Actions)

Plik workflow znajduje się zawsze w standardowej lokalizacji GitHub Actions:

.github/workflows/sync-clean-one.yml

To **jedyny plik**, który użytkownik uruchamia ręcznie z poziomu GitHub UI.

---

### Skrypt czyszczący

Skrypt odpowiedzialny za logikę czyszczenia:

tools/cleaner/clean_one.py

- nie jest uruchamiany bezpośrednio,
- zawsze działa w kontekście workflow,
- może być dalej rozwijany (np. obsługa tabel, edge-case’y Markdown).

---

## Repozytorium źródłowe (read-only)

Źródłem treści jest prywatne repozytorium strony:

robocamp-new-web

Przykładowe ścieżki źródłowe:
data/blogposts/pl/lego-science-recenzja/content.md  
data/blogposts/en/lego-science-review/content.md  

Repozytorium to jest:
- tylko do odczytu,
- traktowane jako **źródło redakcyjne**, nie archiwalne.

---

## Repozytorium docelowe (knowledge-base)

Docelowa struktura dla **jednego artykułu**:

blog/articles/<article-id>/
├── pl/
│   └── full.md
└── en/
    └── full.md

Przykład:

blog/articles/lego-science-review/
├── pl/full.md
└── en/full.md

---

## Co zawiera plik `full.md`

Każdy `full.md` składa się z dwóch części:

### 1. Front Matter (YAML)

Generowany **automatycznie przez Action**, a nie ręcznie.

Zawiera m.in.:

- article_id
- title
- language
- author (lista)
- canonical_url (pełny URL)
- web_slug
- published (data)
- license (opcjonalne)
- status (opcjonalne)

Celem jest:
- spójność,
- brak ręcznych błędów,
- możliwość późniejszej walidacji.

---

### 2. Oczyszczony Markdown (treść)

Skrypt `clean_one.py`:

1. Usuwa elementy layoutowe strony,
2. Usuwa `[TOC]`,
3. Normalizuje nagłówki,
4. **ZACHOWUJE strukturę H2/H3** (krytyczne dla chapters),
5. Konwertuje linki relatywne → absolutne, np.:

[Link](/pl/course-spike-prime-intermediate/)
→
[Link](https://www.robocamp.pl/pl/course-spike-prime-intermediate/)

6. Usuwa atrybuty po linkach, np. `{target="_blank"}`,
7. Zapisuje wynik jako `full.md`.

---

## Dlaczego tak

Ten podział rozwiązuje kilka problemów jednocześnie:

- LLM (Justyna) **nie musi czyścić treści**,
- łatwiejsze jest:
  - szacowanie objętości,
  - kontrola tokenów,
  - stabilne generowanie chapters,
- zachowana jest struktura nagłówków i anchorów,
- `full.md` może być:
  - archiwum,
  - wejściem dla chapters,
  - punktem odniesienia do bloga.

---

## Rola Custom GPT „Justyna”

Justyna:
- **nie pracuje już na surowym pliku strony**,
- dostaje `full.md` jako wejście,
- generuje chapters **ZAWSZE od nowa**,
- bazuje na:
  - strukturze H2/H3,
  - linkach do sekcji,
  - pełnych URL-ach artykułu.

---

## Uruchamianie procesu

1. Wejdź w zakładkę Actions w repozytorium `knowledge-base`,
2. Wybierz workflow „Sync & clean ONE blog article”,
3. Kliknij „Run workflow”,
4. Wypełnij dane artykułu,
5. Workflow:
   - pobierze treść,
   - oczyści ją,
   - zapisze `full.md`,
   - zrobi commit do repozytorium.

Proces jest **świadomie ręczny**, bo:
- aktualizacje artykułów nie zawsze są symetryczne (PL ≠ EN),
- często są to poprawki techniczne (tabele, formatowanie),
- po każdym update i tak uruchamiana jest Justyna.

---

## Status projektu

- działa technicznie,
- działa funkcjonalnie,
- ma stabilną architekturę,
- jest gotowy do dalszej rozbudowy.

Ten katalog (`tools/cleaner`) jest **kanonicznym miejscem dokumentacji procesu**.
