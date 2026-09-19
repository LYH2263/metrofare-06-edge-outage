from fastapi import APIRouter, HTTPException
from app.schemas.disruption import DisruptionCreate, DisruptionLift
from app.services.metro_service import DisruptionError, MetroService

router = APIRouter(tags=["disruptions"])


@router.get("/disruptions")
def list_disruptions():
    with MetroService() as s:
        return {"items": s.disruptions()}


@router.post("/disruptions")
def register_disruption(body: DisruptionCreate):
    try:
        with MetroService() as s:
            return s.register_disruption(body.a, body.b, body.reason)
    except DisruptionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/disruptions/lift")
def lift_disruption(body: DisruptionLift):
    try:
        with MetroService() as s:
            return s.lift_disruption(body.a, body.b)
    except DisruptionError as e:
        raise HTTPException(status_code=400, detail=str(e))
