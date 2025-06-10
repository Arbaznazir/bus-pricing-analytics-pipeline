"""
Bus Data Simulator with Faker Integration

Generates realistic bus schedule and seat occupancy data using Faker library
for consistent, professional fake data with intentional anomalies for testing
data quality measures in the ETL pipeline.
"""

import json
import os
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path
from faker import Faker
from faker.providers import automotive, company, person

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Faker with Indian locale for realistic Indian data
fake = Faker('en_IN')  # Use single locale to avoid provider issues

# Seed for consistent fake data generation during development
fake.seed_instance(12345)

# Enhanced Indian routes with realistic cities and distances
ROUTES = [
    {"route_id": 1, "origin": "Mumbai", "destination": "Pune",
        "distance_km": 148.0, "popularity": "high"},
    {"route_id": 2, "origin": "Delhi", "destination": "Agra",
        "distance_km": 206.0, "popularity": "high"},
    {"route_id": 3, "origin": "Bangalore", "destination": "Chennai",
        "distance_km": 346.0, "popularity": "high"},
    {"route_id": 4, "origin": "Kolkata", "destination": "Darjeeling",
        "distance_km": 595.0, "popularity": "medium"},
    {"route_id": 5, "origin": "Jaipur", "destination": "Udaipur",
        "distance_km": 421.0, "popularity": "medium"},
    {"route_id": 6, "origin": "Hyderabad", "destination": "Vijayawada",
        "distance_km": 275.0, "popularity": "medium"},
    {"route_id": 7, "origin": "Ahmedabad", "destination": "Rajkot",
        "distance_km": 216.0, "popularity": "low"},
    {"route_id": 8, "origin": "Kochi", "destination": "Thiruvananthapuram",
        "distance_km": 205.0, "popularity": "low"},
    {"route_id": 9, "origin": "Indore", "destination": "Bhopal",
        "distance_km": 195.0, "popularity": "low"},
    {"route_id": 10, "origin": "Guwahati", "destination": "Shillong",
        "distance_km": 103.0, "popularity": "low"},
]

# Enhanced operators with realistic company names and details


def generate_operators():
    """Generate realistic bus operators using Faker"""
    operator_types = [
        "Express", "Travels", "Transport", "Lines", "Tours", "Services",
        "Motors", "Roadways", "Transit", "Logistics"
    ]

    operators = []
    for i in range(1, 13):  # 12 operators for more variety
        if i <= 6:
            # Use some traditional Indian operator names
            base_names = ["RedBus", "VRL", "KSRTC", "Orange", "SRS", "TSRTC"]
            company_name = f"{base_names[i-1]} {random.choice(operator_types)}"
        else:
            # Generate new realistic company names using Faker
            company_name = f"{fake.company().replace(',', '').replace('.', '')} {random.choice(operator_types)}"

        operators.append({
            "operator_id": i,
            "name": company_name,
            "contact_email": fake.company_email(),
            "phone": fake.phone_number(),
            "registration_year": fake.year(),
            "is_active": fake.boolean(chance_of_getting_true=90),
            "headquarters": fake.city(),
        })

    return operators


OPERATORS = generate_operators()

# Seat types and their typical counts
SEAT_TYPES = {
    "regular": {"typical_count": 40, "base_fare_multiplier": 1.0},
    "premium": {"typical_count": 20, "base_fare_multiplier": 1.5},
    "sleeper": {"typical_count": 30, "base_fare_multiplier": 2.0}
}


