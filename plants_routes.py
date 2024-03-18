from contextlib import asynccontextmanager
from typing import List

from azure.cosmos import PartitionKey, exceptions
from azure.cosmos.aio import CosmosClient
from dotenv import dotenv_values
from fastapi import APIRouter, FastAPI, Request
from fastapi.encoders import jsonable_encoder

from models.plant import Plant

config = dotenv_values(".env")

DATABASE_NAME = "PlantsDB"
CONTAINER_NAME = "plants"

plants_router = APIRouter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.cosmos_client = CosmosClient(
        url=config["COSMOS_ENDPOINT"], credential=config["COSMOS_KEY"]
    )
    await get_or_create_db(app, DATABASE_NAME)
    await get_or_create_container(app, CONTAINER_NAME)
    yield
    await app.cosmos_client.close()


async def get_or_create_db(app: FastAPI, db_name: str):
    try:
        app.database = app.cosmos_client.get_database_client(db_name)
        return await app.database.read()
    except exceptions.CosmosResourceNotFoundError:
        print("Creating database")
        return await app.cosmos_client.create_database(db_name)


async def get_or_create_container(app: FastAPI, container_name: str):
    try:
        app.plants_container = app.database.get_container_client(container_name)
        return await app.plants_container.read()
    except exceptions.CosmosResourceNotFoundError:
        print("Creating container with id as partition key")
        return await app.database.create_container(
            id=container_name, partition_key=PartitionKey(path="/id")
        )
    except exceptions.CosmosHttpResponseError:
        raise


@plants_router.get("/list")
async def read_plants(request: Request):
    plants = [plant async for plant in request.app.plants_container.read_all_items()]
    return plants


@plants_router.post("/add")
async def insert(request: Request, plant: Plant):
    plant = jsonable_encoder(plant)
    new_plant = await request.app.plants_container.create_item(body=plant)
    return new_plant


@plants_router.put("/update", response_model=Plant, response_model_exclude_unset=True)
async def update_plant(request: Request, plant_with_update: Plant):
    existing_plant = await request.app.plants_container.read_item(
        plant_with_update.id, plant_with_update.id
    )
    existing_plant_dict = jsonable_encoder(existing_plant)
    update_data = jsonable_encoder(plant_with_update)
    for k in update_data:
        if k in existing_plant_dict:
            existing_plant_dict[k] = update_data[k]
    updated_plant = await request.app.plants_container.upsert_item(existing_plant_dict)
    return updated_plant


@plants_router.delete("/delete")
async def delete_plant(request: Request, plant_id: str):
    await request.app.plants_container.delete_item(plant_id, plant_id)
    return {"message": "Plant deleted successfully"}
