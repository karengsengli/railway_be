from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, time, date
from decimal import Decimal
import pandas as pd
from io import BytesIO

from ..models import FareRule, PassengerType
from .schemas import FareRuleCreate, FareRuleUpdate, FareCalculationRequest, FareCalculationResponse, FareMatrix, FareMatrixRow
from ..models import Station
from ..models import TrainLine

class FareRuleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_fare_rule(self, fare_rule: FareRuleCreate) -> FareRule:
        db_fare_rule = FareRule(**fare_rule.model_dump())
        self.db.add(db_fare_rule)
        await self.db.commit()
        await self.db.refresh(db_fare_rule)
        return db_fare_rule

    async def get_fare_rules(self, skip: int = 0, limit: int = 100, line_id: Optional[int] = None) -> List[FareRule]:
        query = select(FareRule).options(
            selectinload(FareRule.line),
            selectinload(FareRule.from_station),
            selectinload(FareRule.to_station),
            selectinload(FareRule.passenger_type)
        )

        if line_id:
            query = query.where(FareRule.line_id == line_id)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_fare_rule(self, fare_rule_id: int) -> Optional[FareRule]:
        query = select(FareRule).options(
            selectinload(FareRule.line),
            selectinload(FareRule.from_station),
            selectinload(FareRule.to_station),
            selectinload(FareRule.passenger_type)
        ).where(FareRule.id == fare_rule_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_fare_rule(self, fare_rule_id: int, fare_rule_update: FareRuleUpdate) -> Optional[FareRule]:
        query = select(FareRule).where(FareRule.id == fare_rule_id)
        result = await self.db.execute(query)
        db_fare_rule = result.scalar_one_or_none()

        if not db_fare_rule:
            return None

        update_data = fare_rule_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_fare_rule, field, value)

        await self.db.commit()
        await self.db.refresh(db_fare_rule)
        return db_fare_rule

    async def delete_fare_rule(self, fare_rule_id: int) -> bool:
        query = select(FareRule).where(FareRule.id == fare_rule_id)
        result = await self.db.execute(query)
        db_fare_rule = result.scalar_one_or_none()

        if not db_fare_rule:
            return False

        await self.db.delete(db_fare_rule)
        await self.db.commit()
        return True

    async def calculate_fare(self, request: FareCalculationRequest) -> Optional[FareCalculationResponse]:
        # Get the fare rule for the specific route and passenger type
        passenger_type_query = select(PassengerType).where(PassengerType.name == request.passenger_type)
        passenger_type_result = await self.db.execute(passenger_type_query)
        passenger_type = passenger_type_result.scalar_one_or_none()

        if not passenger_type:
            return None

        # Check if travel time falls within peak hours (7-9 AM, 5-7 PM)
        peak_hour_multiplier = 1.00
        if request.travel_time:
            travel_hour = request.travel_time.hour
            if (7 <= travel_hour <= 9) or (17 <= travel_hour <= 19):
                peak_hour_multiplier = 1.25  # 25% surcharge during peak hours

        # Find the fare rule
        current_date = date.today()
        fare_rule_query = select(FareRule).where(
            and_(
                FareRule.line_id == request.line_id,
                FareRule.from_station_id == request.from_station_id,
                FareRule.to_station_id == request.to_station_id,
                FareRule.passenger_type_id == passenger_type.id,
                FareRule.valid_from <= current_date,
                or_(FareRule.valid_to.is_(None), FareRule.valid_to >= current_date)
            )
        )

        fare_rule_result = await self.db.execute(fare_rule_query)
        fare_rule = fare_rule_result.scalar_one_or_none()

        if not fare_rule:
            return None

        # Calculate final price
        base_price = fare_rule.base_price
        final_multiplier = peak_hour_multiplier * fare_rule.peak_hour_multiplier
        final_price = base_price * final_multiplier

        return FareCalculationResponse(
            line_id=request.line_id,
            from_station_id=request.from_station_id,
            to_station_id=request.to_station_id,
            passenger_type=request.passenger_type,
            base_price=base_price,
            peak_hour_multiplier=final_multiplier,
            final_price=final_price,
            currency=fare_rule.currency
        )

    async def get_fare_matrix(self, line_id: int) -> Optional[FareMatrix]:
        # Get line information
        line_query = select(TrainLine).where(TrainLine.id == line_id)
        line_result = await self.db.execute(line_query)
        line = line_result.scalar_one_or_none()

        if not line:
            return None

        # Get all fare rules for this line
        fare_rules_query = select(FareRule).options(
            selectinload(FareRule.from_station),
            selectinload(FareRule.to_station),
            selectinload(FareRule.passenger_type)
        ).where(FareRule.line_id == line_id)

        fare_rules_result = await self.db.execute(fare_rules_query)
        fare_rules = fare_rules_result.scalars().all()

        # Group fare rules by route (from_station, to_station)
        route_fares = {}
        currency = "THB"

        for rule in fare_rules:
            route_key = (rule.from_station_id, rule.to_station_id)
            if route_key not in route_fares:
                route_fares[route_key] = {
                    'from_station_name': rule.from_station.name,
                    'to_station_name': rule.to_station.name,
                    'prices': {}
                }

            route_fares[route_key]['prices'][rule.passenger_type.name] = rule.base_price
            currency = rule.currency

        # Convert to matrix format
        matrix_rows = []
        for (from_id, to_id), route_data in route_fares.items():
            prices = route_data['prices']
            matrix_rows.append(FareMatrixRow(
                from_station_id=from_id,
                from_station_name=route_data['from_station_name'],
                to_station_id=to_id,
                to_station_name=route_data['to_station_name'],
                adult_price=prices.get('adult'),
                child_price=prices.get('child'),
                senior_price=prices.get('senior'),
                member_price=prices.get('member')
            ))

        return FareMatrix(
            line_id=line_id,
            line_name=line.name,
            currency=currency,
            fare_rules=matrix_rows
        )

    async def export_fare_matrix_to_excel(self, line_id: int) -> Optional[BytesIO]:
        fare_matrix = await self.get_fare_matrix(line_id)
        if not fare_matrix:
            return None

        # Convert to DataFrame
        data = []
        for rule in fare_matrix.fare_rules:
            data.append({
                'From Station': rule.from_station_name,
                'To Station': rule.to_station_name,
                'Adult Price': float(rule.adult_price) if rule.adult_price else None,
                'Child Price': float(rule.child_price) if rule.child_price else None,
                'Senior Price': float(rule.senior_price) if rule.senior_price else None,
                'Member Price': float(rule.member_price) if rule.member_price else None
            })

        df = pd.DataFrame(data)

        # Create Excel file in memory
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(
                writer,
                sheet_name=f"{fare_matrix.line_name} Fare Matrix",
                index=False
            )

        excel_buffer.seek(0)
        return excel_buffer

    async def import_fare_matrix_from_excel(self, line_id: int, excel_file: BytesIO) -> bool:
        try:
            df = pd.read_excel(excel_file)

            # Validate required columns
            required_columns = ['From Station', 'To Station', 'Adult Price', 'Child Price', 'Senior Price', 'Member Price']
            if not all(col in df.columns for col in required_columns):
                return False

            # Get passenger types
            passenger_types_query = select(PassengerType)
            passenger_types_result = await self.db.execute(passenger_types_query)
            passenger_types = {pt.name: pt.id for pt in passenger_types_result.scalars().all()}

            # Get stations for this line
            stations_query = select(Station).where(Station.line_id == line_id)
            stations_result = await self.db.execute(stations_query)
            stations = {station.name: station.id for station in stations_result.scalars().all()}

            # Process each row
            for _, row in df.iterrows():
                from_station_name = row['From Station']
                to_station_name = row['To Station']

                if from_station_name not in stations or to_station_name not in stations:
                    continue

                from_station_id = stations[from_station_name]
                to_station_id = stations[to_station_name]

                # Create fare rules for each passenger type
                fare_data = {
                    'adult': row.get('Adult Price'),
                    'child': row.get('Child Price'),
                    'senior': row.get('Senior Price'),
                    'member': row.get('Member Price')
                }

                for passenger_type, price in fare_data.items():
                    if pd.notna(price) and passenger_type in passenger_types:
                        # Check if fare rule already exists
                        existing_rule_query = select(FareRule).where(
                            and_(
                                FareRule.line_id == line_id,
                                FareRule.from_station_id == from_station_id,
                                FareRule.to_station_id == to_station_id,
                                FareRule.passenger_type_id == passenger_types[passenger_type]
                            )
                        )
                        existing_result = await self.db.execute(existing_rule_query)
                        existing_rule = existing_result.scalar_one_or_none()

                        if existing_rule:
                            # Update existing rule
                            existing_rule.base_price = Decimal(str(price))
                        else:
                            # Create new rule
                            new_rule = FareRule(
                                line_id=line_id,
                                from_station_id=from_station_id,
                                to_station_id=to_station_id,
                                passenger_type_id=passenger_types[passenger_type],
                                base_price=Decimal(str(price)),
                                currency="THB"
                            )
                            self.db.add(new_rule)

            await self.db.commit()
            return True

        except Exception as e:
            await self.db.rollback()
            return False