from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

import knight_cash_api as cash_api


@pytest.fixture
def client() -> TestClient:
    """Give every test an independent copy of the seeded ledger."""
    cash_api.reset_balances()
    return TestClient(cash_api.app)


@pytest.mark.parametrize(
    ("account", "expected_balance"),
    [
        ("arthur", "1000.00"),
        ("lancelot", "500.00"),
        ("guinevere", "750.00"),
    ],
)
def test_balance_returns_seeded_account_balance(client, account, expected_balance):
    response = client.get(f"/balance/{account}")

    assert response.status_code == 200
    assert response.json() == {"account": account, "balance": expected_balance}


def test_balance_rejects_unknown_account(client):
    response = client.get("/balance/mordred")

    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"


def test_transfer_happy_path_moves_money_and_preserves_precision(client):
    response = client.post(
        "/transfer",
        json={"sender": "arthur", "recipient": "lancelot", "amount": "0.10"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Transfer completed",
        "sender_balance": "999.90",
        "recipient_balance": "500.10",
    }
    assert client.get("/balance/arthur").json()["balance"] == "999.90"
    assert client.get("/balance/lancelot").json()["balance"] == "500.10"
    assert sum(cash_api.balances.values(), Decimal("0")) == Decimal("2250.00")


@pytest.mark.parametrize("amount", ["0", "-1", "-0.01"])
def test_transfer_rejects_non_positive_amounts(client, amount):
    response = client.post(
        "/transfer",
        json={"sender": "arthur", "recipient": "lancelot", "amount": amount},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Transfer amount must be greater than zero"
    assert cash_api.balances["arthur"] == Decimal("1000.00")


def test_transfer_rejects_insufficient_funds(client):
    response = client.post(
        "/transfer",
        json={"sender": "arthur", "recipient": "lancelot", "amount": "1000.01"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient funds"
    assert cash_api.balances["lancelot"] == Decimal("500.00")


def test_transfer_allows_entire_available_balance(client):
    response = client.post(
        "/transfer",
        json={"sender": "lancelot", "recipient": "guinevere", "amount": "500.00"},
    )

    assert response.status_code == 200
    assert cash_api.balances["lancelot"] == Decimal("0.00")


def test_transfer_rejects_same_sender_and_recipient(client):
    response = client.post(
        "/transfer",
        json={"sender": "arthur", "recipient": "arthur", "amount": "1"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Sender and recipient must be different"


@pytest.mark.parametrize(
    "payload",
    [
        {"sender": "", "recipient": "lancelot", "amount": "1"},
        {"sender": "arthur", "recipient": "   ", "amount": "1"},
    ],
)
def test_transfer_rejects_blank_account_names(client, payload):
    response = client.post("/transfer", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Sender and recipient are required"


@pytest.mark.parametrize(
    "payload",
    [
        {"sender": "mordred", "recipient": "arthur", "amount": "1"},
        {"sender": "arthur", "recipient": "mordred", "amount": "1"},
    ],
)
def test_transfer_rejects_unknown_sender_or_recipient(client, payload):
    response = client.post("/transfer", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"


@pytest.mark.parametrize(
    "payload",
    [
        {"sender": "arthur", "recipient": "lancelot"},
        {"sender": "arthur", "recipient": "lancelot", "amount": "not-money"},
    ],
)
def test_transfer_rejects_malformed_requests(client, payload):
    response = client.post("/transfer", json=payload)

    assert response.status_code == 422

