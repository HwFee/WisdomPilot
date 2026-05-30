"""Code execution API endpoints"""

import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.utils.deps import get_current_active_user
from app.models.user import User
from app.schemas.code import (
    CodeExecutionRequest,
    CodeExecutionResponse,
    LanguageInfo,
    BatchCodeExecutionRequest,
    BatchCodeExecutionResponse,
    TestCaseResult,
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
    except httpx.HTTPStatusError as e:
        logger.error("Judge0 HTTP error: %s %s", e.response.status_code, e)
        if e.response.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁，请稍后再试。Judge0 API 有限流保护。"
            )
        raise HTTPException(
            status_code=503,
            detail="Code execution service returned an error. Please try again later."
        )
    except httpx.RequestError as e:
        logger.error("Judge0 request failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Code execution service is unavailable. Please try again later."
        )


@router.post("/execute-batch", response_model=BatchCodeExecutionResponse)
async def execute_code_batch(
    request: BatchCodeExecutionRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    judge0: Judge0Service = Depends(get_judge0_service),
):
    """
    Execute code against multiple test cases in a single request.

    This is the recommended approach for programming exercises with multiple test cases.
    - Runs code once with all test inputs combined
    - Returns results for each test case
    - Avoids rate limiting issues

    Request body:
    - code: Source code to execute
    - language_id: Language ID (50=C, 71=Python, etc.)
    - test_cases: List of {input: str, expected_output: str}
    """
    try:
        # Validate language_id
        valid_language_ids = [lang["id"] for lang in SUPPORTED_LANGUAGES]
        if request.language_id not in valid_language_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language_id. Supported: {valid_language_ids}"
            )

        # Validate test case count (max 50 to avoid large payloads)
        if len(request.test_cases) > 50:
            raise HTTPException(
                status_code=400,
                detail="Too many test cases. Maximum 50 test cases allowed per submission."
            )

        if len(request.test_cases) == 0:
            raise HTTPException(
                status_code=400,
                detail="At least one test case is required."
            )

        # Convert test cases to dict format
        test_cases = [
            {"input": tc.input, "expected_output": tc.expected_output}
            for tc in request.test_cases
        ]

        # Execute batch
        result = await judge0.execute_batch(
            code=request.code,
            language_id=request.language_id,
            test_cases=test_cases,
        )

        return BatchCodeExecutionResponse(
            token=result.get("token", ""),
            status=result.get("status", "Unknown"),
            status_id=result.get("status_id", 13),
            passed_count=result.get("passed_count", 0),
            total_count=result.get("total_count", 0),
            results=[TestCaseResult(**r) for r in result.get("results", [])],
            time=result.get("time"),
            memory=result.get("memory"),
            compile_output=result.get("compile_output"),
            message=result.get("message"),
        )

    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        logger.error("Judge0 HTTP error: %s %s", e.response.status_code, e)
        if e.response.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁，请稍后再试。"
            )
        raise HTTPException(
            status_code=503,
            detail="Code execution service returned an error."
        )
    except httpx.RequestError as e:
        logger.error("Judge0 request failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Code execution service is unavailable."
        )
    except Exception:
        logger.exception("Batch execution error")
        raise HTTPException(
            status_code=500,
            detail="代码执行服务内部错误，请稍后重试。"
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
