from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import os
import json

# =====================================================================
# I. INTERFACES & ABSTRACT BASE CLASSES (Loose Coupling & Dependency Inversion)
# =====================================================================

class Penalty(ABC):
    @abstractmethod
    def calculate_deactivation_days(self, book) -> int:
        pass


class StorageRepository(ABC):
    """Interface for Data Saving/Loading (Interface Segregation / Dependency Inversion)"""
    @abstractmethod
    def save(self, accounts: list):
        pass

    @abstractmethod
    def load(self) -> list:
        pass

# =====================================================================
# II. STRATEGY PATTERN FOR DEACTIVATION PENALTIES (Polymorphism & Open/Closed)
# =====================================================================

class BookPenaltyProcessor(Penalty):
    """Responsible solely for the calculation of deactivation days (Single Responsibility)"""
    def calculate_deactivation_days(self, book) -> int:
        total_days = 0
        overdue_days = book.get_overdue_days()
        
        # CASE A: BOOK HAS NOT BEEN RETURNED
        if book.status == "Not returned":
            if book.condition == "Good" and overdue_days > 0:
                total_days = 2 + overdue_days
            elif book.condition == "Damaged":
                total_days = 4 + overdue_days
            elif book.condition == "Lost":
                if book.lost_declared_date:
                    days_since_lost = (datetime.now() - book.lost_declared_date).days
                    if days_since_lost > 3:
                        total_days = 5 + overdue_days
                    else:
                        total_days = 0
                else:
                    total_days = 5 + overdue_days

        # CASE B: BOOK HAS BEEN RETURNED (Residual Penalty Lock)
        elif book.status == "Returned":
            if book.condition == "Damaged":
                late_days = book.final_overdue_days if hasattr(book, 'final_overdue_days') else 0
                total_days = 4 + late_days
            elif book.condition == "Lost_Then_Returned":
                chance_days_used = book.lost_resolved_duration if hasattr(book, 'lost_resolved_duration') else 0
                late_days = book.final_overdue_days if hasattr(book, 'final_overdue_days') else 0
                damaged_add = 4 if book.was_damaged_upon_return else 0
                total_days = 5 + chance_days_used + late_days + damaged_add
            elif book.condition == "Good":
                late_days = book.final_overdue_days if hasattr(book, 'final_overdue_days') else 0
                if late_days > 0:
                    total_days = 2 + late_days

        return total_days

# =====================================================================
# III. DATA PERSISTENCE LAYER (JSON Format Storage Engine)
# =====================================================================

