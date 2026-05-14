# Library_Book_Borrowing_Penalty_App
A Python-based Library Management Application featuring an automated penalty calculation engine, real-time account deactivation tracking, and JSON data persistence for CC 103.

# Application Features
**1. Account & Security Management**
* **User Registration:** The application allows for the seamless creation of new borrower profiles.
 * **Strict Input Validation:** To ensure data integrity, the application prevents empty name fields, blocks duplicate registrations, and enforces a strict 11-digit numeric format for contact numbers starting with "09".
 * **Account Capacity Management:** The application includes a memory-efficient limit of 1,000 total accounts.
 * **Account Deletion:** Administrators have the authority to permanently remove borrower profiles from the database.
 * **Administrative Manual Override:** A specialized feature allows administrators to manually lift an account's deactivation even if the penalty period has not yet expired.
# **2. Core Library Operations**
 * **Regulated Borrowing Process:** The application automatically sets due dates restricted to a 3–5 day window and strictly prohibits borrowing for accounts with active deactivation status.
 * **Dynamic Return & Update Module:** Users can update book statuses to "Good," "Damaged," or "Lost," which triggers the corresponding application logic.
 * **History Management:** The application provides an option to clear "Returned" book history to maintain a clean and organized user profile.
# **3. Advanced Penalty Engine**
 * **Automated Penalty Calculation:** The engine automatically computes "Deactivation Days" based on return conditions:
   * **Good Condition (Overdue):** 2 base days + the total number of days late.
   * **Damaged Condition:** 4 base days + the total number of days late.
   * **Lost Items:** 5 base days + the total number of days late.
 * **3-Day Search Grace Period:** A unique feature providing borrowers with a 3-day window to locate lost books before heavy penalties are officially applied.
 * **Lost-to-Returned Tracking:** The application monitors the duration taken to recover lost items and assesses any additional damage upon return.
 * **Real-time Deactivation Countdown:** Each profile displays a live countdown of remaining penalty time in days, hours, minutes, and seconds.
# **4. Administrative Tools & Data Integrity**
 * **JSON Data Persistence:** The application utilizes library_data.json to ensure all records and timestamps are preserved even if the application or device restarts.
 * **Advanced Search & Filtering:** * **Name Search:** Quick lookup of borrowers using specific keywords.
   * **Deactivation Filter:** A dedicated view that isolates and displays only the accounts currently under penalty.
 * **Critical Alert Dashboard:** An administrative view designed to immediately flag borrowers with active penalties or violations.
 * **Statistical Reporting Summary:** Generates real-time overviews of total registered profiles, active book loans, and the total number of blocked accounts.

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
