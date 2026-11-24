# Client 360° Customer Support Data Platform

## Project Overview
This project builds a customer support data platform that consolidates customer, agent, support ticket, feedback, and application log data into PostgreSQL for analytics and reporting.

The dataset is synthetic and was generated for learning and portfolio purposes.

## Architecture
Synthetic CSV/JSON Data → Python ETL → PostgreSQL → SQL Analytics → Power BI Dashboard

## Technologies Used
- Python
- Pandas
- PostgreSQL
- SQL
- Power BI
- Git and GitHub

## Data Sources
- 1,000 customers
- 50 support agents
- 10,000 support tickets
- 5,000 customer feedback records
- 10,000 application log records

## ETL Process
1. Generate synthetic source data.
2. Read CSV and JSON files.
3. Clean and validate records.
4. Handle missing values.
5. Transform ticket and customer data.
6. Load dimension and fact tables into PostgreSQL.

## Database Design
- dim_customers
- dim_agents
- dim_date
- fact_support_tickets
- fact_customer_feedback
- application_logs

## Analytics
- Ticket volume by priority
- Ticket volume by category
- SLA compliance
- Average resolution time
- Agent performance
- Customer satisfaction by industry

## Dashboard
The Power BI dashboard provides ticket KPIs, priority and category analysis, agent performance, customer satisfaction, and interactive filters.
<img width="887" height="525" alt="image" src="https://github.com/user-attachments/assets/024edd49-6d8b-44d0-aaf3-5c98ba040e3e" />

## Data Quality
The pipeline includes checks for duplicate ticket IDs, missing keys, invalid resolution times, and source-to-target row counts.

## How to Run
1. Install Python and PostgreSQL.
2. Create the `client360_db` database.
3. Install dependencies using `pip install -r requirements.txt`.
4. Configure database credentials in a local `.env` file.
5. Generate the synthetic data.
6. Create the database tables.
7. Run `python src/etl_pipeline.py`.
8. Connect Power BI to PostgreSQL and open the dashboard.

## Disclaimer
All data is synthetic and does not represent real customers or support records.
