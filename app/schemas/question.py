from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class QuestionBase(BaseModel):
    """题目基础模型"""
    content: str = Field(..., min_length=1, max_length=1000, description="题目内容")
    type: str = Field(..., regex="^(choice|essay|judgment)$", description="题目类型")
    options: Optional[List[str]] = Field(None, min_items=2, max_items=5, description="选项列表")
    answer: Any = Field(..., description="答案")
    difficulty: float = Field(..., ge=0, le=1, description="难度系数")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v not in ['choice', 'essay', 'judgment']:
            raise ValueError('不支持的题目类型')
        return v
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v, info):
        if info.data.get('type') == 'choice' and not v:
            raise ValueError('选择题必须包含选项')
        return v
        
    @field_validator('answer')
    @classmethod
    def validate_answer(cls, v, info):
        if info.data.get('type') == 'choice':
            if not isinstance(v, str):
                raise ValueError('选择题答案必须是字符串')
            if info.data.get('options') and v not in info.data['options']:
                raise ValueError('选择题答案必须在选项列表中')
        elif info.data.get('type') == 'judgment':
            if not isinstance(v, bool):
                raise ValueError('判断题答案必须是布尔值')
        elif info.data.get('type') == 'essay':
            if not isinstance(v, str):
                raise ValueError('问答题答案必须是字符串')
        return v

class QuestionCreate(QuestionBase):
    """创建题目模型"""
    pass

class QuestionUpdate(QuestionBase):
    """更新题目模型"""
    content: Optional[str] = Field(None, min_length=1, max_length=1000)
    type: Optional[str] = Field(None, regex="^(choice|essay|judgment)$")
    options: Optional[List[str]] = Field(None, min_items=2, max_items=5)
    answer: Optional[Any] = None
    difficulty: Optional[float] = Field(None, ge=0, le=1)

class Question(QuestionBase):
    """题目模型"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QuestionTransform(BaseModel):
    """题目变形模型"""
    question: Question
    transform_type: str = Field(..., regex="^(paraphrase|difficulty_adjust|context_change|format_change|perspective_change)$", description="变形类型")
    
    @field_validator('transform_type')
    @classmethod
    def validate_transform_type(cls, v):
        if v not in ['paraphrase', 'difficulty_adjust', 'context_change', 'format_change', 'perspective_change']:
            raise ValueError('不支持的变形类型')
        return v 