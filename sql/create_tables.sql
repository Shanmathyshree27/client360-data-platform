
CREATE TABLE IF NOT EXISTS dim_customers (
    CustomerKey SERIAL PRIMARY KEY,
    CustomerID VARCHAR(20) UNIQUE NOT NULL,
    CustomerName VARCHAR(150),
    Industry VARCHAR(100),
    City VARCHAR(100),
    RegistrationDate DATE
);

CREATE TABLE IF NOT EXISTS dim_agents (
    AgentKey SERIAL PRIMARY KEY,
    AgentID VARCHAR(20) UNIQUE NOT NULL,
    AgentName VARCHAR(150),
    Team VARCHAR(100),
    ExperienceLevel VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS dim_date (
    DateKey INTEGER PRIMARY KEY,
    FullDate DATE UNIQUE,
    Year INTEGER,
    Month INTEGER,
    MonthName VARCHAR(20),
    Day INTEGER
);

CREATE TABLE IF NOT EXISTS fact_support_tickets (
    TicketID VARCHAR(20) PRIMARY KEY,
    CustomerKey INTEGER REFERENCES dim_customers(CustomerKey),
    AgentKey INTEGER REFERENCES dim_agents(AgentKey),
    DateKey INTEGER REFERENCES dim_date(DateKey),
    Category VARCHAR(100),
    Priority VARCHAR(50),
    Status VARCHAR(50),
    CreatedDate TIMESTAMP,
    ResolvedDate TIMESTAMP,
    ResolutionHours NUMERIC(10,2),
    SLAStatus VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS fact_customer_feedback (
    FeedbackID VARCHAR(20) PRIMARY KEY,
    TicketID VARCHAR(20),
    Rating INTEGER,
    Comment TEXT
);

CREATE TABLE IF NOT EXISTS application_logs (
    LogID VARCHAR(20) PRIMARY KEY,
    TicketID VARCHAR(20),
    EventType VARCHAR(30),
    LogTimestamp TIMESTAMP,
    Description TEXT
);

