from sqlalchemy import Column, SmallInteger, BigInteger, Integer, String, DateTime

from server.database import Base


class RestaurantStatus(Base):
    __tablename__ = "restaurant_status"

    observation_id = Column(BigInteger, primary_key=True, autoincrement='auto')
    store_id = Column(BigInteger, nullable=False)
    timestamp_utc = Column(DateTime(timezone=False), nullable=False)
    status = Column(String(8), nullable=False)

class BusinessHours(Base):
    __tablename__ = "business_hours"

    id = Column(Integer, primary_key=True, autoincrement='auto')
    store_id = Column(BigInteger, nullable=False)
    day_of_week = Column(SmallInteger, nullable=False)
    start_time_local = Column(DateTime(timezone=False), nullable=False)
    end_time_local = Column(DateTime(timezone=False), nullable=False)

class RestaurantTimezone(Base):
    __tablename__ = "restaurant_timezone"

    store_id = Column(BigInteger, primary_key=True)
    timezone_str = Column(String(256), default='America/Chicago')

class Report(Base):
    __tablename__ = "reports"

    report_id = Column(Integer, primary_key=True, autoincrement='auto')
    status = Column(String(10), default='Running')
    report_csv_url = Column(String(2048))
