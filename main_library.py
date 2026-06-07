from abc import ABC, abstractmethod
import datetime
import os
import json
import math

R, G, Y, C, W, B, O = '\033[91m', '\033[92m', '\033[93m', '\033[96m', '\033[0m', '\033[94m', '\033[33m'
	
class Penalty(ABC):
    @abstractmethod
    def calculate_deactivation_days(self, book) -> float:
        pass


class StorageRepository(ABC):
    @abstractmethod
    def save(self, accounts: list):
        pass

    @abstractmethod
    def load(self) -> list:
        pass


class BookPenaltyProcessor(Penalty):
    def calculate_deactivation_days(self, book) -> float:
        total_days = 0.0
        overdue_days = book.get_overdue_days()
        
        if book.status == "Not returned":
            if book.condition == "Good" and overdue_days > 0:
                total_days = 2 + overdue_days
            elif book.condition == "Damaged":
                total_days = 4 + overdue_days
            elif book.condition == "Lost":
                if book.lost_declared_date:
                    seconds_since_lost = (datetime.datetime.now() - book.lost_declared_date).total_seconds()
                    days_since_lost = seconds_since_lost / 86400.0  
                    if days_since_lost > 3:
                        total_days = 5 + overdue_days
                    else:
                        total_days = 0.0
                else:
                    total_days = 5 + overdue_days

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

        return float(total_days)


class JSONStorageRepository(StorageRepository):
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
                        acc.penalty_start_date = datetime.datetime.strptime(item["penalty_start_date"], "%Y-%m-%d %H:%M:%S")
                    acc.last_calculated_penalty_days = float(item["last_calculated_penalty_days"])
                    
                    for b_item in item["borrowed_books"]:
                        b_date = datetime.datetime.strptime(b_item["borrow_date"], "%Y-%m-%d %H:%M:%S")
                        d_date = datetime.datetime.strptime(b_item["due_date"], "%Y-%m-%d %H:%M:%S")
                        book = BorrowedBook(b_item["title"], b_date, d_date, b_item["condition"], b_item["status"])
                        
                        if b_item["lost_declared_date"] != "NONE":
                            book.lost_declared_date = datetime.datetime.strptime(b_item["lost_declared_date"], "%Y-%m-%d %H:%M:%S")
                        book.final_overdue_days = b_item["final_overdue_days"]
                        book.lost_resolved_duration = b_item["lost_resolved_duration"]
                        book.was_damaged_upon_return = b_item["was_damaged_upon_return"]
                        
                        acc.borrowed_books.append(book)
                    loaded_accounts.append(acc)
        except Exception as e:
            print(f"⚠️   Storage Load Error: {e}")
        return loaded_accounts


class BorrowedBook:
    def __init__(self, title: str, borrow_date: datetime.datetime, due_date: datetime.datetime, 
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
    def title(self) -> str:
        return self._title

    @property
    def borrow_date(self) -> datetime.datetime:
        return self._borrow_date

    @property
    def due_date(self) -> datetime.datetime:
        return self._due_date
    
    @property
    def condition(self) -> str:
        return self._condition

    @condition.setter
    def condition(self, value: str):
        self._condition = value

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str):
        self._status = value

    def get_overdue_days(self) -> int:
        if self._status == "Returned":
            return 0
        if datetime.datetime.now() > self._due_date:
            return int((datetime.datetime.now() - self._due_date).total_seconds() / 86400.0)
        return 0