class JSONStorageRepository(StorageRepository):
    """Manages saving and loading of data using clean JSON formatting"""
    def __init__(self, filename: str = "library_data.json"):
        self.DATA_FILE = filename

    def save(self, accounts: list):
        try:
            data_to_save = []
            for acc in accounts:
                acc_dict = {
                    "name": acc.name,
                    "contact": acc.contact,
                    "penalty_start_date": acc.penalty_start_date.strftime("%Y-%m-%d %H:%M:%S") if acc.penalty_start_date else "NONE",
                    "last_calculated_penalty_days": acc.last_calculated_penalty_days,
                    "borrowed_books": []
                }
                for b in acc.borrowed_books:
                    acc_dict["borrowed_books"].append({
                        "title": b.title,
                        "borrow_date": b.borrow_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "due_date": b.due_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "condition": b.condition,
                        "status": b.status,
                        "lost_declared_date": b.lost_declared_date.strftime("%Y-%m-%d %H:%M:%S") if b.lost_declared_date else "NONE",
                        "final_overdue_days": b.final_overdue_days,
                        "lost_resolved_duration": b.lost_resolved_duration,
                        "was_damaged_upon_return": b.was_damaged_upon_return
                    })
                data_to_save.append(acc_dict)
                
            with open(self.DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(data_to_save, file, indent=4)
        except Exception as e:
            print(f"⚠️ Storage Save Error: {e}")

    def load(self) -> list:
        loaded_accounts = []
        if not os.path.exists(self.DATA_FILE):
            return loaded_accounts
        try:
            with open(self.DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                for item in data:
                    acc = BorrowerAccount(item["name"], item["contact"])
                    if item["penalty_start_date"] != "NONE":
                        acc.penalty_start_date = datetime.strptime(item["penalty_start_date"], "%Y-%m-%d %H:%M:%S")
                    acc.last_calculated_penalty_days = item["last_calculated_penalty_days"]
                    
                    for b_item in item["borrowed_books"]:
                        b_date = datetime.strptime(b_item["borrow_date"], "%Y-%m-%d %H:%M:%S")
                        d_date = datetime.strptime(b_item["due_date"], "%Y-%m-%d %H:%M:%S")
                        book = BorrowedBook(b_item["title"], b_date, d_date, b_item["condition"], b_item["status"])
                        
                        if b_item["lost_declared_date"] != "NONE":
                            book.lost_declared_date = datetime.strptime(b_item["lost_declared_date"], "%Y-%m-%d %H:%M:%S")
                        book.final_overdue_days = b_item["final_overdue_days"]
                        book.lost_resolved_duration = b_item["lost_resolved_duration"]
                        book.was_damaged_upon_return = b_item["was_damaged_upon_return"]
                        
                        acc.borrowed_books.append(book)
                    loaded_accounts.append(acc)
        except Exception as e:
            print(f"⚠️ Storage Load Error: {e}")
        return loaded_accounts

# =====================================================================
# IV. CORE DOMAIN CLASSES (Strict Encapsulation)
# =====================================================================

class BorrowedBook:
    def __init__(self, title: str, borrow_date: datetime, due_date: datetime, 
                 condition: str = "Good", status: str = "Not returned"):
        self._title = title
        self._borrow_date = borrow_date
        self._due_date = due_date
        self._condition = condition  
        self._status = status        
        
        self.lost_declared_date = None
        self.final_overdue_days = 0
        self.lost_resolved_duration = 0
        self.was_damaged_upon_return = False

    @property
    def title(self) -> str: return self._title
    @property
    def borrow_date(self) -> datetime: return self._borrow_date
    @property
    def due_date(self) -> datetime: return self._due_date
    
    @property
    def condition(self) -> str: return self._condition
    @condition.setter
    def condition(self, value: str): self._condition = value

    @property
    def status(self) -> str: return self._status
    @status.setter
    def status(self, value: str): self._status = value

    def get_overdue_days(self) -> int:
        if self._status == "Returned":
            return 0
        if datetime.now() > self._due_date:
            return (datetime.now() - self._due_date).days
        return 0


class BorrowerAccount:
    def __init__(self, name: str, contact: str):
        self._name = name
        self._contact = contact
        self.borrowed_books = []  
        self.penalty_start_date = None
        self.last_calculated_penalty_days = 0

    @property
    def name(self) -> str: return self._name
    @property
    def contact(self) -> str: return self._contact

    def update_penalty_timestamps(self, processor: Penalty):
        current_penalty = 0
        for book in self.borrowed_books:
            current_penalty += processor.calculate_deactivation_days(book)
            
        if current_penalty > 0:
            if self.penalty_start_date is None:
                self.penalty_start_date = datetime.now()
            self.last_calculated_penalty_days = current_penalty
        else:
            self.penalty_start_date = None
            self.last_calculated_penalty_days = 0

    def get_remaining_deactivation_days(self, processor: Penalty) -> int:
        self.update_penalty_timestamps(processor)
        if self.penalty_start_date is None or self.last_calculated_penalty_days == 0:
            return 0
            
        # Dito kinukuha ang lumipas na araw kahit nakasara ang program
        days_passed = (datetime.now() - self.penalty_start_date).days
        remaining = self.last_calculated_penalty_days - days_passed
        
        if remaining <= 0:
            self.penalty_start_date = None
            self.last_calculated_penalty_days = 0
            return 0
            
        return remaining

# =====================================================================
# V. THE SYSTEM INTEGRATOR CLASS (Dependency Injection applied)
# =====================================================================

class LibrarySystem:
    def __init__(self, processor: Penalty, repository: StorageRepository):
        self._processor = processor
        self._repository = repository
        self.MAX_ACCOUNTS = 100  
        
        self.accounts = self._repository.load()
        if not self.accounts:
            self.insert_sample_data()
            self._repository.save(self.accounts)

    def insert_sample_data(self):
        now = datetime.now()
        user1 = BorrowerAccount("Jhon Steeven Vargas", "09123456789")
        book1 = BorrowedBook("Intro to OOP", now - timedelta(days=5), now - timedelta(days=2))
        user1.borrowed_books.append(book1)
        user1.update_penalty_timestamps(self._processor)
        
        user2 = BorrowerAccount("Generous Furaque", "09987654321")
        book2 = BorrowedBook("SOLID Design Guide", now - timedelta(days=1), now + timedelta(days=3))
        user2.borrowed_books.append(book2)
        
        user3 = BorrowerAccount("Jules Gardon", "09152436475")
        self.accounts.extend([user1, user2, user3])

    def register_account(self):
        print("\n--- Register Account ---")
        if len(self.accounts) >= self.MAX_ACCOUNTS:
            print(f"❌ Warning: Limit reached. Maximum capacity is {self.MAX_ACCOUNTS} accounts.")
            return

        while True:
            name = input("Name: ").strip()
            if not name:
                print("❌ Warning: Name field cannot be empty!")
                continue
            break

        while True:
            contact = input("Contact: ").strip()
            if not contact:
                print("❌ Warning: Contact field cannot be empty!")
                continue
            if not contact.isdigit():
                print("❌ Warning: Contact must contain numbers only.")
                continue
            if len(contact) != 11:
                print("❌ Warning: Contact must be exactly 11 digits long.")
                continue
            if not contact.startswith("09"):
                print("❌ Warning: Contact number must start with '09'.")
                continue
            if any(acc.contact == contact for acc in self.accounts):
                print(f"❌ Warning: The contact number '{contact}' is already registered to another account!")
                continue
            break

        new_acc = BorrowerAccount(name, contact)
        self.accounts.append(new_acc)
        self._repository.save(self.accounts)
        print(f"✔️ Account successfully registered for {name}! ({len(self.accounts)}/{self.MAX_ACCOUNTS})")

    def show_borrower_list(self):
        if not self.accounts:
            print("\nEmpty library system. No registered accounts.")
            return

        while True:
            print("\n--- Borrower Account List ---")
            for i, acc in enumerate(self.accounts, 1):
                remaining_days = acc.get_remaining_deactivation_days(self._processor)
                status_tag = f" [DEACTIVATED - {remaining_days} Days Left]" if remaining_days > 0 else " [Active/Clear]"
                print(f"[{i}] {acc.name} ({acc.contact}){status_tag}")
            print("[0] Back to Main Menu")
            
            try:
                choice = int(input("\nSelect Borrower (Enter Number): "))
                if choice == 0: break
                if 1 <= choice <= len(self.accounts):
                    selected_acc = self.accounts[choice-1]
                    remaining_days = selected_acc.get_remaining_deactivation_days(self._processor)
                    
                    if remaining_days > 0:
                        print(f"\n❌ Account cannot be opened due to its {remaining_days} days deactivation!")
                        input("Press Enter to go back...")
                    else:
                        self.enter_borrower_profile(selected_acc)
                else:
                    print("❌ Invalid selection.")
            except ValueError:
                print("❌ Input validation failed. Numbers only.")

    def enter_borrower_profile(self, account: BorrowerAccount):
        while True:
            print(f"\n==========================================")
            print(f" PROFILE: {account.name}")
            print(f" CONTACT: {account.contact}")
            print(f"==========================================")
            
            if account.borrowed_books:
                print("\nCURRENT/PAST BORROWED BOOKS:")
                for i, b in enumerate(account.borrowed_books, 1):
                    b_formatted = b.borrow_date.strftime("%B %d, %Y | %I:%M %p")
                    d_formatted = b.due_date.strftime("%B %d, %Y | %I:%M %p")
                    print(f"  [{i}] Book Title: {b.title}")
                    print(f"      Date/Time Borrowed: {b_formatted}")
                    print(f"      Due Date: {d_formatted}")
                    print(f"      Condition: {b.condition} | Status: {b.status}")
            else:
                print("\nℹ️ No active borrowing history.")

            print("\n[1] Borrow Book")
            print("[2] Delete Returned Book History")
            print("[3] Delete Account")
            print("[4] Return / Update Book Status")
            print("[0] Back to List")
            
            choice = input("\nSelect Option: ")
            
            if choice == "1":
                self.borrow_book_logic(account)
            elif choice == "2":
                account.borrowed_books = [b for b in account.borrowed_books if b.status != "Returned"]
                account.update_penalty_timestamps(self._processor)
                self._repository.save(self.accounts)
                print("✔️ Returned book history successfully cleared.")
            elif choice == "3":
                confirm = input(f"Are you sure you want to delete {account.name}'s account? (y/n): ")
                if confirm.lower() == 'y':
                    self.accounts.remove(account)
                    self._repository.save(self.accounts)
                    print("✔️ Account successfully deleted.")
                    return
            elif choice == "4":
                self.return_book_logic(account)
            elif choice == "0":
                break

    def borrow_book_logic(self, account: BorrowerAccount):
        print("\n--- Borrow Book ---")
        title = input("Book title: ").strip()
        if not title:
            print("❌ Error: Book title cannot be blank.")
            return

        while True:
            try:
                days = int(input("Due date (3-5 days only): "))
                if 3 <= days <= 5: break
                print("❌ Error: Valid loan period is between 3 to 5 days only.")
            except ValueError:
                print("❌ Error: Numbers only.")

        borrow_date = datetime.now()
        due_date = borrow_date + timedelta(days=days)

        new_book = BorrowedBook(title, borrow_date, due_date)
        account.borrowed_books.append(new_book)
        account.update_penalty_timestamps(self._processor)
        self._repository.save(self.accounts)
        
        print(f"\n✔️ Book Borrowed Successfully!")
        print(f"  • Book title         : {new_book.title}")
        print(f"  • Date/time borrowed : {borrow_date.strftime('%B %d, %Y | %I:%M %p')}")
        print(f"  • Due date           : {due_date.strftime('%B %d, %Y | %I:%M %p')}")
        print(f"  • Condition          : {new_book.condition}")
        print(f"  • Status             : {new_book.status}")

    def return_book_logic(self, account: BorrowerAccount):
        active_books = [b for b in account.borrowed_books if b.status == "Not returned"]
        if not active_books:
            print("\n❌ No active unreturned books for this profile.")
            return

        print("\n--- Return / Update Window ---")
        for i, b in enumerate(active_books, 1):
            overdue_txt = f"({b.get_overdue_days()} days overdue)" if b.get_overdue_days() > 0 else ""
            print(f"[{i}] '{b.title}' | Current Condition Mark: {b.condition} {overdue_txt}")
            
        try:
            choice = int(input("Select book entry to process: "))
            if 1 <= choice <= len(active_books):
                target_book = active_books[choice-1]
                
                print(f"\nProcessing book: '{target_book.title}'")
                print("[1] Returned (Good Condition)")
                print("[2] Returned (Damaged)")
                print("[3] Declare Lost (Start 3 Days Search Grace Period)")
                print("[4] Update Lost Book -> Found and Returned Now")
                
                cond_choice = input("Select update command: ")
                target_book.final_overdue_days = target_book.get_overdue_days()
                
                if cond_choice == "1":
                    target_book.condition = "Good"
                    target_book.status = "Returned"
                    print("✔️ Book marked as Returned in Good condition.")
                elif cond_choice == "2":
                    target_book.condition = "Damaged"
                    target_book.status = "Returned"
                    print("✔️ Book marked as Returned but Damaged.")
                elif cond_choice == "3":
                    target_book.condition = "Lost"
                    target_book.lost_declared_date = datetime.now()
                    print("✔️ Book marked as LOST. 3 Days Search Chance countdown started.")
                elif cond_choice == "4":
                    if target_book.condition != "Lost":
                        print("❌ Error: This book was not previously declared Lost.")
                        return
                    
                    print("\n--- Lost Book Recovery Verification ---")
                    try:
                        days_used = int(input("How many days did it take to find and return it within the 3-day window? (0-3): "))
                        target_book.lost_resolved_duration = days_used
                    except ValueError:
                        target_book.lost_resolved_duration = 0
                        
                    is_dmg = input("Was the book damaged upon return? (y/n): ")
                    target_book.was_damaged_upon_return = is_dmg.lower() == 'y'
                    
                    target_book.condition = "Lost_Then_Returned"
                    target_book.status = "Returned"
                    print("✔️ Lost book status updated successfully to Returned!")
                else:
                    print("❌ Invalid command option.")
                
                account.update_penalty_timestamps(self._processor)
                self._repository.save(self.accounts)
            else:
                print("❌ Selection out of bounds.")
        except ValueError:
            print("❌ Input error format.")

    def search_and_filter_tool_options(self):
        print("\n🔍 SEARCH AND FILTER TOOL OPTIONS")
        print("[1] Search Borrowers by Name Keyword")
        print("[2] Filter: All Deactivated Profiles")
        choice = input("Select: ")
        
        if choice == "1":
            q = input("Enter search keyword: ").lower()
            for acc in self.accounts:
                if q in acc.name.lower():
                    print(f"📌 Match: {acc.name} - Contact: {acc.contact}")
        elif choice == "2":
            print("\n--- Currently Deactivated Accounts ---")
            for acc in self.accounts:
                rem_days = acc.get_remaining_deactivation_days(self._processor)
                if rem_days > 0:
                    print(f"• {acc.name} (Deactivated - {rem_days} Days Remaining)")

    def invoked_manual_override(self):
        print("\n⚙️ INVOKED MANUAL OVERRIDE")
        name_search = input("Enter accurate Name of borrower to lift deactivation from: ").strip()
        found = False
        for acc in self.accounts:
            if acc.name.lower() == name_search.lower():
                found = True
                for b in acc.borrowed_books:
                    b.status = "Returned"
                    b.condition = "Good"
                    b.final_overdue_days = 0
                    b.lost_resolved_duration = 0
                acc.penalty_start_date = None
                acc.last_calculated_penalty_days = 0
                self._repository.save(self.accounts)
                print(f"✔️ Override Successful! Restored full account access to {acc.name}.")
                break
        if not found:
            print("❌ Target borrower name not found.")

    def critical_alert_list(self):
        print("\n⚡ CRITICAL ALERT LIST (Accounts Active Penalty Days) ⚡")
        print(f"{'Borrower Name':<20} | {'Contact Info':<15} | {'Deactivation Days Left':<25}")
        print("-" * 65)
        for acc in self.accounts:
            rem_days = acc.get_remaining_deactivation_days(self._processor)
            if rem_days > 0:
                print(f"{acc.name:<20} | {acc.contact:<15} | {f'{rem_days} days locked':<25}")

    def generate_statistical_reports_summary(self):
        print("\n📊 GENERATE STATISTICAL REPORTS SUMMARY")
        total_accounts = len(self.accounts)
        active_loans = sum(len([b for b in acc.borrowed_books if b.status == "Not returned"]) for acc in self.accounts)
        deactivated = sum(1 for acc in self.accounts if acc.get_remaining_deactivation_days(self._processor) > 0)
        
        print(f"Total Registered Profiles   : {total_accounts} / {self.MAX_ACCOUNTS}")
        print(f"Total Books Checked Out     : {active_loans} books")
        print(f"Total Blocked/Deactivated   : {deactivated} accounts")

    def run(self):
        while True:
            print("\n=======================================================")
            print("         LIBRARY BOOK BORROWING PENALTY APP            ")
            print("=======================================================")
            print("[1] Register account")
            print("[2] Borrower Account")
            print("[3] Search and Filter tool options")
            print("[4] Invoked Manual Override")
            print("[5] Critical alert list")
            print("[6] Generate statistical reports summary")
            print("[7] Exit")
            print("=======================================================")
            
            choice = input("Enter Choice (1-7): ")
            
            if choice == "1": self.register_account()
            elif choice == "2": self.show_borrower_list()
            elif choice == "3": self.search_and_filter_tool_options()
            elif choice == "4": self.invoked_manual_override()
            elif choice == "5": self.critical_alert_list()
            elif choice == "6": self.generate_statistical_reports_summary()
            elif choice == "7":
                self._repository.save(self.accounts)
                print("\nShutting down administrative framework session. Goodbye!")
                break
            else:
                print("❌ Input validation failed. Please choose from 1 to 7.")

# =====================================================================
# VI. RUNNING ENVIRONMENT INITIALIZATION (Dependency Injection Entry)
# =====================================================================
if __name__ == "__main__":
    storage_engine = JSONStorageRepository("library_data.json")
    engine_processor = BookPenaltyProcessor()
    
    app = LibrarySystem(processor=engine_processor, repository=storage_engine)
    app.run()
