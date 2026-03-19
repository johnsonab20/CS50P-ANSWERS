"""
Finance Dashboard — CLI Companion
CS50P Final Project Companion Tool

Usage:
  python project.py add
  python project.py list [--month YYYY-MM]
  python project.py summary [--month YYYY-MM]
  python project.py delete <id>
  python project.py export
"""

import json
import os
import sys
import uuid
import webbrowser
from datetime import datetime
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data.json"
HTML_FILE = Path(__file__).parent / "index.html"

INCOME_CATEGORIES  = ["Salary", "Freelance", "Investment", "Gift", "Other Income"]
EXPENSE_CATEGORIES = ["Housing", "Food", "Transport", "Health", "Entertainment",
                      "Shopping", "Utilities", "Education", "Other Expense"]


# ── helpers ───────────────────────────────────────────────────────────────────

def load() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE) as f:
        return json.load(f)


def save(data: list[dict]) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def fmt_money(amount: float) -> str:
    return f"${amount:,.2f}"


def current_month() -> str:
    return datetime.now().strftime("%Y-%m")


def parse_month(month_str: str) -> tuple[int, int]:
    """Return (year, month_1indexed) from 'YYYY-MM'."""
    dt = datetime.strptime(month_str, "%Y-%m")
    return dt.year, dt.month


def filter_by_month(data: list[dict], month_str: str) -> list[dict]:
    year, month = parse_month(month_str)
    result = []
    for tx in data:
        d = datetime.strptime(tx["date"], "%Y-%m-%d")
        if d.year == year and d.month == month:
            result.append(tx)
    return result


# ── commands ──────────────────────────────────────────────────────────────────

def cmd_add() -> None:
    """Interactively add a new transaction."""
    print("\n── Add Transaction ──────────────────")

    # Type
    while True:
        t = input("Type [income/expense]: ").strip().lower()
        if t in ("income", "expense"):
            tx_type = t
            break
        print("  Please enter 'income' or 'expense'.")

    # Description
    while True:
        desc = input("Description: ").strip()
        if desc:
            break
        print("  Description cannot be empty.")

    # Amount
    while True:
        try:
            amount = float(input("Amount: $").strip())
            if amount <= 0:
                raise ValueError
            break
        except ValueError:
            print("  Please enter a positive number.")

    # Category
    categories = INCOME_CATEGORIES if tx_type == "income" else EXPENSE_CATEGORIES
    print("Categories:")
    for i, cat in enumerate(categories, 1):
        print(f"  {i}. {cat}")
    while True:
        try:
            idx = int(input("Choose category (number): ").strip()) - 1
            if 0 <= idx < len(categories):
                category = categories[idx]
                break
        except ValueError:
            pass
        print(f"  Enter a number between 1 and {len(categories)}.")

    # Date
    today = datetime.now().strftime("%Y-%m-%d")
    date_input = input(f"Date [{today}]: ").strip() or today
    try:
        datetime.strptime(date_input, "%Y-%m-%d")
    except ValueError:
        print("  Invalid date, using today.")
        date_input = today

    tx = {
        "id":       str(uuid.uuid4())[:8],
        "type":     tx_type,
        "desc":     desc,
        "amount":   round(amount, 2),
        "category": category,
        "date":     date_input,
    }

    data = load()
    data.append(tx)
    save(data)
    print(f"\n  ✓ Added [{tx['type'].upper()}] {tx['desc']} — {fmt_money(tx['amount'])} ({tx['date']})")


def cmd_list(month: str | None = None) -> None:
    """List transactions, optionally filtered to a month."""
    month = month or current_month()
    data  = filter_by_month(load(), month)

    if not data:
        print(f"No transactions for {month}.")
        return

    data.sort(key=lambda t: t["date"])
    print(f"\n── Transactions for {month} ──────────────────")
    print(f"  {'ID':<10} {'Date':<12} {'Type':<8} {'Category':<16} {'Amount':>10}  Description")
    print("  " + "─" * 72)
    for tx in data:
        sign = "+" if tx["type"] == "income" else "-"
        print(f"  {tx['id']:<10} {tx['date']:<12} {tx['type']:<8} {tx['category']:<16} "
              f"{sign}{fmt_money(tx['amount']):>10}  {tx['desc']}")
    print()


def cmd_summary(month: str | None = None) -> None:
    """Print a summary for the given month."""
    month = month or current_month()
    data  = filter_by_month(load(), month)

    income  = sum(t["amount"] for t in data if t["type"] == "income")
    expense = sum(t["amount"] for t in data if t["type"] == "expense")
    balance = income - expense
    savings = (balance / income * 100) if income else 0

    print(f"\n── Summary for {month} ──────────────────")
    print(f"  Total Income:   {fmt_money(income):>12}")
    print(f"  Total Expenses: {fmt_money(expense):>12}")
    print(f"  Net Balance:    {fmt_money(balance):>12}  {'✓ positive' if balance >= 0 else '✗ deficit'}")
    print(f"  Savings Rate:   {savings:>11.1f}%")

    # Category breakdown
    cats: dict[str, float] = {}
    for tx in data:
        if tx["type"] == "expense":
            cats[tx["category"]] = cats.get(tx["category"], 0) + tx["amount"]

    if cats:
        print("\n  Expense categories:")
        for cat, total in sorted(cats.items(), key=lambda x: -x[1]):
            pct = total / expense * 100 if expense else 0
            bar = "█" * int(pct / 5)
            print(f"    {cat:<18} {fmt_money(total):>10}  {bar:<20} {pct:.1f}%")
    print()


def cmd_delete(tx_id: str) -> None:
    """Delete a transaction by ID."""
    data = load()
    before = len(data)
    data = [t for t in data if t["id"] != tx_id]
    if len(data) == before:
        print(f"  No transaction found with id '{tx_id}'.")
        return
    save(data)
    print(f"  ✓ Deleted transaction {tx_id}.")


def cmd_export() -> None:
    """Open the HTML dashboard in a browser."""
    if not HTML_FILE.exists():
        print("  Dashboard HTML not found. Make sure index.html is present.")
        return
    webbrowser.open(HTML_FILE.as_uri())
    print(f"  ✓ Opened dashboard: {HTML_FILE}")


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return

    cmd = args[0]

    if cmd == "add":
        cmd_add()

    elif cmd == "list":
        month = None
        if "--month" in args:
            idx = args.index("--month")
            if idx + 1 < len(args):
                month = args[idx + 1]
        cmd_list(month)

    elif cmd == "summary":
        month = None
        if "--month" in args:
            idx = args.index("--month")
            if idx + 1 < len(args):
                month = args[idx + 1]
        cmd_summary(month)

    elif cmd == "delete":
        if len(args) < 2:
            print("  Usage: python project.py delete <id>")
            return
        cmd_delete(args[1])

    elif cmd == "export":
        cmd_export()

    else:
        print(f"  Unknown command '{cmd}'. Run with --help for usage.")


if __name__ == "__main__":
    main()
