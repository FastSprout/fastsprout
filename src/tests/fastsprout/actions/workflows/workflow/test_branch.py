from typing import assert_type

import pytest

from fastsprout.actions import Workflow, action
from fastsprout.core import BaseSchema


class Decision(BaseSchema):
    approved: bool


class Approved(BaseSchema):
    value: str


class Rejected(BaseSchema):
    code: int


async def test_branch_extension_preserves_original_workflow_contract() -> None:
    @action
    async def decide(decision: Decision) -> Approved | Rejected:
        return (
            Approved(value="paid") if decision.approved else Rejected(code=409)
        )

    @action
    async def approve(result: Approved) -> Approved:
        return result

    @action
    async def reject(result: Rejected) -> Rejected:
        return result

    approvals = Workflow(decide).branch(Approved, approve)
    all_outcomes = approvals.branch(Rejected, reject)
    approved_results = [
        item async for item in approvals(Decision(approved=True))
    ]
    approved = approved_results[0]
    assert_type(approved, Approved)
    assert approved.value == "paid"
    continued = approvals.then(approve)
    assert_type(continued, Workflow[Decision, Approved])
    assert [
        item async for item in Workflow(continued)(Decision(approved=True))
    ] == approved_results
    rejected_results = [
        item async for item in all_outcomes(Decision(approved=False))
    ]
    rejected = rejected_results[0]
    assert_type(rejected, Approved | Rejected)
    assert isinstance(rejected, Rejected)
    assert rejected.code == 409
    with pytest.raises(LookupError, match="No workflow branch for Rejected"):
        async for _ in approvals(Decision(approved=False)):
            pytest.fail("Unmatched branch produced a result")
