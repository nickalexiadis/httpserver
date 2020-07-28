import psycopg2
from server1 import connect_to_db

# Connects to database. Before connection, the database must be created and appropriate values entered
# on lines 273-277 of server1.py
try:
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("SELECT version();")
    record = cursor.fetchone()
    print("You are connected to - ", record, "\n")

    # Table queries
    create_customer = '''CREATE TABLE customer (
        id serial NOT NULL  check (id > 0),
        name varchar(255) NOT NULL,
        active smallint DEFAULT '1',
        PRIMARY KEY (id)
        );'''

    create_ip_blacklist = '''CREATE TABLE ip_blacklist (
        ip numeric NOT NULL,
        PRIMARY KEY (ip)
        );'''

    create_ua_blacklist = '''CREATE TABLE ua_blacklist (
        ua varchar(255) NOT NULL,
        PRIMARY KEY (ua)
        );'''

    create_hourly_stats = '''CREATE TABLE hourly_stats (
        id Serial NOT NULL,
        customer_id int NOT NULL,
        time timestamp NOT NULL,
        request_count int NOT NULL DEFAULT 0,
        invalid_count int NOT NULL DEFAULT 0,
        PRIMARY KEY (id),
        CONSTRAINT unique_customer_time UNIQUE(customer_id,time),
        CONSTRAINT hourly_stats_customer_id FOREIGN KEY (customer_id) REFERENCES customer (id) ON DELETE CASCADE ON UPDATE NO ACTION
        );'''

    # Creates db tables
    cursor.execute(create_customer)
    cursor.execute(create_ip_blacklist)
    cursor.execute(create_ua_blacklist)
    cursor.execute(create_hourly_stats)
    connection.commit()
    print("Tables created successfully in PostgreSQL ")

    # Insertion queries
    insert_customer = """ INSERT INTO customer (ID, NAME, ACTIVE) VALUES (1,'Big News Media Corp',1),(2,'Online Mega Store',1),(3,'Nachoroo Delivery',0),(4,'Euro Telecom Group',1);"""
    insert_ip_blacklist = """ INSERT INTO ip_blacklist (IP) VALUES (0),(2130706433),(4294967295);"""
    insert_ua_blacklist = """ INSERT INTO ua_blacklist (UA) VALUES ('A6-Indexer'),('Googlebot-News'),('Googlebot');"""

    # Insert sample data into tables
    cursor.execute(insert_customer)
    cursor.execute(insert_ip_blacklist)
    cursor.execute(insert_ua_blacklist)
    connection.commit()
    print("Records inserted successfully into tables")

except (Exception, psycopg2.DatabaseError) as error:
    print("Error while creating PostgreSQL table or inserting data", error)

finally:
    # Closes database connection
    if (connection):
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")