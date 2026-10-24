from typing import assert_type

import pytest

from fastsprout.actions import Workflow, action
from fastsprout.core import BaseSchema
from fastsprout.testing.core import given, then, when


class Decision(BaseSchema):
    approved: bool


class Approved(BaseSchema):
    value: str


class Rejected(BaseSchema):
    code: int


@action
async def decide(decision: Decision) -> Approved | Rejected:
    return Approved(value="paid") if decision.approved else Rejected(code=409)


@action
async def approve(result: Approved) -> Approved:
    return result


@action
async def reject(result: Rejected) -> Rejected:
    return result


class TestBranchExtension:
    @given("a workflow routing approved decisions")
    def approvals(self) -> Workflow[Decision, Approved, Approved | Rejected]:
        return Workflow(decide).branch(Approved, approve)

    @when("the workflow is extended with a rejection branch")
    async def outcomes(
        self,
        approvals: Workflow[Decision, Approved, Approved | Rejected],
        accepted: bool,
    ) -> list[Approved | Rejected]:
        extended = approvals.branch(Rejected, reject)
        return [item async for item in extended(Decision(approved=accepted))]

    @pytest.mark.parametrize("accepted", [False, True])
    @then("both the original and added branches remain reachable")
    def test_extension(
        self, outcomes: list[Approved | Rejected], accepted: bool
    ) -> None:
        assert_type(outcomes, list[Approved | Rejected])
        assert outcomes == (
            [Approved(value="paid")] if accepted else [Rejected(code=409)]
        )

    @when("the original workflow is continued and nested")
    async def continued(
        self, approvals: Workflow[Decision, Approved, Approved | Rejected]
    ) -> tuple[list[Approved], list[Approved]]:
        nested = approvals.then(approve)
        assert_type(nested, Workflow[Decision, Approved])
        payload = Decision(approved=True)
        return (
            [item async for item in approvals(payload)],
            [item async for item in Workflow(nested)(payload)],
        )

    @then("continuation preserves the original output contract")
    def test_continuation(
        self, continued: tuple[list[Approved], list[Approved]]
    ) -> None:
        original, nested = continued
        assert original == nested == [Approved(value="paid")]

    @when("a rejected decision reaches the original workflow")
    async def unmatched(
        self, approvals: Workflow[Decision, Approved, Approved | Rejected]
    ) -> LookupError | None:
        try:
            async for _ in approvals(Decision(approved=False)):
                pass
        except LookupError as error:
            return error
        return None

    @then("the original workflow still rejects unmatched decisions")
    def test_unmatched(self, unmatched: LookupError | None) -> None:
        assert isinstance(unmatched, LookupError)
        assert str(unmatched) == "No workflow branch for Rejected"
