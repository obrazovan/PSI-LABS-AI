# Лабораторная работа №2: Бюро Экзаменационных Билетов (Desktop GUI & Bespoke Web Edition)

> **Стандарт разработки:** GitHub Spec Kit (Spec-Driven Development / SDD)  
> **Архитектура:** Hexagonal (Ports & Adapters), SOLID, Clean Code, 12-Factor App Config  
> **Тестовое покрытие:** 100% (55 автоматизированных тестов: Unit, Architecture, Integration, Playwright E2E)

Кроссплатформенная production-ready система для распределения экзаменационных билетов строгой отчётности с гарантией абсолютной идемпотентности, защитой от подделки и фиксацией в журнале Microsoft Excel (`results.xlsx`).

---

## 🏛️ Архитектура проекта и Spec Kit

Проект разработан по методологии **Spec-Driven Development (SDD)** с использованием **GitHub Spec Kit** (`.specify/`):

```text
lab2/
├── .specify/                            # Спецификационный комплект (GitHub Spec Kit)
│   ├── constitution.md                  # Незыблемые архитектурные законы (SOLID, Clean Code, Идемпотентность)
│   ├── specs/
│   │   └── spec.md                      # Полная спецификация требований и сценарии Gherkin (AC 1–9)
│   ├── plan.md                          # Архитектурный план, UML-диаграммы и протоколы
│   ├── tasks.md                         # Матрица задач и трассировки реализации
│   └── prompts/
│       └── prompt_engineering_kit.md    # Мастер-промпты для LLM и Copilot (согласно Шагу 1 плана воркшопа)
├── .github/
│   └── workflows/
│       └── ci.yml                       # CI/CD пайплайн (GitHub Actions: multi-OS, multi-Python, Playwright)
├── src/
│   └── ticket_gui/
│       ├── config.py                    # Конфигурация приложения (AppConfig, 12-Factor App)
│       ├── logging_config.py            # Структурированное логирование для продакшена
│       ├── py.typed                     # Маркер статической типизации (PEP 561)
│       ├── ports.py                     # @runtime_checkable Protocol-интерфейсы (DIP, ISP)
│       ├── exceptions.py                # Изолированная иерархия доменных исключений
│       ├── models.py                    # Чистые неизменяемые модели (Student, Ticket, ExamResult)
│       ├── parsers.py                   # Адаптеры чтения: ExcelStudentReader и DocxTicketParser
│       ├── storage.py                   # ResultJournalStorage, ExcelJournalStyler, DelegatingLockHandler
│       ├── service.py                   # TicketService и стратегия RandomTicketSelector
│       ├── ui/                          # Десктопный адаптер (Tkinter / ttk)
│       │   ├── main_window.py
│       │   ├── result_dialog.py
│       │   └── presenters.py
│       └── web/                         # Веб-адаптер (Bespoke Academic Web Edition)
│           ├── router.py                # TicketWebRouter (REST API + static)
│           ├── server.py                # TicketWebServer (http.server с авто-закрытием сокетов)
│           ├── playwright_runner.py     # PlaywrightBrowserRunner (авто-браузер)
│           └── static/                  # Уникальный интерфейс "Академическая Комиссия"
│               ├── index.html           # Семантическая разметка бланка строгой отчётности
│               ├── styles.css           # Архивный пергамент, гильош, перфорация, печать A4
│               └── app.js               # Web Audio тактильность, фильтрация, hotkeys
├── tests/
│   ├── test_config.py                   # Тесты конфигурации и переменных окружения
│   ├── test_models.py                   # Тесты доменных моделей
│   ├── test_parsers.py                  # Тесты чтения Excel и Word
│   ├── test_storage.py                  # Тесты хранилища и блокировок
│   ├── test_service.py                  # Тесты бизнес-логики и идемпотентности
│   ├── test_solid.py                    # Тесты соблюдения принципов SOLID
│   ├── test_ui_logic.py                 # Тесты десктопного UI и клавиши ESC
│   ├── test_web_router.py               # Тесты REST API и статических файлов
│   └── test_web_e2e_playwright.py       # E2E тесты веб-интерфейса (Page Object Model)
├── Dockerfile                           # Контейнеризация для продакшена
├── docker-compose.yml                   # Запуск контейнера со смонтированными томами
├── Makefile                             # Стандартные команды разработчика
├── pyproject.toml                       # Метаданные пакета, зависимости, ruff и mypy
├── requirements.txt                     # Фиксация библиотек
├── run.py                               # Запуск десктопного GUI
└── run_web.py                           # Запуск веб-сервера и Playwright
```

---

