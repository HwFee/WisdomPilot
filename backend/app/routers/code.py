"""Code execution API endpoints"""

import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.deps import get_current_active_user
from app.models.user import User
from app.schemas.code import (
    CodeExecutionRequest,
    CodeExecutionResponse,
    LanguageInfo,
)
from app.services.judge0 import Judge0Service, LANGUAGE_PYTHON, LANGUAGE_JAVASCRIPT, LANGUAGE_TYPESCRIPT, LANGUAGE_C, LANGUAGE_CPP

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/code", tags=["code"])

# Supported languages configuration
SUPPORTED_LANGUAGES = [
    {"id": LANGUAGE_PYTHON, "name": "Python 3", "monaco_language": "python"},
    {"id": LANGUAGE_JAVASCRIPT, "name": "JavaScript", "monaco_language": "javascript"},
    {"id": LANGUAGE_TYPESCRIPT, "name": "TypeScript", "monaco_language": "typescript"},
    {"id": LANGUAGE_C, "name": "C", "monaco_language": "c"},
    {"id": LANGUAGE_CPP, "name": "C++", "monaco_language": "cpp"},
]


async def get_judge0_service() -> Judge0Service:
    """Dependency to get Judge0 service instance"""
    return Judge0Service()


@router.post("/execute", response_model=CodeExecutionResponse)
async def execute_code(
    request: CodeExecutionRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    judge0: Judge0Service = Depends(get_judge0_service),
):
    """
    Execute code using Judge0 API.

    Returns execution result including stdout, stderr, and status.
    """
    try:
        # Validate language_id
        valid_language_ids = [lang["id"] for lang in SUPPORTED_LANGUAGES]
        if request.language_id not in valid_language_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language_id. Supported: {valid_language_ids}"
            )

        result = await judge0.execute_code(
            code=request.code,
            language_id=request.language_id,
            stdin=request.stdin,
        )

        # Format the output in 洛谷 style
        formatted = judge0.format_output(result)

        return CodeExecutionResponse(
            token=formatted["token"],
            status=formatted["status"],
            status_id=formatted["status_id"],
            stdout=formatted["stdout"],
            stderr=formatted["stderr"],
            compile_output=formatted["compile_output"],
            message=formatted["message"],
            time=formatted["time"],
            memory=formatted["memory"],
            exit_code=formatted["exit_code"],
        )

    except HTTPException:
        raise
    except httpx.RequestError as e:
        logger.error("Judge0 request failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Code execution service is unavailable. Please try again later."
        )
    except httpx.HTTPStatusError as e:
        logger.error("Judge0 HTTP error: %s %s", e.response.status_code, e)
        raise HTTPException(
            status_code=503,
            detail="Code execution service returned an error. Please try again later."
        )


@router.get("/languages", response_model=list[LanguageInfo])
async def get_supported_languages(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get list of supported programming languages"""
    return [
        LanguageInfo(
            id=lang["id"],
            name=lang["name"],
            monaco_language=lang["monaco_language"]
        )
        for lang in SUPPORTED_LANGUAGES
    ]
