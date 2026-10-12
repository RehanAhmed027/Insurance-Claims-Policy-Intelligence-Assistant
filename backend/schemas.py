from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=2000,
        description="Insurance question asked by the user"
    )

    product_name: str = Field(
        default="",
        max_length=100
    )


class PolicyQuestionRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=2000
    )

    product_name: str = Field(
        min_length=3,
        max_length=100
    )