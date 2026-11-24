
from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# ==================================================
# 1. PROJECT PATHS AND DATABASE CONNECTION
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"

load_dotenv(PROJECT_ROOT / ".env")

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "client360_db"),
)

engine = create_engine(db_url)


# ==================================================
# 2. EXTRACT DATA
# ==================================================

def extract_data():
    print("Starting extraction...")

    customers = pd.read_csv(RAW_DIR / "customers.csv")
    agents = pd.read_csv(RAW_DIR / "agents.csv")
    tickets = pd.read_csv(RAW_DIR / "tickets.csv")

    feedback = pd.read_json(RAW_DIR / "feedback.json")
    logs = pd.read_json(RAW_DIR / "application_logs.json")

    # Standardize every column name to lowercase.
    # Example: CustomerID becomes customerid.
    # This prevents PostgreSQL capitalization problems.
    dataframes = [
        customers,
        agents,
        tickets,
        feedback,
        logs,
    ]

    for df in dataframes:
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
        )

    print("Customers:", len(customers))
    print("Agents:", len(agents))
    print("Tickets:", len(tickets))
    print("Feedback:", len(feedback))
    print("Application logs:", len(logs))

    print("Data extraction completed.")

    return customers, agents, tickets, feedback, logs


# ==================================================
# 3. TRANSFORM DATA
# ==================================================

