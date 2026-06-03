 import pytest
from datetime import datetime, timedelta
import time

from main_library import (
    BookPenaltyProcessor,
    BorrowedBook,
    BorrowerAccount,
    JSONStorageRepository,
    LibrarySystem)
       

def create_book(
    status="Not returned",
    condition="Good",
    borrow_offset=10,
    due_offset=5,
    lost_days=None,
    final_overdue=0,
    resolved_duration=0,
    damaged=False):
    	
    now = datetime.now()
    book = BorrowedBook(
        "Test Book",
        now - timedelta(days=borrow_offset),
        now - timedelta(days=due_offset))

    book._status = status
    book._condition = condition
    book.final_overdue_days = final_overdue
    book.lost_resolved_duration = resolved_duration
    book.was_damaged_upon_return = damaged

    if lost_days is not None:
        book.lost_declared_date = now - timedelta(days=lost_days)
    else:
        book.lost_declared_date = None
    return book

class FakeProcessor:
    def calculate_deactivation_days(self, book):
        return 3

class FakeRepo:
    def __init__(self):
        self.data = []

    def save(self, data):
        self.data = data

    def load(self):
        return self.data





def test_penalty_all_not_returned_cases():
    p = BookPenaltyProcessor()

    assert p.calculate_deactivation_days(create_book()) >= 2
    assert p.calculate_deactivation_days(create_book(condition="Damaged")) >= 4
    assert p.calculate_deactivation_days(create_book(condition="Lost")) >= 5



def test_penalty_lost_grace_period():
    p = BookPenaltyProcessor()

    book1 = create_book(condition="Lost", lost_days=1)
    book2 = create_book(condition="Lost", lost_days=4)

    assert isinstance(p.calculate_deactivation_days(book1), float)
    assert p.calculate_deactivation_days(book2) >= 0




def test_penalty_returned_cases():
    p = BookPenaltyProcessor()

    book1 = create_book(status="Returned", condition="Good")
    book1.final_overdue_days = 2

    book2 = create_book(status="Returned", condition="Damaged")
    book2.final_overdue_days = 2

    book3 = create_book(status="Returned", condition="Lost_Then_Returned",
                        final_overdue=2, resolved_duration=2, damaged=True)

    assert p.calculate_deactivation_days(book1) >= 2
    assert p.calculate_deactivation_days(book2) >= 4
    assert p.calculate_deactivation_days(book3) >= 5





def test_penalty_safety_edge_cases():
    p = BookPenaltyProcessor()

    book = BorrowedBook("X", datetime.now(), datetime.now())
    result = p.calculate_deactivation_days(book)

    assert isinstance(result, float)




def test_overdue_timestamp():
    book = create_book()
    assert isinstance(book.get_overdue_days(), int)




def test_no_overdue_before_due():
    future = datetime.now() + timedelta(days=5)
    book = BorrowedBook("A", datetime.now(), future)

    assert book.get_overdue_days() == 0


def test_account_timestamp_flow():
    acc = BorrowerAccount("Generous", "09123456789")
    acc.borrowed_books.append(create_book())
    acc.update_penalty_timestamps(FakeProcessor())

    assert isinstance(acc.last_calculated_penalty_days, float)



def test_deactivation_time_progress():
    acc = BorrowerAccount("Generous", "09123456789")
    acc.borrowed_books.append(create_book())
    
    class TinyPenaltyProcessor:
        def calculate_deactivation_days(self, book):
            return 0.00005 

    tiny_processor = TinyPenaltyProcessor()
    acc.update_penalty_timestamps(tiny_processor)
    
    first = acc.get_remaining_deactivation_days(tiny_processor)
    time.sleep(1.2) 
    
    second = acc.get_remaining_deactivation_days(tiny_processor)    
    assert isinstance(first, str), f"Expected string but got {type(first)}"
    assert isinstance(second, str), f"Expected string but got {type(second)}"
    assert first != "0", "Dapat may active penalty pa sa unang check."

    assert first != second, f"Dapat nagbago ang natitirang oras: '{first}' vs '{second}'"




def test_storage_save_load(tmp_path):
    file = tmp_path / "data.json"
    repo = JSONStorageRepository(str(file))

    acc = BorrowerAccount("Steeven", "09123456789")
    acc.borrowed_books.append(create_book())

    repo.save([acc])
    loaded = repo.load()
    assert isinstance(loaded, list)



def test_storage_datetime_preservation(tmp_path):
    file = tmp_path / "data.json"
    repo = JSONStorageRepository(str(file))

    acc = BorrowerAccount("Steeven", "09123456789")
    acc.penalty_start_date = datetime.now()

    repo.save([acc])
    loaded = repo.load()
    assert loaded is not None




def test_register_account(monkeypatch):
    system = LibrarySystem(FakeProcessor(), FakeRepo())

    inputs = iter(["Jules", "09123456789"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    system.register_account()
    assert len(system.accounts) == 1




def test_borrow_book(monkeypatch):
    system = LibrarySystem(FakeProcessor(), FakeRepo())
    acc = BorrowerAccount("Jules", "09123456789")

    inputs = iter(["Python Book", "3"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    system.borrow_book_logic(acc)
    assert len(acc.borrowed_books) == 1


def test_return_book(monkeypatch):
    system = LibrarySystem(FakeProcessor(), FakeRepo())
    acc = BorrowerAccount("Jules", "09123456789")

    acc.borrowed_books.append(create_book())
    inputs = iter(["1", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    system.return_book_logic(acc)
    assert acc.borrowed_books[0] is not None



def test_manual_override(monkeypatch): 
    system = LibrarySystem(FakeProcessor(), FakeRepo())
 
    acc = BorrowerAccount("Steeven", "09123456789")
    acc.borrowed_books.append(create_book(status="Returned"))
    system.accounts.append(acc)
    
    monkeypatch.setattr("builtins.input", lambda _: "Steeven")
 
    system.invoked_manual_override()

    assert acc.penalty_start_date is None
    assert acc.last_calculated_penalty_days == 0.0
    assert acc.borrowed_books[0].lost_declared_date is None




def test_negative_and_corrupt_values():
    p = BookPenaltyProcessor()

    book = create_book()
    book.final_overdue_days = -999

    result = p.calculate_deactivation_days(book)

    assert result >= 0



def test_multiple_updates_stability():
    acc = BorrowerAccount("Generous", "09123456789")
    acc.borrowed_books.append(create_book())

    for _ in range(3):
        acc.update_penalty_timestamps(FakeProcessor())
        time.sleep(0.2)

    assert acc.last_calculated_penalty_days >= 0
