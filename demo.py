#!/usr/bin/env python3
"""
Bus Pricing Pipeline Demo Script

Demonstrates the complete functionality of the bus pricing pipeline including:
- Data simulation and generation
- ETL processing and data quality
- API endpoints and analytics
- Dynamic pricing suggestions
- System monitoring and health checks

This script can be run to showcase the project capabilities during the viva voce.
"""

import requests
import json
import time
import os
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BusPipelineDemo:
    """Demo orchestrator for the bus pricing pipeline"""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.demo_results = {}

    def print_section(self, title: str):
        """Print a formatted section header"""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60)

    def print_subsection(self, title: str):
        """Print a formatted subsection header"""
        print(f"\n--- {title} ---")

    def wait_for_api(self, timeout: int = 60) -> bool:
        """Wait for API to become available"""
        self.print_subsection("Waiting for API to be ready")

        for i in range(timeout):
            try:
                response = self.session.get(
                    f"{self.api_base_url}/health", timeout=5)
                if response.status_code == 200:
                    print(f"✅ API is ready! (took {i+1} seconds)")
                    return True
            except requests.exceptions.RequestException:
                pass

            if i < timeout - 1:
                print(f"⏳ Waiting... ({i+1}/{timeout})")
                time.sleep(1)

        print(f"❌ API failed to start within {timeout} seconds")
        return False

    def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        self.print_subsection("System Health Check")

        health_data = {}

        try:
            # Check API health
            response = self.session.get(f"{self.api_base_url}/health")
            if response.status_code == 200:
                health_data["api"] = response.json()
                print("✅ API Service: Healthy")
            else:
                print(
                    f"❌ API Service: Unhealthy (Status: {response.status_code})")

        except requests.exceptions.RequestException as e:
            print(f"❌ API Service: Connection failed - {e}")
            return health_data

        try:
            # Check system statistics
            response = self.session.get(f"{self.api_base_url}/stats/summary")
            if response.status_code == 200:
                stats = response.json()
                health_data["stats"] = stats
                print("✅ Database: Connected")
                print(f"   📊 Total Routes: {stats.get('total_routes', 0)}")
                print(
                    f"   🚌 Total Operators: {stats.get('total_operators', 0)}")
                print(
                    f"   📅 Total Schedules: {stats.get('total_schedules', 0)}")
                print(
                    f"   💺 Total Occupancy Records: {stats.get('total_occupancy_records', 0)}")
            else:
                print("❌ Database: Connection issues")

        except requests.exceptions.RequestException as e:
            print(f"❌ Database: Failed to get stats - {e}")

        self.demo_results["health_check"] = health_data
        return health_data

    def demonstrate_api_endpoints(self):
        """Demonstrate key API endpoints"""
        self.print_section("API ENDPOINTS DEMONSTRATION")

        endpoints_demo = {}

        # 1. Routes endpoint
        self.print_subsection("1. Routes API")
        try:
            response = self.session.get(f"{self.api_base_url}/routes")
            if response.status_code == 200:
                routes = response.json()
                endpoints_demo["routes"] = routes
                print(f"✅ Found {len(routes)} routes:")
                for route in routes[:3]:  # Show first 3
                    print(
                        f"   🛣️  Route {route['route_id']}: {route['origin']} → {route['destination']} ({route['distance_km']} km)")
            else:
                print(f"❌ Routes API failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Routes API error: {e}")

        # 2. Operators endpoint
        self.print_subsection("2. Operators API")
        try:
            response = self.session.get(f"{self.api_base_url}/operators")
            if response.status_code == 200:
                operators = response.json()
                endpoints_demo["operators"] = operators
                print(f"✅ Found {len(operators)} operators:")
                for operator in operators[:3]:  # Show first 3
                    print(
                        f"   🚌 {operator['name']} (ID: {operator['operator_id']})")
            else:
                print(f"❌ Operators API failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Operators API error: {e}")

        # 3. Analytics endpoint
        self.print_subsection("3. Occupancy Analytics API")
        try:
            response = self.session.get(
                f"{self.api_base_url}/analytics/occupancy")
            if response.status_code == 200:
                analytics = response.json()
                endpoints_demo["analytics"] = analytics
                print("✅ Analytics data retrieved:")
                print(
                    f"   📊 Total Schedules: {analytics.get('total_schedules', 0)}")
                print(
                    f"   💺 Average Occupancy: {analytics.get('average_occupancy_rate', 0):.1%}")
                print(
                    f"   💰 Average Fare: ₹{analytics.get('average_fare', 0):.2f}")
                print(
                    f"   🎫 Total Seats Available: {analytics.get('total_seats_available', 0)}")
                print(
                    f"   👥 Total Seats Occupied: {analytics.get('total_seats_occupied', 0)}")
            else:
                print(f"❌ Analytics API failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Analytics API error: {e}")

        self.demo_results["api_endpoints"] = endpoints_demo

    def demonstrate_pricing_engine(self):
        """Demonstrate the dynamic pricing engine"""
        self.print_section("DYNAMIC PRICING ENGINE DEMONSTRATION")

        pricing_demos = []

        # Test scenarios with different occupancy rates and conditions
        test_scenarios = [
            {
                "name": "High Occupancy - Peak Hour",
                "route_id": 1,
                "seat_type": "regular",
                "current_occupancy_rate": 0.85,
                "departure_time": (datetime.now() + timedelta(hours=2)).replace(hour=8).isoformat(),
                "current_fare": 350.0
            },
            {
                "name": "Low Occupancy - Off Peak",
                "route_id": 2,
                "seat_type": "premium",
                "current_occupancy_rate": 0.25,
                "departure_time": (datetime.now() + timedelta(hours=20)).replace(hour=2).isoformat(),
                "current_fare": 500.0
            },
            {
                "name": "Last Minute Booking",
                "route_id": 3,
                "seat_type": "sleeper",
                "current_occupancy_rate": 0.60,
                "departure_time": (datetime.now() + timedelta(minutes=90)).isoformat(),
                "current_fare": 800.0
            },
            {
                "name": "Early Booking - Long Distance",
                "route_id": 4,
                "seat_type": "sleeper",
                "current_occupancy_rate": 0.40,
                "departure_time": (datetime.now() + timedelta(days=10)).isoformat(),
                "current_fare": 1200.0
            }
        ]

        for i, scenario in enumerate(test_scenarios, 1):
            self.print_subsection(f"{i}. {scenario['name']}")

            try:
                response = self.session.post(
                    f"{self.api_base_url}/pricing/suggest",
                    json=scenario,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    pricing = response.json()
                    pricing_demos.append({
                        "scenario": scenario["name"],
                        "input": scenario,
                        "result": pricing
                    })

                    print("✅ Pricing suggestion generated:")
                    print(
                        f"   📍 Route: {scenario['route_id']} | Seat: {scenario['seat_type']} | Occupancy: {scenario['current_occupancy_rate']:.1%}")
                    print(
                        f"   💰 Current Fare: ₹{scenario['current_fare']:.2f}")
                    print(
                        f"   💎 Suggested Fare: ₹{pricing['suggested_fare']:.2f}")

                    change_pct = pricing['fare_adjustment_percentage']
                    change_symbol = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
                    print(f"   {change_symbol} Adjustment: {change_pct:+.1f}%")
                    print(
                        f"   🎯 Confidence: {pricing['confidence_score']:.0%}")
                    print(f"   💭 Reasoning: {pricing['reasoning']}")

                elif response.status_code == 400:
                    error_detail = response.json()
                    print(
                        f"❌ Invalid request: {error_detail.get('detail', 'Unknown error')}")
                else:
                    print(f"❌ Pricing API failed: {response.status_code}")

            except Exception as e:
                print(f"❌ Pricing API error: {e}")

        self.demo_results["pricing_demos"] = pricing_demos

    def demonstrate_data_quality(self):
        """Demonstrate data quality monitoring"""
        self.print_section("DATA QUALITY MONITORING")

        self.print_subsection("Data Quality Report")

        try:
            response = self.session.get(
                f"{self.api_base_url}/data-quality/report?days_back=7")
            if response.status_code == 200:
                quality_report = response.json()
                self.demo_results["data_quality"] = quality_report

                print("✅ Data Quality Report (Last 7 days):")
                print(
                    f"   📊 Total Records Processed: {quality_report.get('total_records_processed', 0):,}")
                print(
                    f"   ✅ Valid Records: {quality_report.get('valid_records', 0):,}")
                print(
                    f"   ❌ Invalid Records: {quality_report.get('invalid_records', 0):,}")
                print(
                    f"   🎯 Quality Score: {quality_report.get('quality_score', 0):.1%}")

                issues = quality_report.get('issues', [])
                if issues:
                    print("   🚨 Quality Issues Found:")
                    for issue in issues:
                        severity_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(
                            issue['severity'], "⚪")
                        print(
                            f"      {severity_icon} {issue['issue_type']}: {issue['count']} occurrences ({issue['severity']} severity)")
                else:
                    print("   🎉 No quality issues found!")

            else:
                print(f"❌ Data Quality API failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Data Quality API error: {e}")

    def demonstrate_route_analytics(self):
        """Demonstrate route-specific analytics"""
        self.print_section("ROUTE ANALYTICS DEMONSTRATION")

        # Get routes first
        try:
            response = self.session.get(f"{self.api_base_url}/routes")
            if response.status_code != 200:
                print("❌ Could not fetch routes for analytics demo")
                return

            routes = response.json()
            if not routes:
                print("ℹ️  No routes available for analytics demo")
                return

            route_analytics = []

            # Analyze first few routes
            for route in routes[:3]:
                self.print_subsection(
                    f"Route {route['route_id']}: {route['origin']} → {route['destination']}")

                try:
                    # Get analytics for this specific route
                    response = self.session.get(
                        f"{self.api_base_url}/analytics/occupancy?route_id={route['route_id']}"
                    )

                    if response.status_code == 200:
                        analytics = response.json()
                        route_analytics.append({
                            "route": route,
                            "analytics": analytics
                        })

                        print(f"✅ Analytics for Route {route['route_id']}:")
                        print(f"   📏 Distance: {route['distance_km']} km")
                        print(
                            f"   📅 Schedules: {analytics.get('total_schedules', 0)}")

                        if analytics.get('total_schedules', 0) > 0:
                            print(
                                f"   💺 Avg Occupancy: {analytics.get('average_occupancy_rate', 0):.1%}")
                            print(
                                f"   💰 Avg Fare: ₹{analytics.get('average_fare', 0):.2f}")
                            print(
                                f"   📊 Occupancy Range: {analytics.get('min_occupancy_rate', 0):.1%} - {analytics.get('max_occupancy_rate', 0):.1%}")
                        else:
                            print("   ℹ️  No occupancy data available")
                    else:
                        print(
                            f"❌ Analytics failed for route {route['route_id']}: {response.status_code}")

                except Exception as e:
                    print(f"❌ Route analytics error: {e}")

            self.demo_results["route_analytics"] = route_analytics

        except Exception as e:
            print(f"❌ Route analytics demo error: {e}")

    def demonstrate_api_documentation(self):
        """Show API documentation access"""
        self.print_section("API DOCUMENTATION")

        print("📚 Interactive API Documentation:")
        print(f"   🌐 Swagger UI: {self.api_base_url}/docs")
        print(f"   📖 ReDoc: {self.api_base_url}/redoc")
        print("\n💡 You can test all endpoints interactively through the Swagger UI!")

    def generate_summary_report(self):
        """Generate a summary of the demo"""
        self.print_section("DEMO SUMMARY REPORT")

        print("🎯 Bus Pricing Pipeline Demo Completed Successfully!")
        print(
            f"⏰ Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # System health summary
        if "health_check" in self.demo_results:
            health = self.demo_results["health_check"]
            stats = health.get("stats", {})
            print(f"\n📊 System Statistics:")
            print(f"   • Routes: {stats.get('total_routes', 0)}")
            print(f"   • Operators: {stats.get('total_operators', 0)}")
            print(f"   • Schedules: {stats.get('total_schedules', 0)}")
            print(
                f"   • Occupancy Records: {stats.get('total_occupancy_records', 0)}")

        # Pricing demo summary
        if "pricing_demos" in self.demo_results:
            pricing_demos = self.demo_results["pricing_demos"]
            print(f"\n💰 Pricing Scenarios Tested: {len(pricing_demos)}")

            for demo in pricing_demos:
                result = demo["result"]
                change = result["fare_adjustment_percentage"]
                print(f"   • {demo['scenario']}: {change:+.1f}% adjustment")

        # Data quality summary
        if "data_quality" in self.demo_results:
            quality = self.demo_results["data_quality"]
            quality_score = quality.get("quality_score", 0)
            print(f"\n✅ Data Quality Score: {quality_score:.1%}")

        print("\n🚀 Key Features Demonstrated:")
        print("   ✅ Real-time API endpoints")
        print("   ✅ Dynamic pricing engine")
        print("   ✅ Data quality monitoring")
        print("   ✅ Route analytics")
        print("   ✅ Comprehensive data validation")
        print("   ✅ Professional API documentation")

        print("\n🎓 Technical Skills Showcased:")
        print("   • FastAPI web framework")
        print("   • PostgreSQL database design")
        print("   • Data validation & cleaning")
        print("   • Heuristic pricing algorithms")
        print("   • RESTful API development")
        print("   • Docker containerization")
        print("   • Comprehensive testing")
        print("   • CI/CD with GitHub Actions")

        print("\n💼 Industry Applications:")
        print("   • Transportation & logistics")
        print("   • Dynamic pricing strategies")
        print("   • Real-time analytics")
        print("   • Data quality management")
        print("   • Microservices architecture")

    def run_full_demo(self):
        """Run the complete demonstration"""
        print("🚀 Starting Bus Pricing Pipeline Demo")
        print("=" * 60)

        try:
            # Check if API is ready
            if not self.wait_for_api():
                print("❌ Demo cannot proceed without API access")
                print("💡 Please ensure Docker Compose is running: docker-compose up")
                return False

            # Run demonstration sections
            self.check_system_health()
            self.demonstrate_api_endpoints()
            self.demonstrate_pricing_engine()
            self.demonstrate_data_quality()
            self.demonstrate_route_analytics()
            self.demonstrate_api_documentation()
            self.generate_summary_report()

            print("\n🎉 Demo completed successfully!")
            return True

        except KeyboardInterrupt:
            print("\n⏹️  Demo interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            return False


def main():
    """Main demo execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Bus Pricing Pipeline Demo")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Base URL for the API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run a quick demo with reduced output"
    )

    args = parser.parse_args()

    demo = BusPipelineDemo(api_base_url=args.api_url)

    if args.quick:
        print("🚀 Running Quick Demo...")
        demo.wait_for_api()
        demo.check_system_health()
        demo.demonstrate_pricing_engine()
    else:
        demo.run_full_demo()


if __name__ == "__main__":
    main()