def transform_data(
    customers,
    agents,
    tickets,
    feedback,
    logs,
):
    print("Starting transformation...")

    # ----------------------------------------------
    # CLEAN CUSTOMERS
    # ----------------------------------------------

    customers = customers.drop_duplicates(
        subset=["customerid"]
    ).copy()

    customers = customers.dropna(
        subset=["customerid"]
    ).copy()

    customers["customerid"] = (
        customers["customerid"]
        .astype(str)
        .str.strip()
    )

    customers["customername"] = (
        customers["customername"]
        .fillna("Unknown")
    )

    customers["industry"] = (
        customers["industry"]
        .fillna("Unknown")
    )

    customers["city"] = (
        customers["city"]
        .fillna("Unknown")
    )

    customers["registrationdate"] = pd.to_datetime(
        customers["registrationdate"],
        errors="coerce",
    ).dt.date


    # ----------------------------------------------
    # CLEAN AGENTS
    # ----------------------------------------------

    agents = agents.drop_duplicates(
        subset=["agentid"]
    ).copy()

    agents = agents.dropna(
        subset=["agentid"]
    ).copy()

    agents["agentid"] = (
        agents["agentid"]
        .astype(str)
        .str.strip()
    )

    agents["agentname"] = (
        agents["agentname"]
        .fillna("Unknown")
    )

    agents["team"] = (
        agents["team"]
        .fillna("Unknown")
    )

    agents["experiencelevel"] = (
        agents["experiencelevel"]
        .fillna("Unknown")
    )


    # ----------------------------------------------
    # CLEAN TICKETS
    # ----------------------------------------------

    tickets = tickets.drop_duplicates(
        subset=["ticketid"]
    ).copy()

    # TicketID, CustomerID and AgentID are required
    tickets = tickets.dropna(
        subset=[
            "ticketid",
            "customerid",
            "agentid",
        ]
    ).copy()

    for column in [
        "ticketid",
        "customerid",
        "agentid",
    ]:
        tickets[column] = (
            tickets[column]
            .astype(str)
            .str.strip()
        )

    tickets["priority"] = (
        tickets["priority"]
        .fillna("Medium")
        .astype(str)
        .str.strip()
        .str.title()
    )

    tickets["status"] = (
        tickets["status"]
        .fillna("Open")
        .astype(str)
        .str.strip()
        .str.title()
    )

    tickets["createddate"] = pd.to_datetime(
        tickets["createddate"],
        errors="coerce",
    )

    tickets["resolveddate"] = pd.to_datetime(
        tickets["resolveddate"],
        errors="coerce",
    )

    # Remove tickets without valid creation dates
    tickets = tickets.dropna(
        subset=["createddate"]
    ).copy()


    # ----------------------------------------------
    # CALCULATE RESOLUTION HOURS
    # ----------------------------------------------

    tickets["resolutionhours"] = (
        tickets["resolveddate"]
        - tickets["createddate"]
    ).dt.total_seconds() / 3600

    # Invalid negative resolution time becomes null
    tickets.loc[
        tickets["resolutionhours"] < 0,
        "resolutionhours",
    ] = None


    # ----------------------------------------------
    # CALCULATE SLA STATUS
    # ----------------------------------------------

    sla_targets = {
        "Critical": 4,
        "High": 8,
        "Medium": 24,
        "Low": 48,
    }

    tickets["slatargethours"] = (
        tickets["priority"].map(sla_targets)
    )

    def calculate_sla(row):
        hours = row["resolutionhours"]
        priority = row["priority"]

        if pd.isna(hours):
            return "Pending"

        target = sla_targets.get(priority)

        if target is None:
            return "Not Applicable"

        if hours <= target:
            return "Met"

        return "Breached"

    tickets["slastatus"] = tickets.apply(
        calculate_sla,
        axis=1,
    )


    # ----------------------------------------------
    # CREATE DATE DIMENSION
    # ----------------------------------------------

    unique_dates = (
        tickets["createddate"]
        .dt.date
        .drop_duplicates()
    )

    date_dim = pd.DataFrame({
        "fulldate": unique_dates
    })

    date_dim["datekey"] = (
        pd.to_datetime(date_dim["fulldate"])
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    date_dim["year"] = (
        pd.to_datetime(date_dim["fulldate"])
        .dt.year
    )

    date_dim["month"] = (
        pd.to_datetime(date_dim["fulldate"])
        .dt.month
    )

    date_dim["monthname"] = (
        pd.to_datetime(date_dim["fulldate"])
        .dt.strftime("%B")
    )

    date_dim["day"] = (
        pd.to_datetime(date_dim["fulldate"])
        .dt.day
    )

    date_dim = date_dim[
        [
            "datekey",
            "fulldate",
            "year",
            "month",
            "monthname",
            "day",
        ]
    ]


    # Add date key to ticket data
    tickets["datekey"] = (
        tickets["createddate"]
        .dt.strftime("%Y%m%d")
        .astype(int)
    )


    # ----------------------------------------------
    # CLEAN FEEDBACK
    # ----------------------------------------------

    feedback = feedback.drop_duplicates(
        subset=["feedbackid"]
    ).copy()

    feedback = feedback.dropna(
        subset=[
            "feedbackid",
            "ticketid",
        ]
    ).copy()

    feedback["rating"] = pd.to_numeric(
        feedback["rating"],
        errors="coerce",
    )

    feedback = feedback[
        feedback["rating"].between(1, 5)
    ].copy()

    feedback["rating"] = (
        feedback["rating"].astype(int)
    )

    feedback["comment"] = (
        feedback["comment"]
        .fillna("")
        .astype(str)
    )

    feedback["feedbackid"] = (
        feedback["feedbackid"].astype(str)
    )

    feedback["ticketid"] = (
        feedback["ticketid"].astype(str)
    )


    # ----------------------------------------------
    # CLEAN APPLICATION LOGS
    # ----------------------------------------------

    logs = logs.drop_duplicates(
        subset=["logid"]
    ).copy()

    logs = logs.dropna(
        subset=["logid"]
    ).copy()

    logs["logid"] = (
        logs["logid"].astype(str)
    )

    logs["ticketid"] = (
        logs["ticketid"].astype(str)
    )

    logs["timestamp"] = pd.to_datetime(
        logs["timestamp"],
        errors="coerce",
    )

    logs = logs.dropna(
        subset=["timestamp"]
    ).copy()

    logs = logs.rename(
        columns={
            "timestamp": "logtimestamp"
        }
    )

    logs["eventtype"] = (
        logs["eventtype"]
        .fillna("INFO")
    )

    logs["description"] = (
        logs["description"]
        .fillna("")
    )


    print("Transformation completed.")

    print("Clean customers:", len(customers))
    print("Clean agents:", len(agents))
    print("Clean tickets:", len(tickets))
    print("Clean feedback:", len(feedback))
    print("Clean logs:", len(logs))

    return (
        customers,
        agents,
        tickets,
        feedback,
        logs,
        date_dim,
    )


# ==================================================
# 4. LOAD DATA INTO POSTGRESQL
# ==================================================

def load_data(
    customers,
    agents,
    tickets,
    feedback,
    logs,
    date_dim,
):
    print("Starting load...")

    # ----------------------------------------------
    # RESET TABLE DATA BEFORE LOADING
    # ----------------------------------------------

    # This makes the demo pipeline rerunnable.
    # It clears the existing project data each run.

    with engine.begin() as connection:
        connection.execute(
            text("""
                TRUNCATE TABLE
                    fact_customer_feedback,
                    application_logs,
                    fact_support_tickets,
                    dim_date,
                    dim_agents,
                    dim_customers
                RESTART IDENTITY CASCADE;
            """)
        )

    print("Existing project data cleared.")


    # ----------------------------------------------
    # LOAD CUSTOMER DIMENSION
    # ----------------------------------------------

    customers_db = customers[
        [
            "customerid",
            "customername",
            "industry",
            "city",
            "registrationdate",
        ]
    ].copy()

    customers_db.to_sql(
        "dim_customers",
        engine,
        if_exists="append",
        index=False,
        chunksize=1000,
    )

    print("Customer dimension loaded.")


    # ----------------------------------------------
    # LOAD AGENT DIMENSION
    # ----------------------------------------------

    agents_db = agents[
        [
            "agentid",
            "agentname",
            "team",
            "experiencelevel",
        ]
    ].copy()

    agents_db.to_sql(
        "dim_agents",
        engine,
        if_exists="append",
        index=False,
        chunksize=1000,
    )

    print("Agent dimension loaded.")


    # ----------------------------------------------
    # LOAD DATE DIMENSION
    # ----------------------------------------------

    date_dim.to_sql(
        "dim_date",
        engine,
        if_exists="append",
        index=False,
        chunksize=1000,
    )

    print("Date dimension loaded.")


    # ----------------------------------------------
    # GET GENERATED DATABASE KEYS
    # ----------------------------------------------

    with engine.connect() as connection:

        customer_keys = pd.read_sql_query(
            text("""
                SELECT customerkey, customerid
                FROM dim_customers
            """),
            connection,
        )

        agent_keys = pd.read_sql_query(
            text("""
                SELECT agentkey, agentid
                FROM dim_agents
            """),
            connection,
        )


    # ----------------------------------------------
    # MAP CUSTOMER AND AGENT KEYS
    # ----------------------------------------------

    tickets = tickets.merge(
        customer_keys,
        on="customerid",
        how="inner",
    )

    tickets = tickets.merge(
        agent_keys,
        on="agentid",
        how="inner",
    )

    print("Ticket dimension keys mapped.")


    # ----------------------------------------------
    # PREPARE TICKET FACT TABLE
    # ----------------------------------------------

    fact_tickets = tickets[
        [
            "ticketid",
            "customerkey",
            "agentkey",
            "datekey",
            "category",
            "priority",
            "status",
            "createddate",
            "resolveddate",
            "resolutionhours",
            "slastatus",
        ]
    ].copy()

    fact_tickets.to_sql(
        "fact_support_tickets",
        engine,
        if_exists="append",
        index=False,
        chunksize=1000,
    )

    print("Support ticket fact table loaded.")


    # ----------------------------------------------
    # LOAD CUSTOMER FEEDBACK
    # ----------------------------------------------

    feedback_db = feedback[
        [
            "feedbackid",
            "ticketid",
            "rating",
            "comment",
        ]
    ].copy()

    feedback_db.to_sql(
        "fact_customer_feedback",
        engine,
        if_exists="append",
        index=False,
        chunksize=1000,
    )

    print("Customer feedback loaded.")


    # ----------------------------------------------
    # LOAD APPLICATION LOGS
    # ----------------------------------------------

    logs_db = logs[
        [
            "logid",
            "ticketid",
            "eventtype",
            "logtimestamp",
            "description",
        ]
    ].copy()

    logs_db.to_sql(
        "application_logs",
        engine,
        if_exists="append",
        index=False,
        chunksize=1000,
    )

    print("Application logs loaded.")


    # ----------------------------------------------
    # PRINT LOAD SUMMARY
    # ----------------------------------------------

    with engine.connect() as connection:

        customers_count = connection.execute(
            text("SELECT COUNT(*) FROM dim_customers")
        ).scalar()

        agents_count = connection.execute(
            text("SELECT COUNT(*) FROM dim_agents")
        ).scalar()

        tickets_count = connection.execute(
            text("SELECT COUNT(*) FROM fact_support_tickets")
        ).scalar()

        feedback_count = connection.execute(
            text("SELECT COUNT(*) FROM fact_customer_feedback")
        ).scalar()

        logs_count = connection.execute(
            text("SELECT COUNT(*) FROM application_logs")
        ).scalar()

    print()
    print("========== LOAD SUMMARY ==========")
    print("Customers loaded:", customers_count)
    print("Agents loaded:", agents_count)
    print("Tickets loaded:", tickets_count)
    print("Feedback loaded:", feedback_count)
    print("Application logs loaded:", logs_count)


# ==================================================
# 5. MAIN ETL PIPELINE
# ==================================================

def main():
    print("====================================")
    print("CLIENT 360 DATA ENGINEERING ETL")
    print("====================================")

    # Test PostgreSQL connection
    with engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT current_database()")
        ).scalar()

    print("Connected to database:", database_name)

    # Extract
    raw_data = extract_data()

    # Transform
    transformed_data = transform_data(*raw_data)

    # Load
    load_data(*transformed_data)

    print()
    print("====================================")
    print("ETL PIPELINE COMPLETED SUCCESSFULLY")
    print("====================================")


if __name__ == "__main__":
    main()
