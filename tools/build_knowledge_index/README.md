# RoboCamp Knowledge Index Builder

Moduł odpowiedzialny za **automatyczne generowanie indeksu wiedzy (`knowledge_index.json`)** na podstawie wszystkich artykułów blogowych RoboCamp, znajdujących się w repozytorium `robocamp-knowledge / knowledge-base`.

Ten moduł jest częścią **RoboCamp Knowledge Hub**, i stanowi główne źródło danych semantycznych dla Custom GPT (np. Gosia).

---

## Cel systemu

Celem jest stworzenie **zunifikowanego indeksu wiedzy**, który łączy dane z artykułów RoboCamp w jednym pliku JSON, zawierającym:
- metadane artykułów (`title`, `language`, `canonical_url`),
- listę rozdziałów z plików `chapters_*.json`,
- podział językowy (PL/EN),
- timestamp generacji (`generated_at`).

Efekt działania to gotowy plik:
```
metadata/knowledge_index.json
```
używany przez Custom GPT RoboCamp do analizy i cytowania źródeł.

---

## Architektura (wysoki poziom)

System składa się z dwóch elementów:

1. **GitHub Action (workflow)**  
   Odpowiada za:
   - ręczne uruchamianie procesu (`workflow_dispatch`),
   - automatyczne uruchamianie raz w tygodniu (`cron`),
   - wywołanie skryptu Pythona,
   - commit i push wyniku do repozytorium.

2. **Skrypt Python (`build_index.py`)**  
   Odpowiada za:
   - przeszukanie wszystkich katalogów artykułów,
   - odczyt metadanych z `full.md`,
   - wczytanie i scalanie wszystkich `chapters_*.json`,
   - wygenerowanie jednolitego pliku JSON (`knowledge_index.json`).

---

## Struktura katalogów (aktualna)

```
knowledge-base/
│
├─ .github/
│   └─ workflows/
│       └─ build-knowledge-index.yml   # GitHub Action
│
├─ blog/
│   └─ articles/
│       ├─ 3d-printing-in-school/
│       │   ├─ en/
│       │   │   ├─ full.md
│       │   │   └─ chapters_01-07.json
│       │   └─ pl/
│       │       ├─ full.md
│       │       └─ chapters_01-07.json
│       ├─ lego-spike-prime-review/
│       └─ lego-science-review/
│
├─ metadata/
│   └─ knowledge_index.json            # WYNIK DZIAŁANIA SKRYPTU
│
└─ tools/
    ├─ build_knowledge_index/
    │   ├─ build_index.py              # GŁÓWNY SKRYPT BUILDERA
    │   └─ README.md                   # (ten plik)
    └─ cleaner/
        └─ clean_one.py
```

---

## Lokalizacja plików w repozytorium

### Workflow (GitHub Actions)

Plik workflow:
```
.github/workflows/build-knowledge-index.yml
```

Może być:
- uruchamiany ręcznie z poziomu GitHub UI (manual trigger),
- wywoływany automatycznie co poniedziałek (harmonogram `cron`),
- aktywowany po każdej zmianie w katalogu `blog/articles/**`.

### Skrypt Buildera

Skrypt:
```
tools/build_knowledge_index/build_index.py
```

- napisany w **Pythonie 3**,  
- może być uruchamiany:
  - lokalnie (np. `python3 tools/build_knowledge_index/build_index.py`),
  - automatycznie w GitHub Actions,
- generuje plik wynikowy w katalogu `metadata/`.

---

## Repozytorium źródłowe

Źródłem danych są wszystkie artykuły RoboCamp w strukturze:
```
blog/articles/<article-id>/<language>/
```
Każdy język (np. `en` i `pl`) zawiera:
- plik `full.md` (z YAML headerem),
- jeden lub więcej plików `chapters_*.json`.

---

## Struktura danych w pliku `knowledge_index.json`

Każdy wpis w `knowledge_index.json` zawiera:

| Klucz | Typ | Opis |
|-------|-----|------|
| `slug` | string | folder artykułu |
| `article_id` | string | ID artykułu z YAML |
| `language` | string | `pl` lub `en` |
| `title` | string | Tytuł artykułu |
| `canonical_url` | string | Pełny URL wpisu |
| `chapters` | array | Lista rozdziałów z plików `chapters_*.json` |

---

### Przykład:

```json
{
  "generated_at": "2026-01-19T20:12:41Z",
  "sources": {
    "articles": [
      {
        "slug": "3d-printing-in-school",
        "article_id": "3d-printing-in-school",
        "language": "en",
        "title": "3D Printer in School – Myths, Real Uses, and Robotics with 3D Printing",
        "canonical_url": "https://www.robocamp.eu/en/blog/3d-printing-in-school/",
        "chapters": [
          {
            "chapter_id": "1",
            "title": "Introduction: 3D Printer in School – Context and Goals",
            "summary": "The chapter describes how 3D printers are increasingly common...",
            "canonical_url": "https://www.robocamp.eu/en/blog/3d-printing-in-school/"
          }
        ]
      }
    ],
    "social": []
  }
}
```

---

## Dlaczego tak

Ten system pozwala:
- zautomatyzować aktualizację indeksu wiedzy,
- uniknąć błędów przy ręcznym edytowaniu JSON,
- zapewnić aktualność danych dla Custom GPT (np. Gosia),
- ujednolicić dostęp do wiedzy dla wszystkich języków.

Dzięki temu `metadata/knowledge_index.json` staje się **centralnym semantycznym punktem repozytorium wiedzy RoboCamp**.

---

## Uruchamianie procesu

### Ręcznie (GitHub UI)
1. Wejdź w zakładkę **Actions** w repozytorium `knowledge-base`,
2. Wybierz workflow **“Build Knowledge Index”**,
3. Kliknij **“Run workflow”**,
4. Wybierz branch `main`,
5. Poczekaj, aż pojawi się log:
   ```
   ✅ Zebrano 6 artykułów (3 PL, 3 EN).
   💾 Zapisano plik: metadata/knowledge_index.json
   ```
6. Wynik zostanie automatycznie wypchnięty do repozytorium.

### Automatycznie
Workflow działa również:
- **raz w tygodniu (poniedziałek 4:00 UTC)**,
- **przy każdej zmianie w katalogu `blog/articles/**`**.

---

## Status projektu

- działa technicznie i funkcjonalnie,
- zgodny ze strukturą RoboCamp Knowledge Base,
- gotowy do dalszej rozbudowy (np. integracja z `social_posts.json`).

Ten katalog (`tools/build_knowledge_index`) jest **kanonicznym miejscem dokumentacji procesu generowania indeksu wiedzy**.

---

## Planowane rozszerzenia

1. Dodanie sekcji `social` (integracja z `social/social_posts.json`),
2. Walidator jakości danych (sprawdzanie brakujących pól),
3. Generowanie `offer_index.json` dla kursów i planów subskrypcyjnych.
