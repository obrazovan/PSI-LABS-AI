# Prompt Engineering Kit (Master Prompts for Copilot & LLMs)

> **Origin:** Required by Step 1 of `Workshop_Plan_AI_Development.pdf`  
> **Standard:** GitHub Spec Kit / Prompt Engineering Artifacts

---

## 1. System Architect Prompt (Specification & SOLID Hexagonal Design)

```markdown
You are a Principal Software Architect and Python Engineering Expert.
We are building a robust Academic Examination Ticket Generator complying with strict university examination requirements:
1. Domain Rules:
   - Input: `students.xlsx` (one sheet per academic group, columns: Last Name, First Name) and `tickets.docx` (header: 'Билет N', followed by numbered questions 1, 2, 3...).
   - Output: `results.xlsx` (columns: Group, Last Name, First Name, Ticket Number, Timestamp, Repeat ('да'/'нет')).
   - Idempotency: When a student is selected repeatedly, always assign the identical ticket number from their first attempt, appending a new record with 'да' in the Repeat column.
   - Fault Tolerance: If results.xlsx is locked by Excel, do not crash; notify the user and handle retries. If a ticket has fewer than 3 questions, skip it with a log warning.
2. Architecture Mandate:
   - Strictly follow SOLID and Clean Code.
   - Hexagonal / Ports & Adapters architecture: Define fine-grained `@runtime_checkable` `typing.Protocol` interfaces in `ports.py`.
   - Domain models in `models.py` must be immutable dataclasses with zero external framework dependencies.
   - The application service in `service.py` must depend ONLY on protocols.
Provide the complete Python port definitions, custom exception hierarchy, and domain models.
```

---

## 2. Code Generation Prompt (Hexagonal Adapters & Desktop UI)

```markdown
Implement the infrastructure adapters and desktop presentation layer:
1. `ExcelStudentReader`: Reads groups and students from `students.xlsx` using `openpyxl`. Return empty lists on empty sheets without exceptions.
2. `DocxTicketParser`: Parses `tickets.docx` using `python-docx`. Skip malformed tickets with < 3 questions.
3. `ResultJournalStorage`: Appends rows to `results.xlsx`, applies styling via `ExcelJournalStyler`, and handles file locks via `LockHandlerProtocol`.
4. `MainWindow` (Tkinter): Implements dual selection logic (Group -> Student -> Enable Generate button). Pressing ESC closes the result dialog without terminating the app.
All code must be strictly typed, well-documented, and error-handled.
```

---

## 3. Web Edition & Playwright E2E Prompt

```markdown
Design and implement a modern Web Edition and Playwright E2E test suite:
1. Build a pure standard-library HTTP server and REST router (`TicketWebRouter`) providing endpoints:
   - `GET /api/init`: Source files validation and group list.
   - `GET /api/students?group=...`: Student list for selected group.
   - `POST /api/generate`: Ticket assignment with idempotency and Excel journaling.
   - `GET /api/history`: Recent exam results.
2. Build an automated browser runner using Playwright (`PlaywrightBrowserRunner`) with fallback detection.
3. Create an E2E test suite using the Page Object Model (POM) pattern verifying page loading, empty group handling, ticket generation, modal ESC dismissal, and theme switching.
```

---

## 4. Production Hardening & Unique Academic Bureau UI Prompt

```markdown
Refactor the UI away from generic AI/SaaS templates (no generic purple gradients or blurry glass cards).
Create an authentic, tactile "Academic Examination Registrar" interface:
- High-end archival paper aesthetic (warm ivory / eggshell background, deep oxford navy ink, sepia borders, antique gold accents).
- Physical examination ticket metaphor: Perforated tear-off stub line, authentic university watermark seal, serial number barcode, and crimson duplicate stamp ("ПОВТОРНАЯ ВЫДАЧА • ДУБЛИКАТ").
- Production features: Printable A4 examination sheet (`@media print`), live source status indicators, interactive archival ledger, and subtle Web Audio feedback.
```
