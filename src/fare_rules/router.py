from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from io import BytesIO

from ..database import get_db
from .service import FareRuleService
from .schemas import (
    FareRule, FareRuleCreate, FareRuleUpdate, FareCalculationRequest,
    FareCalculationResponse, FareMatrix, PassengerType, PassengerTypeCreate
)

router = APIRouter()

@router.post("/fare-rules/", response_model=FareRule)
async def create_fare_rule(
    fare_rule: FareRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    service = FareRuleService(db)
    return await service.create_fare_rule(fare_rule)

@router.get("/fare-rules/", response_model=List[FareRule])
async def get_fare_rules(
    skip: int = 0,
    limit: int = 100,
    line_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    service = FareRuleService(db)
    return await service.get_fare_rules(skip=skip, limit=limit, line_id=line_id)

@router.get("/fare-rules/{fare_rule_id}", response_model=FareRule)
async def get_fare_rule(
    fare_rule_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = FareRuleService(db)
    fare_rule = await service.get_fare_rule(fare_rule_id)
    if not fare_rule:
        raise HTTPException(status_code=404, detail="Fare rule not found")
    return fare_rule

@router.put("/fare-rules/{fare_rule_id}", response_model=FareRule)
async def update_fare_rule(
    fare_rule_id: int,
    fare_rule_update: FareRuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    service = FareRuleService(db)
    fare_rule = await service.update_fare_rule(fare_rule_id, fare_rule_update)
    if not fare_rule:
        raise HTTPException(status_code=404, detail="Fare rule not found")
    return fare_rule

@router.delete("/fare-rules/{fare_rule_id}")
async def delete_fare_rule(
    fare_rule_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = FareRuleService(db)
    deleted = await service.delete_fare_rule(fare_rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Fare rule not found")
    return {"message": "Fare rule deleted successfully"}

@router.post("/calculate-fare/", response_model=FareCalculationResponse)
async def calculate_fare(
    request: FareCalculationRequest,
    db: AsyncSession = Depends(get_db)
):
    service = FareRuleService(db)
    result = await service.calculate_fare(request)
    if not result:
        raise HTTPException(status_code=404, detail="Fare rule not found for the given parameters")
    return result

@router.get("/fare-matrix/{line_id}", response_model=FareMatrix)
async def get_fare_matrix(
    line_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = FareRuleService(db)
    matrix = await service.get_fare_matrix(line_id)
    if not matrix:
        raise HTTPException(status_code=404, detail="Line not found or no fare rules exist")
    return matrix

@router.get("/fare-matrix/{line_id}/export")
async def export_fare_matrix(
    line_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = FareRuleService(db)
    excel_file = await service.export_fare_matrix_to_excel(line_id)
    if not excel_file:
        raise HTTPException(status_code=404, detail="Line not found or no fare rules exist")

    return StreamingResponse(
        BytesIO(excel_file.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=fare_matrix_line_{line_id}.xlsx"}
    )

@router.post("/fare-matrix/{line_id}/import")
async def import_fare_matrix(
    line_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx) are supported")

    service = FareRuleService(db)
    content = await file.read()
    excel_file = BytesIO(content)

    success = await service.import_fare_matrix_from_excel(line_id, excel_file)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to import fare matrix")

    return {"message": "Fare matrix imported successfully"}