class BorrowerAccount:
    def __init__(self, name: str, contact: str):
        self._name = name
        self._contact = contact
        self.borrowed_books = []  
        self.penalty_start_date = None
        self.last_calculated_penalty_days = 0.0

    @property
    def name(self) -> str:
        return self._name

    @property
    def contact(self) -> str:
        return self._contact

    def update_penalty_timestamps(self, processor: Penalty):
        current_penalty = 0.0
        for book in self.borrowed_books:
            current_penalty += processor.calculate_deactivation_days(book)
            
        if current_penalty > 0:
            if self.penalty_start_date is None:
                self.penalty_start_date = datetime.datetime.now()
                self.last_calculated_penalty_days = current_penalty
            else:
                if current_penalty > self.last_calculated_penalty_days:
                    self.last_calculated_penalty_days = current_penalty
        else:
            self.penalty_start_date = None
            self.last_calculated_penalty_days = 0.0

    def get_remaining_deactivation_days(self, processor: Penalty):
        if self.penalty_start_date is None or self.last_calculated_penalty_days == 0:
            return "0"
            
        seconds_passed = (datetime.datetime.now() - self.penalty_start_date).total_seconds()
        remaining_seconds = (self.last_calculated_penalty_days * 86400.0) - seconds_passed
        
        if remaining_seconds <= 0:
            for b in self.borrowed_books:
                b.status = "Returned"
                b.condition = "Good"
                b.final_overdue_days = 0
                b.lost_resolved_duration = 0
                b.was_damaged_upon_return = False
                b.lost_declared_date = None
            
            self.penalty_start_date = None
            self.last_calculated_penalty_days = 0.0
            return "0"
            
        days = int(remaining_seconds // 86400)
        hours = int((remaining_seconds % 86400) // 3600)
        minutes = int((remaining_seconds % 3600) // 60)
        seconds = int(remaining_seconds % 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        else:
            return f"{minutes}m {seconds}s left"


class LibrarySystem:
    def __init__(self, processor: Penalty, repository: StorageRepository):
        self._processor = processor
        self._repository = repository
        self.MAX_ACCOUNTS = 1000 
        self.accounts = self._repository.load()

    def register_account(self):
        print("\n" + "="*70)
        print(f"{C}REGISTER NEW ACCOUNT{W}".center(75))
        print('='*70)
        if len(self.accounts) >= self.MAX_ACCOUNTS:
            print(f"{R} Limit reached. Maximum capacity is {self.MAX_ACCOUNTS} accounts.{W}".center(75))
            return

        while True:
            name = input("  Name: ").strip()
            if not name:
                print(f"{R}     Name field cannot be empty!{W}")
                continue
            if any(acc.name.lower() == name.lower() for acc in self.accounts):
                print(f"{R}     The name '{name}' is already registered!{W}")
                continue
            break

        while True:
            contact = input("  Contact: ").strip()
            if not contact:
                print(f"{R}     Contact field cannot be empty!{W}")
                continue
            if not contact.isdigit():
                print(f"{R}     Please enter numbers only.{W}")
                continue
            if len(contact) != 11:
                print(f"{R}     Must contains 11 numbers.{W}")
                continue
            if not contact.startswith("09"):
                print(f"{R}     Must start with 09.{W}")
                continue
            break

        new_acc = BorrowerAccount(name, contact)
        self.accounts.append(new_acc)
        self._repository.save(self.accounts)
        print("_"*70)
        print(f"{Y}ACCOUNT SUCCESSFULLY REGISTERED for {name}!{W}".center(75))
        print(f" ({len(self.accounts)}/{self.MAX_ACCOUNTS})".center(70))

    def show_borrower_list(self):
        if not self.accounts:
            print("\n")
            print(f"{B}Empty library system. No registered accounts.{W}".center(75))
            return

        while True:
            print("\n" + "="*70)
            print(f"{C}BORROWER ACCOUNT LIST{W}".center(75))
            print("="*70)
            for i, acc in enumerate(self.accounts, 1):
                rem_status = acc.get_remaining_deactivation_days(self._processor)
                status_tag = f"{R}[DEACTIVATED - {rem_status}]{W}" if rem_status != "0" else f"{G}[Active] {W}"
                print(f"  [{i}] {acc.name:<30}{status_tag}")
            print(f"{C}  [0] Back to Main Menu{W}")
            
            try:
                choice_input = input("\n  Select Borrower (Enter Number): ").strip()
                if not choice_input: continue
                choice = int(choice_input)
                
                if choice == 0:
                    break
                
                if 1 <= choice <= len(self.accounts):
                    selected_acc = self.accounts[choice-1]
                    rem_status = selected_acc.get_remaining_deactivation_days(self._processor)
                    
                    if rem_status != "0":
                        print("\n")
                        print(f"{R}Account cannot be opened due to its {rem_status} deactivation!{W}".center(80))
                        input(f"Press Enter to go back...".center(75))
                    else:
                        self.enter_borrower_profile(selected_acc)
                else:
                    print(f"{R}Invalid selection.{W}".center(75))
            except ValueError:
                print(f"{R}Input validation failed. Numbers only.{W}".center(75))

    def enter_borrower_profile(self, account: BorrowerAccount):
        while True:
            print("\n" + "="*70)
            print(f" {Y}PROFILE: {account.name}".center(75))
            print(f" CONTACT: {account.contact}{W}".center(75))
            print("="*70)
            
            if account.borrowed_books:
                print("\n  CURRENT/PAST BORROWED BOOKS:")
                for i, b in enumerate(account.borrowed_books, 1):
                    b_formatted = b.borrow_date.strftime("%B %d, %Y | %I:%M:%S %p")
                    d_formatted = b.due_date.strftime("%B %d, %Y | %I:%M:%S %p")
                    print(f"  [{i}] Book Title: {b.title}")
                    print(f"      Date/Time Borrowed: {b_formatted}")
                    print(f"      Due Date: {d_formatted}")
                    print(f"      {G}Condition:{W} {b.condition} | {C}Status:{W} {b.status}")
            else:
                print("\n  No active borrowing history.")

            print("\n" + "="*70)
            print("  [1] Borrow Book")
            print("  [2] Delete Returned Book History")
            print("  [3] Delete Account")
            print("  [4] Return / Update Book Status")
            print(f"{C}  [0] Back to List{W}")
            
            choice = input("\n  Select Option: ").strip()
            
            if choice == "1":
                self.borrow_book_logic(account)
            elif choice == "2":
                account.borrowed_books = [b for b in account.borrowed_books if b.status != "Returned"]
                account.update_penalty_timestamps(self._processor)
                self._repository.save(self.accounts)
                print("\n")
                print(f"{Y}RETURNED BOOK HISTORY SUCCESSFULLY CLEARED.{W}".center(75))
            elif choice == "3":
                confirm = input(f"  Are you sure you want to delete {account.name}'s account? (y/n): ")
                if confirm.lower() == 'y':
                    self.accounts.remove(account)
                    self._repository.save(self.accounts)
                    print("\n")
                    print(f"{Y}ACCOUNT SUCCESSFULLY DELETED.{W}".center(75))
                    return
            elif choice == "4":
                self.return_book_logic(account)
            elif choice == "0":
                break
            else:
                print(f"{R}     Invalid selection.{W}")

    def borrow_book_logic(self, account: BorrowerAccount):
        rem_status = account.get_remaining_deactivation_days(self._processor)
        if rem_status != "0":
            print("\n")
            print(f"{R}  BLOCKED: Account has an active penalty ({rem_status}).{W}".center(75))
            print(f"{R} Borrowing privileges are suspended until the deactivation period is completed.{W}".center(75))
            input("Press Enter to continue...".center(75))
            return

        print("\n" + "="*70)
        print(f"--- {Y}BORROW BOOK{W} ---".center(75))
        title = input("  Book title: ").strip()
        if not title:
            print("\n")
            print(f"{R}Error: Book title cannot be blank.{W}".center(75))
            return

        days = 0 
        while True:
            try:
                days_input = input("  Due date (3-5 days only): ").strip()
                if not days_input: 
                    continue
                days = int(days_input) 
                if 3 <= days <= 5: 
                    break
                print(f"     {R}Enter 3-5 days only.{W}")
            except ValueError:
                print(f"     {R}Error: Numbers only.{W}")

        try:         
            borrow_date = datetime.datetime.now()
            due_date = borrow_date + datetime.timedelta(days=days)

            new_book = BorrowedBook(title, borrow_date, due_date)
            account.borrowed_books.append(new_book)
            account.update_penalty_timestamps(self._processor)
            self._repository.save(self.accounts)
            
            print("\n")
            print(f"{Y}BOOK BORROWED SUCCESSFULLY!{W}".center(75))
            print("\n")
            print(f"  • Book title         : {new_book.title}")
            print(f"  • Date/time borrowed : {borrow_date.strftime('%B %d, %Y | %I:%M:%S %p')}")
            print(f"  • Due date           : {due_date.strftime('%B %d, %Y | %I:%M:%S %p')}")
            
            input("\n  Press Enter to return to profile...") 

        except Exception as e:
            print(f"  {R}System Error: {e}{W}")

    def return_book_logic(self, account: BorrowerAccount):
        active_books = [b for b in account.borrowed_books if b.status == "Not returned"]
        if not active_books:
            print("\n")
            print(f"{R}No active unreturned books for this profile.{W}".center(75))
            return

        print("\n" + "="*70)
        print(f"--- {Y}RETURN / UPDATE WINDOW{W} ---".center(75))
        for i, b in enumerate(active_books, 1):
            overdue_txt = f"({b.get_overdue_days()} days overdue)" if b.get_overdue_days() > 0 else ""
            print(f"  [{i:<2}] '{b.title:<15}' |  Current Condition Mark:  {G}{b.condition}{W} {R}{overdue_txt}{W}")
            
        try:
            choice_input = input("  Select book entry to process: ").strip()
            if not choice_input: return
            choice = int(choice_input)

            if 1 <= choice <= len(active_books):
                target_book = active_books[choice-1]
                
                print("\n")
                print(f"  Processing book: '{target_book.title}'")
                print("  [1] Returned (Good Condition)")
                print("  [2] Returned (Damaged)")
                print("  [3] Declare Lost (Start 3 Days Search Grace Period)")
                print("  [4] Update Lost Book -> Found and Returned Now")
                
                cond_choice = input("\n  Select update command: ").strip()
                target_book.final_overdue_days = target_book.get_overdue_days()
                
                if cond_choice == "1":
                    target_book.condition = "Good"
                    target_book.status = "Returned"
                    print("\n")
                    print(f"{G} Book Marked As Returned In Good Condition.{W}".center(75))
                elif cond_choice == "2":
                    target_book.condition = "Damaged"
                    target_book.status = "Returned"
                    print("\n")
                    print(f"{Y} Book marked as Returned but Damaged.{W}".center(75))
                elif cond_choice == "3":
                    target_book.condition = "Lost"
                    target_book.lost_declared_date = datetime.datetime.now()
                    print ("\n")
                    print(f"{R}Book marked as LOST. 3 Days Search Chance countdown started.{W}".center(75))
                elif cond_choice == "4":
                    if target_book.condition != "Lost":
                        print("\n  No prior Lost status was recorded for this book.".center(70))
                        return
                    
                    print("\n")
                    print("--- {Y}LOST BOOK RECOVERY VERIFICATION{W} ---")
                    while True:
                        try:
                            days_used_input = input("  Days taken to locate and return the book (0-3): ").strip()
                            if not days_used_input: continue
                            days_used = int(days_used_input)
                            if 0 <= days_used <= 3:
                                target_book.lost_resolved_duration = days_used
                                break
                            print(f"     {R}Error: 0 to 3 days lamang.{W}")
                        except ValueError:
                            print(f"     {R}Error: Numbers only.{W}")
                        
                    is_dmg = input("  Was the book damaged when it was returned? (y/n): ")
                    target_book.was_damaged_upon_return = is_dmg.lower() == 'y'
                    
                    target_book.condition = "Lost_Then_Returned"
                    target_book.status = "Returned"
                    print(f"{Y}LOST BOOK STATUS UPDATED SUCCESSFULLY TO RETURNED!{W}".center(75))
                else:
                    print(f"{R}     Invalid command option.{W}")
                
                account.update_penalty_timestamps(self._processor)
                self._repository.save(self.accounts)
            else:
                print(f"{R}     Selection out of bounds.{W}")
        except ValueError:
            print(f"{R}     Input error format.{W}")

    def search_and_filter_tool_options(self):
        print("\n" + "="*70)
        print(f"{C}SEARCH AND FILTER TOOL OPTIONS{W}".center(75))
        print("—"*70)
        print("  [1] Search Borrowers by Name Keyword")
        print(f"  [2] {R}Filter: All Deactivated Profiles{W}")
        choice = input("  Select: ").strip()
        
        if choice == "1":
            print("—"*70)
            q = input("  Enter search keyword: ").strip().lower()
            if not q: return
            found = False
            for acc in self.accounts:
                if q in acc.name.lower():
                    print(f"  📌 Match: {acc.name:<30} - Contact: {acc.contact}")
                    found = True
            if not found: 
                print("\n")
                print(f"{R}No matching records.{W}".center(75))
        elif choice == "2":
            print("="*70)
            print(f"--- {R}CURRENTLY DEACTIVATED ACCOUNTS{W} ---".center(75))
            
            found_deactivated = False
            for acc in self.accounts:
                rem_status = acc.get_remaining_deactivation_days(self._processor)
                if rem_status != "0":
                    print(f"  • {acc.name} (Deactivated - {rem_status} Remaining)")
                    found_deactivated = True
            if not found_deactivated: 
                print(f"{R}No accounts are currently deactivated.{W}".center(75))
        else:
            print(f"{R}Invalid option.{W}".center(75))

    def invoked_manual_override(self):
        print("\n" + "="*70)
        print(f"{C}INVOKED MANUAL OVERRIDE{W}".center(75))
        print("="*70)

        name_search = input("  Enter accurate name of borrower to lift deactivation from: ").strip()
        if not name_search: return
        found = False

        for acc in self.accounts:
            if acc.name.lower() == name_search.lower():
                found = True
                for b in acc.borrowed_books:
                    b.status = "Returned"
                    b.condition = "Good"
                    b.final_overdue_days = 0
                    b.lost_resolved_duration = 0
                    b.was_damaged_upon_return = False
                    b.lost_declared_date = None   

                acc.penalty_start_date = None
                acc.last_calculated_penalty_days = 0.0

                self._repository.save(self.accounts)
                print("\n")
                print(f"{Y}OVERRIDE SUCCESSFUL! Restored full account access to {acc.name}.{W}".center(75))
                break

        if not found:
            print("\n")
            print(f"{R}Target borrower profile not found.{W}".center(75))

    def critical_alert_list(self):
        print("\n" + "="*70)
        print(f"{R}⚡ CRITICAL ALERT LIST (Accounts Active Penalty Days) ⚡{W}".center(75))
        print("="*70)
        print(f"  {'👤 Borrower Name':<20} |  {'☎ Contact Info':<15} |  {'🔐 Deactivation Status':<25}")
        print("-"*70)
        has_alerts = False
        for acc in self.accounts:
            rem_status = acc.get_remaining_deactivation_days(self._processor)
            if rem_status != "0":
                print(f"  {acc.name:<20}  |  {acc.contact:<15}  |     {rem_status:<25}")
                has_alerts = True
        if not has_alerts: 
            print(f"{B}No accounts are currently flagged.{W}".center(75))

    def generate_statistical_reports_summary(self):
        print("\n" + "="*70)
        print(f"{Y}GENERATE STATISTICAL REPORTS SUMMARY{W}".center(75))
        print("="*70)
        total_accounts = len(self.accounts)
        active_loans = sum(len([b for b in acc.borrowed_books if b.status == "Not returned"]) for acc in self.accounts)
        deactivated = sum(1 for acc in self.accounts if acc.get_remaining_deactivation_days(self._processor) != "0")
        
        print(f"  Total Registered Profiles   : {total_accounts} / {self.MAX_ACCOUNTS}")
        print(f"  Total Books Checked Out     : {active_loans} books")
        print(f"  Total Blocked/Deactivated   : {deactivated} accounts")

    def run(self):
        while True:
            print("\n" + "="*70)
            print(f"{C}LIBRARY BOOK BORROWING PENALTY APP{W}".center(75))
            print("="*70)
            print("  [1] Register Account")
            print("  [2] Borrower Account")
            print("  [3] Search and Filter tool Options")
            print("  [4] Invoked Manual Override")
            print(f"  [5]{R} Critical Alert List{W}")
            print(f"  [6]{Y} Generate Statistical Reports Summary{W}")
            print(f"{C}  [7] Exit{W}")
            print("="*70)
            
            choice = input("  Enter Choice (1-7): ").strip()
            
            if choice == "1": 
                self.register_account()
            elif choice == "2": 
                self.show_borrower_list()
            elif choice == "3": 
                self.search_and_filter_tool_options()
            elif choice == "4": 
                self.invoked_manual_override()
            elif choice == "5": 
                self.critical_alert_list()
            elif choice == "6": 
                self.generate_statistical_reports_summary()
            elif choice == "7":
                self._repository.save(self.accounts)
                print("\n")
                print(f"{Y}SHUTTING DOWN APPLICATION!{W}".center(75))
                print(f"{Y} Bye Byeeee! {W}".center(75))
                break
            else:
                print("\n")
                print(f"{R} Input validation failed. Please choose from 1 to 7.{W}".center(75))


if __name__ == "__main__":
    storage_engine = JSONStorageRepository("library_data.json")
    engine_processor = BookPenaltyProcessor()
    
    app = LibrarySystem(processor=engine_processor, repository=storage_engine)
    app.run()
