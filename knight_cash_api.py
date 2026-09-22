"""A deliberately small, testable cash-transfer API for the Week 4 TDD audit."""
from __future__ import annotations

from decimal import Decimal

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI(title="Knight Cash API")

# Decimal values avoid floating-point rounding when money changes hands.
INITIAL_BALANCES: dict[str, Decimal] = {
    "arthur": Decimal("1000.00"),
    "lancelot": Decimal("500.00"),
    "guinevere": Decimal("750.00"),
}
balances = INITIAL_BALANCES.copy()


class TransferRequest(BaseModel):
    sender: str
    recipient: str
    amount: Decimal


def reset_balances() -> None:
    """Restore seed data; used by the pytest fixture to isolate tests."""
    balances.clear()
    balances.update(INITIAL_BALANCES)


def account_balance(account_id: str) -> Decimal:
    if account_id not in balances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return balances[account_id]


@app.get("/balance/{account_id}")
def get_balance(account_id: str) -> dict[str, str]:
    """Return one account's balance as a two-decimal string."""
    return {"account": account_id, "balance": f"{account_balance(account_id):.2f}"}


@app.post("/transfer")
def transfer_money(transfer: TransferRequest) -> dict[str, str]:
    """Move a positive amount between two distinct, existing accounts."""
    sender = transfer.sender.strip()
    recipient = transfer.recipient.strip()

    if not sender or not recipient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sender and recipient are required",
        )
    if sender == recipient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sender and recipient must be different",
        )
    if transfer.amount <= Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transfer amount must be greater than zero",
        )

    sender_balance = account_balance(sender)
    account_balance(recipient)
    if transfer.amount > sender_balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds",
        )

    balances[sender] -= transfer.amount
    balances[recipient] += transfer.amount
    return {
        "message": "Transfer completed",
        "sender_balance": f"{balances[sender]:.2f}",
        "recipient_balance": f"{balances[recipient]:.2f}",
    }

