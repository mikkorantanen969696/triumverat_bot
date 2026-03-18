from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_, or_, func
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json

from database import Base, User, CleaningRequest, RequestPhoto, Payment, City, UserRole, RequestStatus, CleaningType
from config import settings

class DatabaseManager:
    def __init__(self):
        self.engine = create_async_engine(settings.DATABASE_URL)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
    
    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def get_session(self) -> AsyncSession:
        return self.async_session()
    
    # User management
    async def create_user(self, telegram_id: int, username: str = None, role: UserRole = UserRole.CLIENT) -> User:
        async with self.get_session() as session:
            user = User(
                telegram_id=telegram_id,
                username=username,
                role=role
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        async with self.get_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()
    
    async def update_user_role(self, user_id: int, role: UserRole) -> bool:
        async with self.get_session() as session:
            user = await session.get(User, user_id)
            if user:
                user.role = role
                await session.commit()
                return True
            return False
    
    async def get_all_managers(self) -> List[User]:
        async with self.get_session() as session:
            result = await session.execute(
                select(User).where(User.role == UserRole.MANAGER)
            )
            return result.scalars().all()
    
    async def get_cleaners_by_city(self, city: str) -> List[User]:
        async with self.get_session() as session:
            result = await session.execute(
                select(User).where(
                    and_(User.role == UserRole.CLIENT, User.city == city, User.is_active == True)
                )
            )
            return result.scalars().all()
    
    # Request management
    async def create_request(self, request_data: dict) -> CleaningRequest:
        async with self.get_session() as session:
            request = CleaningRequest(**request_data)
            session.add(request)
            await session.commit()
            await session.refresh(request)
            return request
    
    async def get_open_requests_by_city(self, city: str) -> List[CleaningRequest]:
        async with self.get_session() as session:
            result = await session.execute(
                select(CleaningRequest).where(
                    and_(CleaningRequest.city == city, CleaningRequest.status == RequestStatus.OPEN)
                ).order_by(CleaningRequest.created_at.desc())
            )
            return result.scalars().all()
    
    async def assign_request_to_cleaner(self, request_id: int, cleaner_id: int) -> bool:
        async with self.get_session() as session:
            request = await session.get(CleaningRequest, request_id)
            if request and request.status == RequestStatus.OPEN:
                request.cleaner_id = cleaner_id
                request.status = RequestStatus.IN_PROGRESS
                await session.commit()
                return True
            return False
    
    async def complete_request(self, request_id: int) -> bool:
        async with self.get_session() as session:
            request = await session.get(CleaningRequest, request_id)
            if request:
                request.status = RequestStatus.COMPLETED
                request.completed_at = datetime.utcnow()
                await session.commit()
                return True
            return False
    
    async def get_requests_by_manager(self, manager_id: int) -> List[CleaningRequest]:
        async with self.get_session() as session:
            result = await session.execute(
                select(CleaningRequest).where(CleaningRequest.manager_id == manager_id)
                .order_by(CleaningRequest.created_at.desc())
            )
            return result.scalars().all()
    
    async def get_requests_by_cleaner(self, cleaner_id: int) -> List[CleaningRequest]:
        async with self.get_session() as session:
            result = await session.execute(
                select(CleaningRequest).where(CleaningRequest.cleaner_id == cleaner_id)
                .order_by(CleaningRequest.created_at.desc())
            )
            return result.scalars().all()
    
    # Photo management
    async def add_request_photo(self, request_id: int, file_id: str, photo_type: str) -> RequestPhoto:
        async with self.get_session() as session:
            photo = RequestPhoto(
                request_id=request_id,
                file_id=file_id,
                photo_type=photo_type
            )
            session.add(photo)
            await session.commit()
            await session.refresh(photo)
            return photo
    
    async def get_request_photos(self, request_id: int) -> List[RequestPhoto]:
        async with self.get_session() as session:
            result = await session.execute(
                select(RequestPhoto).where(RequestPhoto.request_id == request_id)
                .order_by(RequestPhoto.uploaded_at)
            )
            return result.scalars().all()
    
    # Payment management
    async def create_payment(self, payment_data: dict) -> Payment:
        async with self.get_session() as session:
            payment = Payment(**payment_data)
            session.add(payment)
            await session.commit()
            await session.refresh(payment)
            return payment
    
    async def complete_payment(self, payment_id: int) -> bool:
        async with self.get_session() as session:
            payment = await session.get(Payment, payment_id)
            if payment:
                payment.status = "completed"
                payment.completed_at = datetime.utcnow()
                await session.commit()
                return True
            return False
    
    # Statistics
    async def get_admin_statistics(self) -> Dict[str, Any]:
        async with self.get_session() as session:
            # Общая статистика
            total_requests = await session.scalar(select(func.count(CleaningRequest.id)))
            completed_requests = await session.scalar(
                select(func.count(CleaningRequest.id)).where(CleaningRequest.status == RequestStatus.COMPLETED)
            )
            total_revenue = await session.scalar(
                select(func.sum(CleaningRequest.price)).where(CleaningRequest.status == RequestStatus.COMPLETED)
            ) or 0
            
            # Статистика по менеджерам
            manager_stats = await session.execute(
                select(
                    User.full_name,
                    func.count(CleaningRequest.id).label('requests_count'),
                    func.sum(CleaningRequest.price).label('total_revenue')
                ).select_from(User).join(CleaningRequest, User.id == CleaningRequest.manager_id)
                .where(User.role == UserRole.MANAGER)
                .group_by(User.id, User.full_name)
            )
            
            # Статистика по городам
            city_stats = await session.execute(
                select(
                    CleaningRequest.city,
                    func.count(CleaningRequest.id).label('requests_count'),
                    func.sum(CleaningRequest.price).label('total_revenue')
                ).group_by(CleaningRequest.city)
            )
            
            # Статистика по клинерам
            cleaner_stats = await session.execute(
                select(
                    User.full_name,
                    func.count(CleaningRequest.id).label('completed_requests'),
                    func.sum(CleaningRequest.price).label('total_earned')
                ).select_from(User).join(CleaningRequest, User.id == CleaningRequest.cleaner_id)
                .where(User.role == UserRole.CLIENT, CleaningRequest.status == RequestStatus.COMPLETED)
                .group_by(User.id, User.full_name)
            )
            
            return {
                "total_requests": total_requests,
                "completed_requests": completed_requests,
                "total_revenue": total_revenue,
                "manager_stats": [dict(row) for row in manager_stats],
                "city_stats": [dict(row) for row in city_stats],
                "cleaner_stats": [dict(row) for row in cleaner_stats]
            }
    
    async def get_manager_statistics(self, manager_id: int) -> Dict[str, Any]:
        async with self.get_session() as session:
            # Статистика менеджера
            total_requests = await session.scalar(
                select(func.count(CleaningRequest.id)).where(CleaningRequest.manager_id == manager_id)
            )
            completed_requests = await session.scalar(
                select(func.count(CleaningRequest.id)).where(
                    and_(CleaningRequest.manager_id == manager_id, CleaningRequest.status == RequestStatus.COMPLETED)
                )
            )
            total_revenue = await session.scalar(
                select(func.sum(CleaningRequest.price)).where(
                    and_(CleaningRequest.manager_id == manager_id, CleaningRequest.status == RequestStatus.COMPLETED)
                )
            ) or 0
            
            # Детальная информация по заявкам
            requests = await session.execute(
                select(CleaningRequest).where(CleaningRequest.manager_id == manager_id)
                .order_by(CleaningRequest.created_at.desc())
                .limit(10)
            )
            
            return {
                "total_requests": total_requests,
                "completed_requests": completed_requests,
                "total_revenue": total_revenue,
                "recent_requests": [
                    {
                        "id": req.id,
                        "address": req.address,
                        "client_name": req.client_name,
                        "price": req.price,
                        "status": req.status.value,
                        "created_at": req.created_at.isoformat()
                    }
                    for req in requests.scalars().all()
                ]
            }

db = DatabaseManager()
