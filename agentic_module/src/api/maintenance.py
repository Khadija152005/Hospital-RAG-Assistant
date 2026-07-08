from fastapi import APIRouter

from agents import CoordinatorAgent

router = APIRouter(
    prefix="/maintenance",
    tags=["Maintenance"],
)


@router.get("/health")
def health_check():

    return {
        "status": "ok",
        "message": "Maintenance API is running."
    }


@router.post("/run")
def run_maintenance():

    coordinator = CoordinatorAgent()

    result = coordinator.run()

    return result 
