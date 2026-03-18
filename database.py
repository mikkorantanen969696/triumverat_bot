from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    CLEANER = "client"

class RequestStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class CleaningType(enum.Enum):
    REGULAR = "regular"
    GENERAL = "general"
    POST_CONSTRUCTION = "post_construction"
    WINDOW = "window"
    DRY_CLEANING = "dry_cleaning"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(50), nullable=True)
    full_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    role = Column(Enum(UserRole), nullable=False)
    city = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    password = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    created_requests = relationship("CleaningRequest", foreign_keys="CleaningRequest.manager_id", back_populates="manager")
    assigned_requests = relationship("CleaningRequest", foreign_keys="CleaningRequest.cleaner_id", back_populates="cleaner")
    payments_sent = relationship("Payment", foreign_keys="Payment.sender_id", back_populates="sender")
    payments_received = relationship("Payment", foreign_keys="Payment.receiver_id", back_populates="receiver")

class CleaningRequest(Base):
    __tablename__ = "cleaning_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cleaner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    city = Column(String(50), nullable=False)
    address = Column(Text, nullable=False)
    client_name = Column(String(100), nullable=False)
    client_phone = Column(String(20), nullable=False)
    date_time = Column(DateTime(timezone=True), nullable=False)
    cleaning_type = Column(Enum(CleaningType), nullable=False)
    estimated_duration = Column(Integer, nullable=False)  # в часах
    price = Column(Float, nullable=False)
    equipment_available = Column(Boolean, default=False)
    cleaning_supplies_available = Column(Boolean, default=False)
    additional_info = Column(Text, nullable=True)
    status = Column(Enum(RequestStatus), default=RequestStatus.OPEN)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    manager = relationship("User", foreign_keys=[manager_id], back_populates="created_requests")
    cleaner = relationship("User", foreign_keys=[cleaner_id], back_populates="assigned_requests")
    photos = relationship("RequestPhoto", back_populates="request")
    payments = relationship("Payment", back_populates="request")

class RequestPhoto(Base):
    __tablename__ = "request_photos"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("cleaning_requests.id"), nullable=False)
    file_id = Column(String(255), nullable=False)
    photo_type = Column(String(20), nullable=False)  # 'before' или 'after'
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    request = relationship("CleaningRequest", back_populates="photos")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("cleaning_requests.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_type = Column(String(20), nullable=False)  # 'client_payment' или 'cleaner_payment'
    status = Column(String(20), default="pending")  # 'pending', 'completed', 'failed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    request = relationship("CleaningRequest", back_populates="payments")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="payments_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="payments_received")

class City(Base):
    __tablename__ = "cities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    telegram_topic_id = Column(Integer, nullable=True)  # ID подтемы в супергруппе
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
