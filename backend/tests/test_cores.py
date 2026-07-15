"""
Tests for Core (智核) currency system.

TDD approach: Tests written first, then implementation.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.models.core_transaction import CoreTransaction


class TestCoreBalance:
    """Test core balance endpoint"""

    @pytest.mark.asyncio
    async def test_get_core_balance(self, client: AsyncClient, auth_headers: dict, auth_user: User):
        """Test getting current core balance"""
        response = await client.get("/api/cores/balance", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "total_earned" in data
        assert "total_spent" in data
        # New users start with 100 cores
        assert data["balance"] == 100
        assert data["total_earned"] == 100
        assert data["total_spent"] == 0

    @pytest.mark.asyncio
    async def test_get_core_balance_unauthorized(self, client: AsyncClient):
        """Test getting core balance without auth fails"""
        response = await client.get("/api/cores/balance")
        assert response.status_code == 401


class TestCoreTransactions:
    """Test core transaction history endpoint"""

    @pytest.mark.asyncio
    async def test_get_transactions_empty(self, client: AsyncClient, auth_headers: dict):
        """Test getting empty transaction history"""
        response = await client.get("/api/cores/transactions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "total" in data
        assert data["total"] == 0
        assert data["transactions"] == []

    @pytest.mark.asyncio
    async def test_get_transactions_pagination(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession, auth_user: User):
        """Test transaction history pagination"""
        # Create some transactions
        for i in range(15):
            tx = CoreTransaction(
                user_id=auth_user.id,
                type="earn",
                category="checkin",
                amount=5,
                balance_after=100 + (i + 1) * 5,
                description=f"Daily check-in day {i+1}"
            )
            db_session.add(tx)
        await db_session.commit()

        # Get first page
        response = await client.get("/api/cores/transactions?limit=10&offset=0", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert len(data["transactions"]) == 10

        # Get second page
        response = await client.get("/api/cores/transactions?limit=10&offset=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 5


class TestCoreSpend:
    """Test core spending endpoint"""

    @pytest.mark.asyncio
    async def test_spend_cores_success(self, client: AsyncClient, auth_headers: dict, auth_user: User, db_session: AsyncSession):
        """Test successful core spending"""
        # Initial balance should be 100
        response = await client.post(
            "/api/cores/spend",
            headers=auth_headers,
            json={
                "amount": 5,
                "category": "ai_hint_light",
                "description": "AI hint for exercise"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["balance_after"] == 95

        # Verify transaction was recorded
        response = await client.get("/api/cores/transactions", headers=auth_headers)
        tx_data = response.json()
        # There should be at least 1 transaction (the spend)
        assert tx_data["total"] >= 1
        # Find the spend transaction
        spend_tx = next((t for t in tx_data["transactions"] if t["type"] == "spend"), None)
        assert spend_tx is not None
        assert spend_tx["amount"] == 5
        assert spend_tx["category"] == "ai_hint_light"

    @pytest.mark.asyncio
    async def test_spend_cores_insufficient(self, client: AsyncClient, auth_headers: dict, auth_user: User, db_session: AsyncSession):
        """Test spending more cores than available fails"""
        response = await client.post(
            "/api/cores/spend",
            headers=auth_headers,
            json={
                "amount": 200,  # User only has 100
                "category": "ai_hint_light",
                "description": "Expensive AI hint"
            }
        )
        assert response.status_code == 400
        assert "Insufficient cores" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_spend_cores_zero_or_negative(self, client: AsyncClient, auth_headers: dict):
        """Test spending zero or negative cores fails"""
        response = await client.post(
            "/api/cores/spend",
            headers=auth_headers,
            json={
                "amount": 0,
                "category": "ai_hint_light",
                "description": "Zero spend"
            }
        )
        assert response.status_code == 422  # Validation error

        response = await client.post(
            "/api/cores/spend",
            headers=auth_headers,
            json={
                "amount": -5,
                "category": "ai_hint_light",
                "description": "Negative spend"
            }
        )
        assert response.status_code == 422


class TestCoreEarn:
    """Test core earning functionality"""

    @pytest.mark.asyncio
    async def test_earn_cores_checkin(self, client: AsyncClient, auth_headers: dict, auth_user: User, db_session: AsyncSession):
        """Test earning cores from daily check-in"""
        initial_balance = auth_user.cores

        response = await client.post("/api/users/checkin", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        cores_earned = data["cores_earned"]
        assert cores_earned >= 5

        await db_session.refresh(auth_user)
        assert auth_user.cores == initial_balance + cores_earned

        result = await db_session.execute(
            select(CoreTransaction).where(
                CoreTransaction.user_id == auth_user.id,
                CoreTransaction.category == "checkin",
            )
        )
        transactions = list(result.scalars().all())
        assert len(transactions) == 1
        assert transactions[0].type == "earn"
        assert transactions[0].amount == cores_earned
        assert transactions[0].balance_after == auth_user.cores

        duplicate_response = await client.post("/api/users/checkin", headers=auth_headers)
        assert duplicate_response.status_code == 200
        assert duplicate_response.json()["cores_earned"] == 0

        await db_session.refresh(auth_user)
        assert auth_user.cores == initial_balance + cores_earned

        duplicate_result = await db_session.execute(
            select(CoreTransaction).where(
                CoreTransaction.user_id == auth_user.id,
                CoreTransaction.category == "checkin",
            )
        )
        assert len(list(duplicate_result.scalars().all())) == 1


class TestDailyCoreStats:
    """Test daily core statistics"""

    @pytest.mark.asyncio
    async def test_get_daily_summary(self, client: AsyncClient, auth_headers: dict):
        """Test getting daily core summary"""
        response = await client.get("/api/cores/daily-summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "earned_today" in data
        assert "spent_today" in data
        assert "daily_exercises" in data
        assert "daily_accuracy" in data
