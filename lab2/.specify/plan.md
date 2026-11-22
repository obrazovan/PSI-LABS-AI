# Architectural Blueprint & Technical Plan

> **Framework:** Hexagonal Architecture (Ports and Adapters)  
> **Target Runtimes:** Python 3.12+ (tested up to 3.14.2)  
> **Adherence:** SOLID, Clean Code, Clean Architecture

---

## 1. System Architecture Overview

The system is organized into concentric decoupled rings:

```mermaid
flowchart TD
    subgraph UI_Adapters ["Presentation / Adapters (Outermost Ring)"]
        A1["Tkinter Desktop GUI<br/>(MainWindow, ResultDialog)"]
        A2["Web HTTP & REST Server<br/>(TicketWebServer, TicketWebRouter)"]
        A3["Playwright Browser Runner<br/>(E2E Automation & Client Runner)"]
    end

    subgraph Ports_Layer ["Ports / Abstractions (ports.py)"]
        P1["StudentReaderProtocol"]
        P2["TicketParserProtocol"]
        P3["ResultStorageProtocol"]
        P4["TicketSelectionStrategyProtocol"]
        P5["AlertNotifierProtocol"]
        P6["ResultPresenterProtocol"]
    end

    subgraph Domain_Service ["Application / Service Layer"]
        S1["TicketService<br/>(Orchestration, Idempotency)"]
        S2["RandomTicketSelector"]
    end

    subgraph Core_Domain ["Pure Domain Core (models.py)"]
        M1["Student (dataclass)"]
        M2["Ticket (dataclass)"]
        M3["ExamResult (frozen dataclass)"]
        M4["InitializationReport"]
    end

    subgraph Infrastructure ["Infrastructure Adapters (storage.py, parsers.py)"]
        I1["ExcelStudentReader (openpyxl)"]
        I2["DocxTicketParser (python-docx)"]
        I3["ResultJournalStorage (openpyxl)"]
        I4["ExcelJournalStyler"]
        I5["DelegatingLockHandler"]
    end

    A1 --> P5
    A1 --> P6
    A2 --> S1
    A3 --> A2
    S1 --> P1
    S1 --> P2
    S1 --> P3
    S1 --> P4
    I1 -.-> P1
    I2 -.-> P2
    I3 -.-> P3
    S1 --> Core_Domain
    Infrastructure --> Core_Domain
```

---

## 2. Component Protocols & Responsibility Matrix

| Protocol | Responsibility | Concrete Implementation |
| :--- | :--- | :--- |
| `StudentReaderProtocol` | Read worksheets and student lists | `ExcelStudentReader` (openpyxl) |
| `TicketParserProtocol` | Parse ticket numbers & questions | `DocxTicketParser` (python-docx) |
| `ResultStorageProtocol` | Query history & append exam records | `ResultJournalStorage` (openpyxl) |
| `JournalStylerProtocol` | Apply corporate / academic cell styles | `ExcelJournalStyler` |
| `LockHandlerProtocol` | Resolve file access permission locks | `DelegatingLockHandler` / `InteractiveLockHandler` |
| `TicketSelectionStrategyProtocol` | Select ticket among valid candidates | `RandomTicketSelector` |
| `TicketServiceProtocol` | Business logic & idempotency | `TicketService` |
| `ResultPresenterProtocol` | Render ticket results dialog/modal | `TkResultPresenter` / `TicketWebRouter` |
| `AlertNotifierProtocol` | Alert user regarding errors/warnings | `TkAlertNotifier` / Web Alert Banner |

---

## 3. Sequence: Ticket Assignment & Persistence

```mermaid
sequenceDiagram
    autonumber
    actor User as Examiner
    participant View as Web UI / Desktop View
    participant Service as TicketService
    participant Storage as ResultJournalStorage
    participant File as results.xlsx

    User->>View: Select Group & Student
    View->>View: Validate dual selection (AC-2)
    User->>View: Click "Generate Ticket"
    View->>Service: assign_ticket(student)
    
    Service->>Storage: get_first_ticket_for_student(group, last, first)
    alt Student already in journal (AC-4 Idempotency)
        Storage-->>Service: Return previous ticket_number
        Note over Service: is_repeat = True
    else New Student
        Storage-->>Service: None
        Service->>Service: RandomTicketSelector.select(available_tickets)
        Note over Service: is_repeat = False
    end

    Service->>Storage: append_result(ExamResult)
    Storage->>File: Write row & apply styles
    alt File Locked in Excel (AC-7)
        File-->>Storage: PermissionError
        Storage->>Storage: LockHandler.handle_locked()
    end
    File-->>Storage: Save OK
    Storage-->>Service: Success
    Service-->>View: (Ticket, ExamResult)
    View->>User: Display Ticket & 3 Questions (AC-3, AC-5)
```

---

## 4. Production Engineering Protocols

1. **Configuration Protocol**: Typed `AppConfig` with environment variable overrides.
2. **Logging Protocol**: Structured standard logging with level filtering.
3. **Packaging Protocol**: `py.typed` marker for static typing checkers.
4. **Resilience Protocol**: Automatic exponential backoff retries on file sharing locks.
