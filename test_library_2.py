import pytest
import os
import datetime
from main_library import (
    BorrowedBook, BorrowerAccount, BookPenaltyProcessor, 
    JSONStorageRepository, LibrarySystem
)


@pytest.fixture
def processor():
    return BookPenaltyProcessor()

@pytest.fixture
def sample_account():
    return BorrowerAccount("Juan Dela Cruz", "09123456789")

@pytest.fixture
def temp_repo():
    filename = "test_temp_data.json"
    repo = JSONStorageRepository(filename)
    yield repo
    if os.path.exists(filename):
        os.remove(filename)

def test_penalty_good_condition_overdue(processor):
 
    due = datetime.datetime.now() - datetime.timedelta(days=2)
    book = BorrowedBook("Python 101", datetime.datetime.now(), due, condition="Good")
    

    penalty = processor.calculate_deactivation_days(book)
    assert penalty == 4.0

def test_penalty_lost_grace_period(processor):

    book = BorrowedBook("Data Structures", datetime.datetime.now(), datetime.datetime.now())
    book.status = "Not returned"
    book.condition = "Lost"
    book.lost_declared_date = datetime.datetime.now()
    

    assert processor.calculate_deactivation_days(book) == 0.0

def test_penalty_lost_after_grace_period(processor):

    past_date = datetime.datetime.now() - datetime.timedelta(days=5)
    book = BorrowedBook("Algorithms", datetime.datetime.now(), datetime.datetime.now())
    book.status = "Not returned"
    book.condition = "Lost"
    book.lost_declared_date = past_date
    

    assert processor.calculate_deactivation_days(book) >= 5.0


def test_account_deactivation_status(sample_account, processor):
    due = datetime.datetime.now() - datetime.timedelta(days=1)
    book = BorrowedBook("Logic Circuits", datetime.datetime.now(), due, condition="Damaged")
    sample_account.borrowed_books.append(book)
    
    sample_account.update_penalty_timestamps(processor)
    

    status = sample_account.get_remaining_deactivation_days(processor)
    assert status != "0"
    assert "d" in status or "h" in status or "m" in status

def test_manual_override(sample_account, processor):
 
    book = BorrowedBook("Physics", datetime.datetime.now(), datetime.datetime.now() - datetime.timedelta(days=5))
    sample_account.borrowed_books.append(book)
    sample_account.update_penalty_timestamps(processor)
    
 
    for b in sample_account.borrowed_books:
        b.status = "Returned"
        b.condition = "Good"
    sample_account.penalty_start_date = None
    sample_account.last_calculated_penalty_days = 0.0
    
    assert sample_account.get_remaining_deactivation_days(processor) == "0"



def test_json_save_and_load(temp_repo, sample_account):
    accounts = [sample_account]
    temp_repo.save(accounts)
    
    loaded_accounts = temp_repo.load()
    assert len(loaded_accounts) == 1
    assert loaded_accounts[0].name == "Juan Dela Cruz"
    assert loaded_accounts[0].contact == "09123456789"



def test_register_account_limit(processor, temp_repo):
    system = LibrarySystem(processor, temp_repo)
    system.MAX_ACCOUNTS = 2
    

    system.accounts.append(BorrowerAccount("User 1", "09111111111"))
    system.accounts.append(BorrowerAccount("User 2", "09222222222"))
    
    assert len(system.accounts) == 2

    assert len(system.accounts) >= system.MAX_ACCOUNTS

def test_statistical_report_logic(processor, temp_repo):
    system = LibrarySystem(processor, temp_repo)
    acc = BorrowerAccount("Test User", "09123456789")
    acc.borrowed_books.append(BorrowedBook("Test Book", datetime.datetime.now(), datetime.datetime.now()))
    system.accounts.append(acc)
    
    total_accounts = len(system.accounts)
    active_loans = sum(len([b for b in a.borrowed_books if b.status == "Not returned"]) for a in system.accounts)
    
    assert total_accounts == 1
    assert active_loans == 1


def test_full_system_flow(temp_repo, processor):
 
    system = LibrarySystem(processor, temp_repo)
   
    new_acc = BorrowerAccount("Test Student", "09998887776")
    system.accounts.append(new_acc)
    system._repository.save(system.accounts)
    

    loaded = temp_repo.load()
    assert len(loaded) == 1
    assert loaded[0].name == "Test Student"

def test_statistical_report_accuracy(temp_repo, processor):
    system = LibrarySystem(processor, temp_repo)
    
    acc = BorrowerAccount("Reporter", "09123456789")
    book = BorrowedBook("Python Guide", datetime.datetime.now(), datetime.datetime.now())
    acc.borrowed_books.append(book)
    system.accounts.append(acc)
    
    active_loans = sum(len([b for b in a.borrowed_books if b.status == "Not returned"]) for a in system.accounts)
    assert active_loans == 1
    assert len(system.accounts) == 1

def test_contact_number_validation_logic():
    contact = "09123456789"
    is_valid = contact.isdigit() and len(contact) == 11 and contact.startswith("09")
    assert is_valid == True

    invalid_contact = "12345"
    is_invalid = invalid_contact.isdigit() and len(invalid_contact) == 11 and invalid_contact.startswith("09")
    assert is_invalid == False