class BusDataSimulator:
    """Simulates bus schedule and seat occupancy data with Faker integration"""

    def __init__(self, output_dir: str = "./data/raw", seed: int = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize faker instance for this simulator
        self.fake = Faker('en_IN')
        if seed:
            self.fake.seed_instance(seed)

        # Add realistic Indian names and data
        self.passenger_names = [fake.name() for _ in range(100)]
        self.booking_agents = [fake.name() for _ in range(20)]

    def generate_schedule_id(self) -> int:
        """Generate a unique schedule ID using Faker"""
        # Use Faker's random number generator for more consistent results
        return self.fake.random_int(min=100000, max=999999)

    def simulate_schedule(self, record_date: datetime) -> Dict[str, Any]:
        """
        Simulate a bus schedule for a given date with enhanced realism

        Args:
            record_date: Date for which to generate schedule

        Returns:
            Dictionary containing schedule information
        """
        route = self.fake.random_element(ROUTES)
        operator = self.fake.random_element(OPERATORS)

        # Generate departure time (6 AM to 11 PM) with realistic patterns
        # More buses during popular hours
        popular_hours = [7, 8, 9, 17, 18, 19, 20]
        if self.fake.boolean(chance_of_getting_true=40):
            departure_hour = self.fake.random_element(popular_hours)
        else:
            departure_hour = self.fake.random_int(min=6, max=23)

        departure_minute = self.fake.random_element([0, 15, 30, 45])
        departure = record_date.replace(
            hour=departure_hour,
            minute=departure_minute,
            second=0,
            microsecond=0
        )

        # Calculate arrival time based on distance and realistic traffic conditions
        base_speed = 55  # Average speed in km/h
        # Adjust speed based on popularity (more traffic on popular routes)
        if route["popularity"] == "high":
            speed = self.fake.random_int(min=45, max=60)
        elif route["popularity"] == "medium":
            speed = self.fake.random_int(min=50, max=65)
        else:
            speed = self.fake.random_int(min=55, max=70)

        travel_hours = route["distance_km"] / speed
        travel_duration = timedelta(hours=travel_hours)
        arrival = departure + travel_duration

        schedule_id = self.generate_schedule_id()

        # Add realistic additional fields
        # Indian bus number format: State code + district number + letters + numbers
        state_codes = ["MH", "DL", "KA", "TN",
                       "WB", "RJ", "GJ", "KL", "AP", "TS"]
        state_code = self.fake.random_element(state_codes)
        bus_number = f"{state_code}-{self.fake.random_int(min=10, max=99)}-{self.fake.bothify(text='??-####')}"
        conductor_name = self.fake.random_element(self.booking_agents)

        return {
            "schedule_id": schedule_id,
            "route_id": route["route_id"],
            "operator_id": operator["operator_id"],
            "departure_time": departure.isoformat(),
            "arrival_time": arrival.isoformat(),
            "date": record_date.date().isoformat(),
            "bus_number": bus_number,
            "conductor_name": conductor_name,
            "route_info": {
                "origin": route["origin"],
                "destination": route["destination"],
                "distance_km": route["distance_km"],
                "popularity": route["popularity"]
            }
        }

    def calculate_base_fare(self, distance_km: float, seat_type: str) -> float:
        """
        Calculate realistic base fare based on distance and seat type using Faker

        Args:
            distance_km: Route distance in kilometers
            seat_type: Type of seat (regular, premium, sleeper)

        Returns:
            Base fare amount
        """
        # Realistic Indian bus fare structure with Faker
        if distance_km < 200:  # Short routes
            rate_per_km = self.fake.random_int(
                min=25, max=35) / 10  # ₹2.5-3.5 per km
        elif distance_km < 400:  # Medium routes
            rate_per_km = self.fake.random_int(
                min=20, max=30) / 10  # ₹2.0-3.0 per km
        else:  # Long routes
            rate_per_km = self.fake.random_int(
                min=15, max=25) / 10  # ₹1.5-2.5 per km

        # Add realistic base fare with minimum fare logic
        base_fare = max(50, distance_km * rate_per_km)  # Minimum ₹50 fare

        # Apply seat type multiplier
        seat_multiplier = SEAT_TYPES[seat_type]["base_fare_multiplier"]

        # Add realistic variance (±10%)
        variance = self.fake.random_int(min=90, max=110) / 100

        final_fare = base_fare * seat_multiplier * variance

        return round(final_fare, 2)

    def simulate_seat_occupancy(self, schedule: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Simulate seat occupancy data for a schedule with enhanced realism

        Args:
            schedule: Schedule information

        Returns:
            List of seat occupancy records with passenger details
        """
        occupancy_records = []
        schedule_id = schedule["schedule_id"]
        distance_km = schedule["route_info"]["distance_km"]
        route_popularity = schedule["route_info"]["popularity"]

        # Simulate for 2-3 seat types per bus (more realistic)
        num_seat_types = self.fake.random_int(min=2, max=3)
        selected_seat_types = self.fake.random_elements(
            elements=list(SEAT_TYPES.keys()),
            length=num_seat_types,
            unique=True
        )

        for seat_type in selected_seat_types:
            # Get typical seat count with some variation
            typical_count = SEAT_TYPES[seat_type]["typical_count"]
            total_seats = self.fake.random_int(
                min=max(10, typical_count - 10),
                max=typical_count + 10
            )

            # Simulate occupancy based on multiple realistic factors
            departure_hour = datetime.fromisoformat(
                schedule["departure_time"]).hour

            # Base occupancy by time of day
            if departure_hour in [7, 8, 9, 17, 18, 19]:  # Peak hours
                base_occupancy = self.fake.random_int(min=60, max=95) / 100
            elif departure_hour in [10, 11, 12, 13, 14, 15, 16]:  # Afternoon
                base_occupancy = self.fake.random_int(min=30, max=70) / 100
            else:  # Early morning/late night
                base_occupancy = self.fake.random_int(min=10, max=50) / 100

            # Adjust for route popularity
            popularity_multiplier = {
                "high": self.fake.random_int(min=110, max=130) / 100,
                "medium": self.fake.random_int(min=90, max=110) / 100,
                "low": self.fake.random_int(min=70, max=90) / 100
            }

            # Apply day-of-week effect (weekends might be different)
            day_of_week = datetime.fromisoformat(
                schedule["departure_time"]).weekday()
            if day_of_week >= 5:  # Weekend
                weekend_factor = self.fake.random_int(min=85, max=115) / 100
            else:
                weekend_factor = 1.0

            occupancy_rate = min(
                0.98, base_occupancy * popularity_multiplier[route_popularity] * weekend_factor)
            occupied_seats = int(total_seats * occupancy_rate)

            # Introduce realistic data errors (2% chance)
            if self.fake.boolean(chance_of_getting_true=2):
                occupied_seats = total_seats + \
                    self.fake.random_int(min=1, max=5)

            # Calculate fare with enhanced realism
            base_fare = self.calculate_base_fare(distance_km, seat_type)

            # Apply realistic demand-based pricing
            if occupancy_rate > 0.8:
                demand_multiplier = self.fake.random_int(
                    min=120, max=150) / 100
            elif occupancy_rate < 0.3:
                demand_multiplier = self.fake.random_int(min=80, max=95) / 100
            else:
                demand_multiplier = self.fake.random_int(min=95, max=120) / 100

            fare = base_fare * demand_multiplier

            # Introduce realistic anomalies for data quality testing (3% chance)
            if self.fake.boolean(chance_of_getting_true=3):
                anomaly_type = self.fake.random_element([
                    "negative_fare", "extreme_high_fare", "zero_fare", "duplicate_booking"
                ])
                if anomaly_type == "negative_fare":
                    fare = -self.fake.random_int(min=100, max=500)
                elif anomaly_type == "extreme_high_fare":
                    fare = self.fake.random_int(min=50000, max=200000)
                elif anomaly_type == "zero_fare":
                    fare = 0

            fare = round(fare, 2)

            # Create realistic timestamp with Faker
            base_timestamp = datetime.fromisoformat(schedule["departure_time"])
            timestamp_offset = self.fake.random_int(
                min=-180, max=60)  # 3 hours before to 1 hour after
            timestamp = base_timestamp + timedelta(minutes=timestamp_offset)

            # Add realistic booking and passenger details
            booking_agent = self.fake.random_element(self.booking_agents)

            # Generate realistic passenger demographics for occupied seats
            passengers = []
            # Sample of passengers (max 5 for demo)
            for _ in range(min(occupied_seats, 5)):
                passenger = {
                    "name": self.fake.name(),
                    "age": self.fake.random_int(min=18, max=75),
                    "gender": self.fake.random_element(["Male", "Female"]),
                    "phone": self.fake.phone_number(),
                    "booking_id": self.fake.bothify(text="BK###??###")
                }
                passengers.append(passenger)

            occupancy_record = {
                "schedule_id": schedule_id,
                "seat_type": seat_type,
                "total_seats": total_seats,
                "occupied_seats": occupied_seats,
                "fare": fare,
                "timestamp": timestamp.isoformat(),
                "occupancy_rate": round(occupied_seats / total_seats, 3) if total_seats > 0 else 0,
                "booking_agent": booking_agent,
                "payment_method": self.fake.random_element(["cash", "card", "upi", "wallet"]),
                "booking_source": self.fake.random_element(["online", "counter", "mobile_app", "agent"]),
                "passenger_sample": passengers,  # Sample passenger data for realism
                "revenue": round(fare * occupied_seats, 2),
                "last_updated": datetime.utcnow().isoformat()
            }

            occupancy_records.append(occupancy_record)

        return occupancy_records

    def generate_data_for_date_range(self, start_date: datetime, num_days: int = 7, schedules_per_day: int = 15):
        """
        Generate simulation data for a range of dates

        Args:
            start_date: Starting date for simulation
            num_days: Number of days to simulate
            schedules_per_day: Number of schedules to generate per day
        """
        logger.info(
            f"Starting data simulation for {num_days} days, {schedules_per_day} schedules per day")

        total_schedules = 0
        total_occupancy_records = 0

        for day_offset in range(num_days):
            current_date = start_date + timedelta(days=day_offset)
            logger.info(f"Generating data for {current_date.date()}")

            day_schedules = []
            day_occupancy = []

            for _ in range(schedules_per_day):
                # Generate schedule
                schedule = self.simulate_schedule(current_date)
                day_schedules.append(schedule)

                # Generate seat occupancy for this schedule
                occupancy_records = self.simulate_seat_occupancy(schedule)
                day_occupancy.extend(occupancy_records)

                total_schedules += 1
                total_occupancy_records += len(occupancy_records)

            # Save daily data to files
            date_str = current_date.strftime("%Y%m%d")

            # Save schedules
            schedules_file = self.output_dir / f"schedules_{date_str}.json"
            with open(schedules_file, 'w') as f:
                json.dump({"schedules": day_schedules}, f, indent=2)

            # Save occupancy data
            occupancy_file = self.output_dir / f"occupancy_{date_str}.json"
            with open(occupancy_file, 'w') as f:
                json.dump({"occupancy_records": day_occupancy}, f, indent=2)

            logger.info(
                f"Saved {len(day_schedules)} schedules and {len(day_occupancy)} occupancy records for {current_date.date()}")

        logger.info(f"Data simulation complete!")
        logger.info(f"Total schedules generated: {total_schedules}")
        logger.info(
            f"Total occupancy records generated: {total_occupancy_records}")
        logger.info(f"Files saved to: {self.output_dir}")

    def generate_sample_metadata(self):
        """Generate static metadata files for routes and operators"""
        # Save routes metadata
        routes_file = self.output_dir / "routes_metadata.json"
        with open(routes_file, 'w') as f:
            json.dump({"routes": ROUTES}, f, indent=2)

        # Save operators metadata
        operators_file = self.output_dir / "operators_metadata.json"
        with open(operators_file, 'w') as f:
            json.dump({"operators": OPERATORS}, f, indent=2)

        logger.info(
            "Metadata files generated: routes_metadata.json, operators_metadata.json")


def main():
    """Main function to run the enhanced data simulation with Faker"""
    # Configuration
    output_directory = os.getenv("RAW_DATA_PATH", "./data/raw")
    # Consistent seed for reproducible data
    seed = int(os.getenv("FAKER_SEED", "12345"))

    logger.info("🎲 Starting enhanced bus data simulation with Faker")
    logger.info(f"📁 Output directory: {output_directory}")
    logger.info(f"🎯 Using seed: {seed} for consistent fake data")

    # Initialize enhanced simulator with Faker
    simulator = BusDataSimulator(output_directory, seed=seed)

    # Generate enhanced metadata
    simulator.generate_sample_metadata()

    # Generate realistic data for the past 3 days and next 4 days (total 7 days)
    start_date = datetime.now() - timedelta(days=3)
    simulator.generate_data_for_date_range(
        start_date=start_date,
        num_days=7,
        schedules_per_day=25  # Generate more realistic 25 schedules per day
    )

    logger.info("✅ Enhanced data simulation complete with realistic fake data!")
    logger.info("📊 Generated data includes:")
    logger.info("   - Realistic Indian operator names and contact details")
    logger.info("   - Enhanced route popularity factors")
    logger.info("   - Realistic passenger demographics and booking details")
    logger.info("   - Authentic Indian phone numbers and addresses")
    logger.info("   - Professional booking IDs and payment methods")
    logger.info("   - Time-based and route-based occupancy patterns")


if __name__ == "__main__":
    main()
