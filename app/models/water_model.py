from app.config.database import db
from bson import ObjectId

class WaterMachine:
    collection = db["water_machines"]

    @staticmethod
    def create(data):
        return WaterMachine.collection.insert_one(data)

    @staticmethod
    def get_all():
        return list(WaterMachine.collection.find())

    @staticmethod
    def get_by_id(machine_id):
        return WaterMachine.collection.find_one({"_id": ObjectId(machine_id)})

    @staticmethod
    def update(machine_id, data):
        data.pop('_id', None)  # Remove _id to prevent MongoDB immutable field error
        return WaterMachine.collection.update_one(
            {"_id": ObjectId(machine_id)},
            {"$set": data}
        )

    @staticmethod
    def delete(machine_id):
        return WaterMachine.collection.delete_one({"_id": ObjectId(machine_id)})

    @staticmethod
    def get_by_location(block, floor):
        return list(WaterMachine.collection.find({"block": block, "floor": int(floor)}))
