"""Pydantic schemas for code execution"""

from typing import Optional
from pydantic import BaseModel


class CodeExecutionRequest(BaseModel):
    """Request schema for code execution"""
    code: str
    language_id: int = 71  # Python default
    stdin: str = ""  # Standard input


class CodeExecutionResponse(BaseModel):
    """Response schema for code execution (洛谷风格)"""
    token: str
    status: str  # "Accepted", "Wrong Answer", etc.
    status_id: int  # Judge0 status ID
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    message: Optional[str] = None
    time: Optional[str] = None
    memory: Optional[int] = None
    exit_code: Optional[int] = None

    model_config = {"from_attributes": True}


class LanguageInfo(BaseModel):
    """Schema for supported language info"""
    id: int
    name: str
    monaco_language: str  # Monaco editor language identifier
