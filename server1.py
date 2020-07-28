import http.server
import psycopg2
import datetime
import json


class MyHandler(http.server.BaseHTTPRequestHandler):
    # Handles POST requests
    def do_POST(self):
        # Connects to database
        connection = connect_to_db()
        cursor = connection.cursor()

        # Selects the body of the request
        content_len = int(self.headers.get('content-length', 0))
        post_body = self.rfile.read(content_len)

        # Initialization, Boolean to be used for processing valid requests
        valid = True
        bad_json = False
        try:
            j = json.loads(post_body)
        # If JSON is malformed or values or missing. To be handled separately
        except json.decoder.JSONDecodeError:
            bad_json = True

        while not bad_json:
            # Retrieves request values. If keys are misspelled, treats as malformed json
            try:
                cust_ID = j['customerID']
                remote_IP = j['remoteIP'].replace('.', '')
            except KeyError:
                bad_json = True
                break
            user_agent = self.headers.get('User-Agent')
            # Database queries
            q1 = "select id from customer"
            q2 = "select active from customer where id = " + str(cust_ID)
            q3 = "select ip from ip_blacklist"
            q4 = "select ua from ua_blacklist"

            # Retrieves ids from db
            cursor.execute(q1)
            id_col = cursor.fetchall()
            ids = []
            for id in id_col:
                ids.append(id[0])

            # Retrieves active property
            cursor.execute(q2)
            active_col = cursor.fetchall()

            # Retrieves IP Blacklist
            cursor.execute(q3)
            remote_IPCol = cursor.fetchall()
            IP_blacklist = []
            for id in remote_IPCol:
                IP_blacklist.append((str(id[0])))

            # Retrieves user-agent Blacklist
            cursor.execute(q4)
            ua_col = cursor.fetchall()
            ua_blacklist = []
            for ua in ua_col:
                ua_blacklist.append(ua[0])

            # If the customer's ID isn't in the db, the account isn;t active, or the IP and User-Agent are in the
            # blacklist, the request is invalid
            if cust_ID not in ids or active_col[0][0] == 0 or remote_IP in IP_blacklist or user_agent in ua_blacklist:
                valid = False

            # Tries to retrieve the timestamp, if possible
            try:
                timestamp = j['timestamp']
            except KeyError:
                bad_json = True
                break

            # Transforms the timestamp to a string
            unix_to_time = datetime.datetime.fromtimestamp(int(timestamp))
            time_string = unix_to_time.strftime('%Y-%m-%d %H:%M:%S')

            # Retrieves the date and hour of the request
            date = time_string[0:10]
            hour = time_string[11] + time_string[12]

            # Retrieves the number of requests by this customer on this date and hour
            q5 = "select count(*) from hourly_stats where customer_id = (%s) and extract(hour from time) = (%s) " \
                 "and date(time) = (%s)"
            cursor.execute(q5, (cust_ID, hour, date))
            count = cursor.fetchall()[0][0]

            # If no requests at this time frame
            if count == 0:
                # If the customer's ID is in the db, inserts data to db accounting for whether the request
                # is valid or not
                if cust_ID in ids:
                    q6 = "insert into hourly_stats (customer_id, time, request_count, invalid_count)" \
                         " values (%s, %s, %s, %s)"
                    if valid:
                        cursor.execute(q6, (cust_ID, unix_to_time, 1, 0))
                        print("Created row - valid")
                    else:
                        cursor.execute(q6, (cust_ID, unix_to_time, 1, 1))
                        print("Created row - invalid")
                # If the Id is not in the db, the request cannot be processed or information stored
                else:
                    print("Cannot save invalid request as customerID does not exist in database")
            # If there is an entry in the db for this time frame, updates the data
            else:
                q7 = "select request_count,invalid_count from hourly_stats where customer_id = (%s) and " \
                     "extract(hour from time) = (%s) and date(time) = (%s)"
                cursor.execute(q7, (cust_ID, hour, date))
                all = cursor.fetchall()
                req_count = all[0][0]
                invalid_count = all[0][1]
                q8 = "update hourly_stats set request_count = (%s), invalid_count = (%s) where customer_id = (%s)" \
                     "and extract(hour from time) = (%s) and date(time) = (%s)"
                if valid:
                    cursor.execute(q8, (req_count + 1, invalid_count, cust_ID, hour, date))
                    print("Updated row - valid")
                else:
                    cursor.execute(q8, (req_count + 1, invalid_count + 1, cust_ID, hour, date))
                    print("Updated row - invalid")

            # Stores changes to database
            connection.commit()

            # If valid request, calls appropriate function
            if valid:
                process()
            break

        # If malformed JSON/missing values
        if bad_json:

            # Stores the request's body as a string and removes all punctuation
            my_str = post_body.decode('utf-8')
            punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
            no_punc = ""
            for char in my_str:
                if char in punctuations:
                    no_punc += " "
                else:
                    no_punc += char

            # Turns the altered string to list without spaces
            list = no_punc.split(" ")
            final_list = [i for i in list if i != ""]

            # If customer Id exists in the malformed JSON and the next value can be represented
            # as an int (helper function), retrieves it as the customer ID
            for i, j in enumerate(final_list):
                if j == "customerID":
                    if(represents_int(final_list[i+1])):
                        cust_ID = final_list[i+1]

            # If the timestamp exists and the next value can be represented as an int, retrieves it as the timestamp
            for i, j in enumerate(final_list):
                if j == "timestamp":
                    if(represents_int(final_list[i+1]) and int(final_list[i+1]) > 0):
                        timestamp = final_list[i+1]
                        unix_to_time = datetime.datetime.fromtimestamp(int(timestamp))
                        time_string = unix_to_time.strftime('%Y-%m-%d %H:%M:%S')
                        date = time_string[0:10]
                        hour = time_string[11] + time_string[12]

            # Retrieves db customer IDs
            id_query = "select id from customer"
            cursor.execute(id_query)
            id_col = cursor.fetchall()
            ids = []
            for id in id_col:
                ids.append(id[0])

            # If the two necessary keys have been retrieved inserts or updates the data as above. If not, it's not
            # possible to save any data for the request
            try:
                if cust_ID and time_string:
                    if int(cust_ID) in ids:
                        count_query = "select count(*) from hourly_stats where customer_id = (%s) and " \
                                      "extract(hour from time) = (%s) and date(time) = (%s)"
                        cursor.execute(count_query, (cust_ID, hour, date))
                        count = cursor.fetchall()[0][0]
                        if count == 0:
                            ins_query = "insert into hourly_stats (customer_id, time, request_count, invalid_count) " \
                                        "values (%s, %s, %s, %s)"
                            cursor.execute(ins_query, (cust_ID, unix_to_time, 1, 1))
                            print("Created row - invalid")
                            connection.commit()
                        else:
                            req_query = "select request_count,invalid_count from hourly_stats where customer_id = (%s) " \
                                        "and extract(hour from time) = (%s) and date(time) = (%s)"
                            cursor.execute(req_query, (cust_ID, hour, date))
                            all = cursor.fetchall()
                            req_count = all[0][0]
                            invalid_count = all[0][1]
                            update_query = "update hourly_stats set request_count = (%s), invalid_count = (%s) where " \
                                           "customer_id = (%s) and extract(hour from time) = (%s) and date(time) = (%s)"
                            cursor.execute(update_query, (req_count + 1, invalid_count + 1, cust_ID, hour, date))
                            print("Updated row - invalid")
                            connection.commit()
                    else:
                        print("Cannot save invalid request as customerID does not exist in database")
            except UnboundLocalError:
                print("Cannot save invalid request as it's not possible to retrieve the customer's ID and the "
                      "request's timestamp")

