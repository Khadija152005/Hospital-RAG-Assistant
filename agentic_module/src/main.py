from fastapi import FastAPI
from api import maintenance as maintenance_router
from core import config
from agents import CoordinatorAgent

app = FastAPI(
    title=config.settings.APP_TITLE,
    version=config.settings.APP_VERSION,
)

app.include_router(maintenance_router.router)


def test_llm_pipeline():

    coordinator = CoordinatorAgent()

    result = coordinator.run()

    # print("\n📊 Workflow Result:")
    # print(result)



if __name__ == "__main__":
    test_llm_pipeline()