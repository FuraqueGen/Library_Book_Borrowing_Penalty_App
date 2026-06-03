# Library_Book_Borrowing_Penalty_App
An automated management system built with Python to monitor borrowed books, calculate penalties, and manage borrower deactivations.

# Application Features


## 1. Account Management & Capacity Control
 * **Register Account (register_account):** Registers a new borrower. The system ensures that the name field cannot be blank and prevents duplicate entries in the database (*Unique Name Enforcement*).
 * **Contact Number Validation:** Strictly filters input to ensure it contains numbers only, consists of exactly 11 digits, and strictly begins with the Philippine mobile prefix "09".
 * **Delete Account:** Allows the deletion of a borrower account, complete with a confirmation prompt (y/n) before permanently removing the record from the system.
 * **Maximum Account Limit:** Caps the database at a maximum of **1,000 accounts** (MAX_ACCOUNTS).

## 2. Borrow Book Management
 * **Borrow Book (borrow_book_logic):** Processes the issuance of a book to an active borrower. The system automatically assigns the *Borrow Date* (current date) and forces the user to set a *Due Date* strictly within a **3 to 5-day range**.
 * **Borrowing History Dashboard:** Displays a comprehensive logs list of currently and previously borrowed books within the borrower's profile, including *Title*, *Date/Time Borrowed*, *Due Date*, *Condition*, and *Status*.
 * **Clear History Option:** Allows the user to clear or purge completed transaction logs (status != "Returned") to keep their profile history clean.

## 3. Book Return & Status Processing (return_book_logic)
 * **Return (Good Condition):** Marks the book as *Returned* and terminates active tracking.
 * **Return (Damaged):** Marks the book as returned but flags it as *Damaged* for penalty calculation purposes.
 * **Declare Lost Book:** Initiates a **3-day search grace period** when a book is officially declared missing by the borrower.
 * **Lost Book Recovery Verification:** If a lost book is successfully recovered, the system allows updating its status to *Returned* while recording the exact number of days spent searching (0–3 days) and evaluating if it sustained any damages upon recovery.

## 4. Mathematical Penalty Calculation Engine (BookPenaltyProcessor)
The system automatically calculates account suspension periods (total_days) using the following precise formulas:
 * **Not Returned (Good + Late):** 
 * **Not Returned (Damaged):** 
 * **Not Returned (Lost - Beyond 3 Days):** 
 * **Returned (Damaged):** 
 * **Returned (Good but Late):** 
 * **Lost Then Returned:** 

## 5. Account Deactivation & Countdown System
 * **Automatic Account Blocking:** If a borrower accumulates a calculated penalty higher than zero, the system automatically logs a penalty_start_date and changes the account status to **DEACTIVATED**. This locks the account, blocking them from accessing their profile or borrowing books.
 * **Dynamic Countdown Display:** Displays the remaining duration of the account penalty dynamically in an Xd Xh Xm or Xh Xm Xs format based on the remaining seconds.
 * **Automatic Reactivation:** Once the penalty timer hits zero, the system completely resets the borrower's account back to an *Active* state and normalizes their book records.

## 6. Search, Filter, & Administrative Tools
 * **Search Borrowers:** Locates registered borrower accounts using a case-insensitive name keyword search (e.g., searching for "juan").
 * **Filter Deactivated Profiles:** A dedicated administrative utility that filters and isolates only the accounts currently serving a deactivation penalty.
 * **Critical Alert List:** A rapid-glance dashboard for librarians displaying the names, contact details, and remaining deactivation times of all flagged accounts.
 * **Invoked Manual Override:** An administrative override feature where typing a borrower's exact name allows the system to instantly wipe all penalties, mark books as "Good" and "Returned", and immediately restore the account to an "Active" state.

## 7. Data Persistence & OOP Architecture
 * **JSON Storage Repository:** Automatically saves (save()) and loads (load()) the entire application state into a library_data.json file, ensuring complete anti-data loss protection even after a system restart.
 * **OOP Compliance:** Fully adheres to **Abstraction** and **Inheritance** (via Penalty and StorageRepository classes), **Encapsulation** (via protected/private attributes like _title, _name), and **Polymorphism** (implemented through custom overrides in calculate_deactivation_days).


# Quality Assurance (Automated Testing)
This project has undergone **27 automated test cases** using the `pytest` framework to ensure the system is reliable and bug-free.

# Test Suites:
1. **`test_library.py` (16 Tests Passed):** Focuses on penalty logic, timestamp flow, and handling of corrupt data or negative values.
2. **`test_library_2.py` (11 Tests Passed):** Verifies system flow, including registration limits, JSON saving/loading, and statistical report accuracy.

# Project Structure
* `main_library.py` - The primary source code of the application.
* `test_library.py` & `test_library_2.py` - Automated test files.
* `library_data.json` - Local database file.
* `README.md` - Project documentation.

# The Team (BSIT 1-2)

* **Technical Lead & Architect:** Generous Furaque  
  *Responsible for system architecture, backend implementation, and the development of the 27 automated test suites.*

* **Technical QA Analyst & Data Consultant:** Jhon Steeven G. Vargas  
  *Responsible for verifying data persistence logic (JSON loading/saving), ensuring system reliability, and conducting extensive feature testing.*

* **Technical Documentation Specialist:** Jules G. Gardon  
  *Responsible for organizing requirements, technical manual production, and ensuring all documentation standards are met.*
