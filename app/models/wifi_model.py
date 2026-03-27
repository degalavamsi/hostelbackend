from app.config.database import db
from bson import ObjectId

class WiFiConfig:
    collection = db["wifi_configs"]

    @staticmethod
    def create(data):
        return WiFiConfig.collection.insert_one(data)

    @staticmethod
    def get_all():
        return list(WiFiConfig.collection.find())

    @staticmethod
    def get_by_id(config_id):
        return WiFiConfig.collection.find_one({"_id": ObjectId(config_id)})

    @staticmethod
    def update(config_id, data):
        from datetime import datetime
        data.pop('_id', None)  # Remove _id to prevent MongoDB immutable field error
        data["last_updated"] = datetime.utcnow()
        return WiFiConfig.collection.update_one(
            {"_id": ObjectId(config_id)},
            {"$set": data}
        )

    @staticmethod
    def delete(config_id):
        return WiFiConfig.collection.delete_one({"_id": ObjectId(config_id)})

    @staticmethod
    def get_by_location(block, floor):
        return WiFiConfig.collection.find_one({"block": block, "floor": int(floor)})
