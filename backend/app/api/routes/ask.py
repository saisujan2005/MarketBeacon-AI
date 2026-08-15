from fastapi import APIRouter, Depends

from app.db.dependencies import get_current_user
from app.models.user import User
from app.schemas.query import QuestionRequest
from app.rag.market_agent import answer_question

router = APIRouter()


@router.post("/ask")
def ask_question(
    request: QuestionRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Ad-hoc RAG question endpoint.

    Requires authentication: it performs retrieval over stored intelligence and
    issues a billable LLM call, so it must never be anonymously callable.
    """
    result = answer_question(
        request.question,
        user_id=current_user.id,
    )

    return result