## 🎨 Уникальный дизайн веб-интерфейса (No AI-Template Cliché)

Вместо стереотипных фиолетовых SaaS-градиентов и размытых неоновых кружков реализована **аутентичная эстетика Государственной Экзаменационной Комиссии**:

1. **Цветовая система «Архивный Пергамент» и «Ночной Кабинет»**:
   * *Светлая тема:* Теплый тон бумажного бланка (`#fdfcf9`), королевский оксфордский синий (`#1e3a8a`), сепия и античное золото (`#b45309`).
   * *Тёмная тема:* Ночной профессорский кабинет (`#0b0e14`, `#121720`) с янтарным тиснением.
2. **Физический экзаменационный билет строгой отчётности**:
   * Линия перфорации с реалистичными полукруглыми вырезами отрывного корешка.
   * Водяной знак академической печати (*"EXAMINA • ORDO • VERITAS"*).
   * Защитная гильошированная микро-рамка и штрихкод верификации документа.
   * **Аутентичный резиновый штамп «ДУБЛИКАТ / ПОВТОРНАЯ ВЫДАЧА»** в багровых чернилах с реалистичным углом наклона (-10°) при повторном назначении.
3. **Функция официальной печати (`@media print`)**:
   * Нажатие кнопки **«Распечатать билет»** (или клавиша `[P]`) форматирует билет на чистый лист A4 для экзамена со строками для письменных ответов студента и подписей экзаменатора.
4. **Тактильный звук (Web Audio API)**:
   * Мягкий синтезированный звук постановки штампа/шелеста бумаги при формировании билета (без внешних mp3-файлов, с возможностью отключения `[M]`).
5. **Интерактивный архивный реестр**:
   * Живая таблица всех выданных билетов с мгновенным поиском по студентам и группам.
6. **Горячие клавиши (Keyboard HUD)**:
   * `[1]` — выбор группы, `[2]` — выбор студента, `[Enter]` — выдать билет, `[Esc]` — закрыть билет, `[P]` — печать, `[D]` — смена темы, `[M]` — звук.

---

## 📋 Таблица соответствия критериям ТЗ (100% Complete)

| № | Критерий приёмки ТЗ | Реализация | Тесты |
|---|---|---|:---:|
| **1** | Выбор группы $\to$ список студентов листа | `ExcelStudentReader.load_groups()` / `load_students_for_group()` | `test_parsers.py` |
| **2** | Кнопка активна только при обоих выборах | Валидация в UI (Tkinter и Web) с блокировкой кнопки | `test_ui_logic.py`, `test_web_e2e_playwright.py` |
| **3** | Билет и 3 вопроса из файла корректны | `DocxTicketParser` с фильтрацией дефектных билетов | `test_parsers.py`, `test_models.py` |
| **4** | Повторный выбор возвращает тот же номер билета | Гарантированная идемпотентность в `TicketService` | `test_service.py`, `test_web_e2e_playwright.py` |
| **5** | ESC закрывает окно результата без завершения | Обработчики клавиши Escape в Tkinter и Web | `test_ui_logic.py`, `test_web_e2e_playwright.py` |
| **6** | Строка в `results.xlsx` пишется сразу | Мгновенная запись через `ResultJournalStorage` | `test_storage.py`, `test_service.py` |
| **7** | Заблокированный файл не роняет приложение | Обработка `PermissionError` с повтором попытки | `test_storage.py`, `test_solid.py` |
| **8** | Повтор добавляет строку в конец с пометкой «да» | Добавление без перезаписи с флагом `is_repeat=True` | `test_service.py`, `test_storage.py` |
| **9** | Полная хронологическая история всех генераций | Последовательный журнал с датой и временем | `test_service.py` |

---

## 🚀 Запуск и команды разработчика

### Использование Makefile:
```bash
make install       # Установка зависимостей и браузера Chromium
make test          # Запуск полного набора из 55 тестов
make test-e2e      # Запуск только Playwright E2E тестов
make run-web       # Запуск веб-сервера (http://127.0.0.1:8000)
make run-browser   # Запуск веб-сервера с автоматическим открытием браузера
make run-desktop   # Запуск десктопного Tkinter приложения
```

### Запуск через Python напрямую:

1. **Веб-версия с автоматическим открытием браузера:**
   ```powershell
   python run_web.py --browser
   ```

2. **Веб-сервер для работы в обычном браузере:**
   ```powershell
   python run_web.py
   # Откройте в браузере: http://127.0.0.1:8000
   ```

3. **Десктопное приложение (Tkinter):**
   ```powershell
   python run.py
   ```

4. **Запуск через Docker Compose:**
   ```bash
   docker-compose up --build
   ```
