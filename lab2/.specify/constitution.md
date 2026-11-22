# Constitution of the Project: Academic Ticket Generator

> **Status:** RATIFIED & ACTIVE  
> **Framework:** GitHub Spec Kit (Spec-Driven Development / SDD)  
> **Scope:** Desktop (Tkinter) & Web (Playwright/HTTP) Editions  
> **Core Objective:** Zero-defect, production-grade examination ticket generator complying with 100% of Acceptance Criteria (AC 1–9) under SOLID & Clean Code architecture.

---

## Article I: Non-Negotiable Architectural Laws (SOLID)

### Section 1. Single Responsibility Principle (SRP)
1. Every module, class, and function must have exactly one reason to change.
2. The domain model (`models.py`) knows nothing about Excel, Word, or UI frameworks.
3. Readers (`parsers.py`) only parse input files.
4. Storage (`storage.py`) only manages the results journal and file locking.
5. Service (`service.py`) coordinates business rules and idempotency.
6. Presenters and UI (`ui/`, `web/`) only handle display and user interaction.

### Section 2. Open/Closed Principle (OCP)
1. Core business logic must be open for extension, closed for modification.
2. Ticket selection strategies are interchangeable via `TicketSelectionStrategyProtocol` without altering `TicketService`.
3. Alternative storage adapters (In-Memory, SQLite, Database) can be plugged in without changing domain logic.
4. UI presentation layers (Tkinter Desktop, Web Server, CLI) operate through uniform protocol contracts.

### Section 3. Liskov Substitution Principle (LSP)
1. Subtypes or protocol implementations must be completely substitutable for their abstractions.
2. Any class implementing `StudentReaderProtocol` must guarantee safe handling of missing sheets without raising untyped crashes.
3. Any class implementing `ResultJournalStorage` must guarantee that previously written rows are never overwritten or mutated.

### Section 4. Interface Segregation Principle (ISP)
1. No client should be forced to depend on methods it does not use.
2. Protocols in `ports.py` are fine-grained:
   - `ResultJournalReaderProtocol` (querying past assignments) is segregated from `ResultJournalWriterProtocol` (appending new records).
   - `AlertNotifierProtocol` is segregated from `ResultPresenterProtocol`.

### Section 5. Dependency Inversion Principle (DIP)
1. High-level modules (`TicketService`, `MainWindow`, `TicketWebRouter`) must not depend on low-level modules (`openpyxl`, `docx`, `tkinter`). Both must depend on abstractions (`ports.py`).
2. Dependency injection is mandated at the Composition Root (`run.py`, `run_web.py`).

---

## Article II: Data Integrity & Idempotency Rules

### Section 1. The Immutability and Idempotency Mandate
1. **AC-4 & AC-8 Idempotency**: If a student $(Group, LastName, FirstName)$ has previously been assigned a ticket in `results.xlsx`, subsequent requests for the same student MUST return the exact ticket number from their very first assignment.
2. **AC-8 & AC-9 Chronological Audit**: Every generation event must immediately append a new record with timestamp and repeat flag (`"да"` / `"нет"`). Existing records are strictly immutable.
3. The domain record `ExamResult` must be an immutable frozen dataclass (`frozen=True`).

### Section 2. Defensive Storage & Concurrency
1. **AC-7 File Lock Handling**: If `results.xlsx` is open in Microsoft Excel or locked by an external process, the application MUST NOT crash.
2. The storage engine must catch `PermissionError` / OS sharing violations, invoke `LockHandlerProtocol` to offer retry/abort, and preserve user state.

---

## Article III: Production & Engineering Standards

### Section 1. Zero-Defect Testing & Verification
1. Every acceptance criterion must be covered by automated tests (`pytest`).
2. Dual-level verification:
   - **Unit & Architectural Tests**: Protocol adherence, mock isolation, edge cases (empty groups, defective tickets, file locking).
   - **End-to-End Tests**: Playwright browser automation verifying actual user interactions, modal dismissal via `ESC`, theme switching, and live DOM state.

### Section 2. Spec-Driven Development (SDD)
1. No code is written or altered without an approved specification in `.specify/specs/`.
2. All technical plans must precede implementation in `.specify/plan.md`.
3. Tasks in `.specify/tasks.md` track completion against acceptance criteria.
