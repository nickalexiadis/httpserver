# httpserver
In order for the program to function correctly, a PostgreSQL server and database must be created (this was done using PgAdmin).

Postgresql and PgAdmin can be downloaded at the links below:

http://www.postgresql.org/download/

https://www.pgadmin.org/download/

It is important to remember the user account details when installing as they are used to connect to the database.

After creating the database, the correct information must be filled in at lines 273-277 of server1.py. “User”, “host” and “port can be found by right-clicking the created server at pgAdmin and selecting the Connection tab. “Password” is the user’s password and “database” refers to the name of the created database. The database can be created by right-clicking on the server and selecting Create - > Database.

Any editor should work for the changes. The program was created in the PyCharm IDE.

In order to run the program, the user must install the psycopg2 module. This can be done by typing pip install psycopg2 in the CL.

After the necessary changes have been made to the server1.py, the user must run create_database.py (python create_database.py), which will populate the database with the tables and sample data. There should be confirmation of this in the console and it can be doublechecked by selecting schemas -> tables at pgAdmin.

Afterwards, the server1.py file should be run (python server1.py). The program will initially prompt the user if they wish to view statistics or proceed to start the server. If “y” is pressed the user has to insert the customer’s ID and a date in the appropriate format to see the stats. Alternatively, the server starts running.

To test the program, the Postman app, as it allows to efficiently and quickly send POST requests with the desired JSON body. The user can also alter the User-Agent. Requests were made to http://localhost:8000/, though that can be changed. If so, line 285 in server1.py should also be changed to the correct values.

Depending on the request, the user should see confirmation of a row being inserted or updated in the database, as well as whether it is valid or not. There is also feeback, if the information from the request cannot be saved and why.
