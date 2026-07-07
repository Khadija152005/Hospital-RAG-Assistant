from fastapi import FastAPI
from agents import CoordinatorAgent


def main():

    coordinator = CoordinatorAgent()
    coordinator.run()


if __name__ == "__main__":
    main()


# app = FastAPI()
# app.include_router(base.base_router)