# Provides statistics from the server to the user
def get_stats():
    # Connects to db
    connection = connect_to_db()
    cursor = connection.cursor()
    stats = ""
    # Prompts user if the want to view statistics and proceeds to display the appropriate data (daily stats for
    # customer, total number or requests they made on the selected date and total requests that day from all users
    while stats not in ('y', 'n'):
        stats = input("Would you like to see statistics for the requests? Enter y/n ")
    if stats == 'y':
        customer = 0
        while customer < 1:
            customer = int(input("Please enter the ID for the customer you want to see statistics for: "))
        date_query = ""
        while not valid_date(date_query):
            date_query = input("Please enter the date you want to see statistics for: YYYY-MM-DD ")

        retrieve_query = "select * from hourly_stats where customer_ID = (%s) and date(time) = (%s)"
        cursor.execute(retrieve_query, (customer, date_query))
        data = cursor.fetchall()
        sum_reqs = 0
        for row in data:
            print("CustomerID: " + str(row[1]) + ", Time: " + str(row[2]) + ", Requests: " + str(row[3]) +
                  ". Invalid Requests: " + str(row[4]))
            sum_reqs += row[3]
        print("Total daily requests for this customer: " + str(sum_reqs))

        all_reqs_query = "select sum(request_count) from hourly_stats where date(time) = (%s)"
        cursor.execute(all_reqs_query, (date_query,))
        all_reqs = cursor.fetchall()
        print("Total daily requests for all customers: " + str(all_reqs[0][0]))
        # Prompts user to quit and starts the server
        quit = ""
        while quit != 'q':
            quit = input("Press q to quit and start the server ")
        return
    else:
        return

# Helper function, returns true if string can be represented as int
def represents_int(str):
    try:
        int(str)
        return True
    except ValueError:
        return False

# Helper function, Validates the user's input date
def valid_date(str):
    try:
        datetime.datetime.strptime(str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

# Stub function that handles valid requests
def process():
    pass

# Database connection
def connect_to_db():
    #   Appropriate values can be found on PgAdmin, by right-clicking the server (see README)
    try:
        connection = psycopg2.connect(user="postgres",
                                      password="",
                                      host="localhost",
                                      port="5432",
                                      database="")
        return connection
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)

# Prompt user for statistics and start server
if __name__ == '__main__':
    get_stats()
    server = http.server.HTTPServer(('localhost', 8000), MyHandler)
    print('Started http server')
    server.serve_forever()