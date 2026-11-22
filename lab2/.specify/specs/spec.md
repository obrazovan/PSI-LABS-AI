# Feature Specification: Examination Ticket Generator System

> **Spec Version:** 2.1.0  
> **Status:** APPROVED  
> **Traceability:** Лабораторная работа №2 (ТЗ) + Web Edition & Playwright Extensions

---

## 1. Domain Overview & Problem Statement

In academic institutions, distributing examination tickets requires strict fairness, idempotency, fraud prevention, and complete auditability:
1. **Fairness**: Tickets must be randomly and uniformly distributed among students who have not yet taken an exam.
2. **Idempotency & Fraud Prevention**: A student who draws a ticket must not be allowed to "re-roll" or change their assigned questions. If drawn again, the exact same ticket must be re-issued with an explicit repeat marker.
3. **Auditability**: Every attempt, whether initial or repeated, must be logged with an immutable timestamp in a persistent journal (`results.xlsx`).

---

## 2. User Stories & Acceptance Criteria

### US-1: Group and Student Discovery
**As an** Examiner,  
**I want** the system to load academic groups from `students.xlsx` and dynamically populate student lists,  
**So that** I can accurately select the student taking the exam.

#### Acceptance Criteria
* **AC-1 (Sheet to Group Mapping):**  
  *Given* `students.xlsx` contains sheets named after groups (e.g., `ИВТ-21`, `ПИ-22`, `ПУСТАЯ-00`),  
  *When* the application starts,  
  *Then* the group dropdown is populated with all valid sheet names.
* **AC-2 (Dual Selection Prerequisite):**  
  *Given* the application is opened,  
  *When* either no group or no student is selected,  
  *Then* the "Generate Ticket" action MUST be disabled.
* **AC-2b (Empty Group Handling):**  
  *Given* a group has no student rows (e.g., `ПУСТАЯ-00`),  
  *When* the examiner selects this group,  
  *Then* the student list becomes empty, the generate action remains disabled, and no exception or crash occurs.

---

### US-2: Ticket Assignment & Idempotency
**As an** Examiner,  
**I want** to assign a random ticket to a new student and retrieve the existing ticket for a returning student,  
**So that** tickets cannot be manipulated and examination fairness is preserved.

#### Acceptance Criteria
* **AC-3 (Random Assignment with Valid Questions):**  
  *Given* a student who has not previously taken the exam,  
  *When* the examiner generates a ticket,  
  *Then* a ticket is selected randomly from `tickets.docx`, and the UI displays "Ваш билет № N" along with exactly three distinct questions.
* **AC-4 (Strict Idempotency):**  
  *Given* student $S$ was previously assigned Ticket № $K$,  
  *When* the examiner generates a ticket for student $S$ again,  
  *Then* the system MUST return Ticket № $K$, never generating a new ticket number.
* **AC-5 (ESC Key Dismissal):**  
  *Given* the ticket result dialog/modal is open,  
  *When* the user presses the `ESC` key,  
  *Then* the modal dialog closes, the application does NOT exit, and the form returns to the student selection state.

---

### US-3: Journaling & Persistence
**As a** Department Head or Auditor,  
**I want** all exam ticket events recorded immediately in `results.xlsx`,  
**So that** an untampered historical log of the entire session exists.

#### Acceptance Criteria
* **AC-6 (Immediate Persistence):**  
  *Given* a ticket generation action,  
  *When* the ticket is assigned,  
  *Then* a new row is appended to `results.xlsx` immediately, without waiting for the application to close.
* **AC-7 (File Lock Resilience):**  
  *Given* `results.xlsx` is open in Microsoft Excel or locked by an external process,  
  *When* the system attempts to save a result,  
  *Then* the application MUST NOT crash; it must notify the user, provide a retry mechanism, and safely resume once the lock is released.
* **AC-8 (Chronological Non-Destructive Log):**  
  *Given* a repeated generation for a student,  
  *When* recorded in `results.xlsx`,  
  *Then* existing rows remain untouched, a new row is appended to the bottom, the ticket number matches the student's first record, and the "Повтор" column is set to `"да"`.
* **AC-9 (Complete History Reconstruction):**  
  *Given* `results.xlsx`,  
  *When* parsed sequentially,  
  *Then* the complete chronological history of all examinations (both initial and duplicates) can be reconstructed verbatim.

---

## 3. Data Schemas

### 3.1 Input: `students.xlsx`
* One worksheet per group; worksheet title = Group Name.
* Row 1: Headers (`Фамилия`, `Имя`).
* Rows 2+: Student records ($A$: Last Name, $B$: First Name).

### 3.2 Input: `tickets.docx`
* Format:
  ```text
  Билет N
  1. Текст вопроса 1
  2. Текст вопроса 2
  3. Текст вопроса 3
  ```
* Defective tickets ($< 3$ questions or unparseable headers) must be logged as warnings and skipped, allowing valid tickets to remain functional.

### 3.3 Output: `results.xlsx`
| Column A | Column B | Column C | Column D | Column E | Column F |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Группа** | **Фамилия** | **Имя** | **Номер билета** | **Дата и время** | **Повтор (да/нет)** |

### 3.4 REST API Contracts (Web Edition)
* `GET /api/init` -> Returns `{ ready: bool, groups: string[], groups_count: int, tickets_count: int, missing_sources: string[] }`
* `GET /api/students?group={name}` -> Returns `{ group: string, students: [{ group, last_name, first_name, full_name }] }`
* `POST /api/generate` -> Body `{ group, last_name, first_name }` -> Returns `{ ticket: { number, questions }, result: { group, last_name, first_name, ticket_number, is_repeat, timestamp } }`
* `GET /api/history` -> Returns `{ count: int, history: ExamResult[] }`
