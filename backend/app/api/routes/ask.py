from fastapi import APIRouter

from app.schemas.query import QuestionRequest
from app.rag.market_agent import answer_question

router = APIRouter()

@router.post("/ask")
def ask_question(
    request: QuestionRequest
):

    result = answer_question(
        request.question
    )

    return result