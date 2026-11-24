
import pandas as pd
import random
import json
import os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

os.makedirs("data/raw", exist_ok=True)

# 1. Generate customers
customers = []

for i in range(1, 1001):
    customers.append({
        "CustomerID": f"C{i:04d}",
        "CustomerName": fake.company(),
        "Industry": random.choice([
            "IT", "Healthcare", "Finance",
            "Retail", "Manufacturing"
        ]),
        "City": fake.city(),
        "RegistrationDate": fake.date_between(
            start_date="-3y",
            end_date="today"
        )
    })

customers_df = pd.DataFrame(customers)
customers_df.to_csv(
    "data/raw/customers.csv",
    index=False
)

# 2. Generate agents
agents = []

for i in range(1, 51):
    agents.append({
        "AgentID": f"A{i:03d}",
        "AgentName": fake.name(),
        "Team": random.choice([
            "Infrastructure",
            "Application Support",
            "Network",
            "Database"
        ]),
        "ExperienceLevel": random.choice([
            "Junior", "Mid", "Senior"
        ])
    })

agents_df = pd.DataFrame(agents)
agents_df.to_csv(
    "data/raw/agents.csv",
    index=False
)

# 3. Generate tickets
tickets = []
start_date = datetime.now() - timedelta(days=180)

for i in range(1, 10001):
    created = start_date + timedelta(
        days=random.randint(0, 180),
        hours=random.randint(0, 23)
    )

    priority = random.choice([
        "Critical", "High", "Medium", "Low"
    ])

    status = random.choice([
        "Resolved", "Resolved", "Resolved", "Open"
    ])

    resolved = None

    if status == "Resolved":
        resolved = created + timedelta(
            hours=random.randint(1, 60)
        )

    tickets.append({
        "TicketID": f"T{i:05d}",
        "CustomerID": f"C{random.randint(1, 1000):04d}",
        "AgentID": f"A{random.randint(1, 50):03d}",
        "Category": random.choice([
            "Network", "Software", "Hardware",
            "Database", "Security"
        ]),
        "Priority": priority,
        "Status": status,
        "CreatedDate": created,
        "ResolvedDate": resolved
    })

tickets_df = pd.DataFrame(tickets)

# Add a few intentional data quality issues
tickets_df.loc[10, "Priority"] = None
tickets_df.loc[20, "CustomerID"] = None

tickets_df.to_csv(
    "data/raw/tickets.csv",
    index=False
)

# 4. Generate feedback
feedback = []

for i in range(1, 5001):
    feedback.append({
        "FeedbackID": f"F{i:05d}",
        "TicketID": f"T{random.randint(1, 10000):05d}",
        "Rating": random.randint(1, 5),
        "Comment": random.choice([
            "Issue resolved quickly",
            "Good support experience",
            "The issue took too long",
            "Very helpful agent",
            "Problem not fully resolved"
        ])
    })

with open(
    "data/raw/feedback.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(feedback, f, indent=2)

# 5. Generate application logs
logs = []

for i in range(1, 10001):
    logs.append({
        "LogID": f"L{i:05d}",
        "TicketID": f"T{random.randint(1, 10000):05d}",
        "EventType": random.choice([
            "INFO", "WARNING", "ERROR"
        ]),
        "Timestamp": fake.date_time_between(
            start_date="-180d",
            end_date="now"
        ).isoformat(),
        "Description": random.choice([
            "Connection timeout",
            "Application error",
            "Login failure",
            "Database unavailable",
            "Service restarted"
        ])
    })

with open(
    "data/raw/application_logs.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(logs, f, indent=2)

print("All datasets generated successfully!")
