from app.config.database import db

class Facility:
    collection = db["facilities"]

    @staticmethod
    def update_floor_facilities(floor, facilities):
        return Facility.collection.update_one(
            {"floor": floor},
            {"$set": {"facilities": facilities}},
            upsert=True
        )

    @staticmethod
    def get_by_floor(floor):
        return Facility.collection.find_one({"floor": int(floor)})

    @staticmethod
    def get_all():
        return list(Facility.collection.find().sort("floor", 1))
