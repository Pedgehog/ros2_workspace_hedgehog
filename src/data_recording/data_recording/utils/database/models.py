from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


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

    pictures = relationship(
        "MeasurementPicture", back_populates="measurement", cascade="all, delete-orphan"
    )

    servo_positions = relationship(
        "ServoPosition", back_populates="measurement", cascade="all, delete-orphan"
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


class MeasurementPicture(Base):
    __tablename__ = "measurements_pictures"

    id = Column(Integer, primary_key=True)
    path = Column(String, default="")

    measurement_id = Column(
        Integer, ForeignKey("measurements.id", ondelete="CASCADE"), nullable=False
    )

    measurement = relationship("Measurement", back_populates="pictures")

    def __init__(self, measurement_id: int, path: str):
        self.measurement_id = measurement_id
        self.path = path


class ServoPosition(Base):
    __tablename__ = "servo_positions"

    id = Column(Integer, primary_key=True)
    group_name = Column(String, nullable=False)
    y_value = Column(Integer, nullable=False)
    z_value = Column(Integer, nullable=False)

    measurement_id = Column(
        Integer, ForeignKey("measurements.id", ondelete="CASCADE"), nullable=False
    )

    measurement = relationship("Measurement", back_populates="servo_positions")

    def __init__(
        self, measurement_id: int, group_name: str, y_value: int, z_value: int
    ):
        self.measurement_id = measurement_id
        self.group_name = group_name
        self.y_value = y_value
        self.z_value = z_value
