# Blog Publisher Cleaner

Skrypt `clean_one.py` służy do automatycznego pobierania, czyszczenia i standaryzowania artykułów blogowych z repozytorium `robocamp-new-web` i umieszczania ich w odpowiedniej strukturze w repozytorium `robocamp-knowledge/knowledge-base`.

---

## 📌 Co robi ten skrypt?

- Pobiera plik `content.md` z artykułem z repozytorium źródłowego (`robocamp-new-web`) w oparciu o dane wejściowe podane w GitHub Action.
- Czyści i standaryzuje strukturę Markdown:
  - usuwa niepożądane znaczniki HTML (np. `target="_blank"`, style inline),
  - konwertuje względne linki wewnętrzne do pełnych linków absolutnych (jeśli prowadzą do stron zewnętrznych np. RoboCamp),
  - zachowuje strukturę nagłówków (H2, H3),
  - usuwa elementy niezgodne z wewnętrznym stylem redakcyjnym.
- Tworzy oczyszczony plik `full.md` gotowy do dalszego przetwarzania (np. przez Custom GPT Justyna) i umieszcza go w strukturze katalogów wiedzy (`knowledge-base`).

---

## 🚀 Jak uruchomić?

Skrypt działa przez GitHub Action `sync-clean-one.yml` z trybem ręcznym (`workflow_dispatch`). Przy uruchomieniu należy podać następujące dane:

### 🔧 Parametry wejściowe

| Nazwa           | Wymagane | Opis |
|------------------|----------|------|
| `language`       | ✅       | Kod języka: `pl`, `en`, itp. |
| `article_id`     | ✅       | Unikalny identyfikator artykułu, np. `lego-science-review` |
| `title`          | ✅       | Pełny tytuł artykułu |
| `authors`        | ✅       | Lista autorów (oddzielone przecinkami) |
| `canonical_url`  | ✅       | Kanoniczny adres URL artykułu |
| `web_slug`       | ✅       | Końcowy segment adresu URL |
| `published`      | ✅       | Data publikacji, format: YYYY-MM-DD |
| `license`        | ❌       | Domyślnie: `CC BY-NC 4.0` |
| `status`         | ❌       | Domyślnie: `published` |

---

## 📁 Struktura katalogów (knowledge-base)

```bash
knowledge-base/
├── blog/
│   └── articles/
│       └── lego-science-review/
│           ├── en/
│           │   └── full.md
│           └── pl/
│               └── full.md
├── tools/
│   └── cleaner/
│       ├── clean_one.py
│       └── README.md  <-- ten plik
