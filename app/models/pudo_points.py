from app.extensions import db
from mongoengine.fields import StringField, FloatField, PointField

class PUDOPoint(db.Document):
    """
    Model to represent a Pickup/Drop-off (PUDO) point.
    """
    name = StringField(max_length=100, required=True)
    address = StringField(max_length=255, required=True)
    latitude = FloatField(required=True)
    longitude = FloatField(required=True)
    # Optional: GeoJSON point for geospatial queries
    # location = PointField()

    def __repr__(self):
        return f"PUDOPoint('{self.name}', '{self.address}')"

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude
        }
