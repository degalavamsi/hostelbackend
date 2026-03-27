from app.config.database import db
from bson import ObjectId

class WashingMachine:
    collection = db["washing_machines"]

    @staticmethod
    def create(data):
        return WashingMachine.collection.insert_one(data)

    @staticmethod
    def get_all():
        return list(WashingMachine.collection.find())

    @staticmethod
    def get_by_id(machine_id):
        return WashingMachine.collection.find_one({"_id": ObjectId(machine_id)})

    @staticmethod
    def update(machine_id, data):
        data.pop('_id', None)  # Remove _id to prevent MongoDB immutable field error
        return WashingMachine.collection.update_one(
            {"_id": ObjectId(machine_id)},
            {"$set": data}
        )

    @staticmethod
    def delete(machine_id):
        return WashingMachine.collection.delete_one({"_id": ObjectId(machine_id)})

    @staticmethod
    def get_by_location(block, floor):
        return list(WashingMachine.collection.find({"block": block, "floor": int(floor)}))
