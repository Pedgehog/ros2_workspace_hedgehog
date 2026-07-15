from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    label = Column(String, default="Not set")
    underground = Column(String)
    conditions = Column(String)

    envelopes = relationship(
        "SensorEnvelope", back_populates="measurement", cascade="all, delete-orphan"
    )

    def __init__(
        self,
        label: str = "Not set",
        underground: str = "Unknown",
        conditions: str = "Unknown",
    ):
        self.label = label
        self.underground = underground
        self.conditions = conditions


class SensorEnvelope(Base):
    __tablename__ = "sensor_envelopes"

    id = Column(Integer, primary_key=True)
    measurement_id = Column(Integer, ForeignKey("measurements.id"))
    sensor_id = Column(Integer)
    time_axis = Column(JSON)
    amplitudes = Column(JSON)

    measurement = relationship("Measurement", back_populates="envelopes")

    def __init__(
        self, measurement_id: int, sensor_id: int, time_axis: list, amplitudes: list
    ):
        self.measurement_id = measurement_id
        self.sensor_id = sensor_id
        self.time_axis = time_axis
        self.amplitudes = amplitudes
