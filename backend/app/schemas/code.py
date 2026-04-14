"""Pydantic schemas for code execution"""

from typing import Optional
from pydantic import BaseModel, Field


class CodeExecutionRequest(BaseModel):
    """Request schema for code execution"""
    code: str
    language_id: int = 71  # Python default
    stdin: str = ""  # Standard input


class TestCaseInput(BaseModel):
    """Single test case input"""
    input: str = Field(default="", description="Test case input")
    expected_output: str = Field(default="", description="Expected output")


class BatchCodeExecutionRequest(BaseModel):
    """Request schema for batch code execution with multiple test cases"""
    code: str
    language_id: int = 71  # Python default
    test_cases: list[TestCaseInput] = Field(default_factory=list, description="List of test cases")


class TestCaseResult(BaseModel):
    """Result for a single test case"""
    passed: bool
    input: str
    expected: str
    actual: str
    message: Optional[str] = None


class BatchCodeExecutionResponse(BaseModel):
    """Response schema for batch code execution"""
    token: str
    status: str  # Overall status: "Accepted" if all pass, otherwise first error
    status_id: int
    passed_count: int
    total_count: int
    results: list[TestCaseResult]
    time: Optional[str] = None
    memory: Optional[int] = None
    compile_output: Optional[str] = None
    message: Optional[str] = None


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
