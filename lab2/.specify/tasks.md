# Task Traceability & Implementation Matrix

> **Traceability Standard:** GitHub Spec Kit  
> **Status:** ALL CORE TASKS COMPLETED & VERIFIED (52/52 Tests Passing)

---

## Task Breakdown

### Phase 1: Pure Domain & Model Layer (Completed)
- [x] **T-1.1**: Define `Student` dataclass with whitespace normalization (`models.py`).
- [x] **T-1.2**: Define `Ticket` dataclass requiring $>= 3$ questions and positive ticket number (`models.py`).
- [x] **T-1.3**: Define immutable `ExamResult` dataclass (`frozen=True`) with formatted row representation (`models.py`).
- [x] **T-1.4**: Define `InitializationReport` decoupling infrastructure scan results from UI (`models.py`).
- [x] **T-1.5**: Author unit tests for all domain models (`tests/test_models.py`).

### Phase 2: SOLID Interfaces & Custom Exceptions (Completed)
- [x] **T-2.1**: Define fine-grained `@runtime_checkable` `Protocol` interfaces (`ports.py`).
- [x] **T-2.2**: Define domain exception hierarchy: `SourceNotFoundError`, `NoTicketsAvailableError`, `StorageLockedError` (`exceptions.py`).
- [x] **T-2.3**: Author SOLID conformance unit tests verifying protocol compliance (`tests/test_solid.py`).

### Phase 3: Infrastructure Adapters (Completed)
- [x] **T-3.1**: Implement `ExcelStudentReader` with graceful handling of empty groups (`parsers.py`).
- [x] **T-3.2**: Implement `DocxTicketParser` skipping malformed tickets ($< 3$ questions) (`parsers.py`).
- [x] **T-3.3**: Implement `ResultJournalStorage` with immediate appending and styling via `ExcelJournalStyler` (`storage.py`).
- [x] **T-3.4**: Implement `DelegatingLockHandler` for resilient file lock handling (`storage.py`).
- [x] **T-3.5**: Author parser and storage test suites (`tests/test_parsers.py`, `tests/test_storage.py`).

### Phase 4: Application Service & Idempotency Orchestration (Completed)
- [x] **T-4.1**: Implement `TicketService` strictly depending on protocols (`service.py`).
- [x] **T-4.2**: Implement `RandomTicketSelector` strategy (`service.py`).
- [x] **T-4.3**: Enforce strict idempotency: identical ticket number returned on duplicate student selection (`service.py`).
- [x] **T-4.4**: Author service test suite (`tests/test_service.py`).

### Phase 5: Desktop Presentation Layer (Completed)
- [x] **T-5.1**: Implement `MainWindow` using `TkResultPresenter` and `TkAlertNotifier` (`ui/main_window.py`).
- [x] **T-5.2**: Implement `ResultDialog` with `ESC` key binding (`ui/result_dialog.py`).
- [x] **T-5.3**: Author desktop UI interaction and state test suite (`tests/test_ui_logic.py`).

### Phase 6: Web Edition & Playwright E2E Automation (Completed)
- [x] **T-6.1**: Implement REST API & static file router `TicketWebRouter` (`web/router.py`).
- [x] **T-6.2**: Implement `TicketWebServer` on Python's built-in `http.server` (`web/server.py`).
- [x] **T-6.3**: Implement `PlaywrightBrowserRunner` with auto-detection of Chromium / Edge (`web/playwright_runner.py`).
- [x] **T-6.4**: Build Web frontend (`web/static/index.html`, `styles.css`, `app.js`).
- [x] **T-6.5**: Implement Page Object Model `TicketPageObject` (`tests/test_web_e2e_playwright.py`).
- [x] **T-6.6**: Author Playwright E2E test suite (`tests/test_web_e2e_playwright.py`).

### Phase 7: Production Hardening & Bespoke Academic UI (In Progress)
- [x] **T-7.1**: Setup GitHub Spec Kit documentation (`.specify/`).
- [ ] **T-7.2**: Implement typed `AppConfig` (`src/ticket_gui/config.py`).
- [ ] **T-7.3**: Implement structured production logging (`src/ticket_gui/logging_config.py`).
- [ ] **T-7.4**: Add `py.typed`, `Makefile`, `Dockerfile`, `docker-compose.yml`, and CI workflow (`.github/workflows/ci.yml`).
- [ ] **T-7.5**: Redesign Web UI into a bespoke, authentic "Academic Examination Registrar" aesthetic (tactile paper ticket, official watermark seal, barcode, duplicate rubber stamp, print-to-PDF stylesheet, sound effects).
- [ ] **T-7.6**: Verify 100% test pass on all suites.
