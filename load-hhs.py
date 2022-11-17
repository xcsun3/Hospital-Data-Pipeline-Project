"""Driver file to load and clean weekly HHS data."""

import sys
import time
from cleandata import clean_hhs_data
from loaddata import connect_to_sql, load_hospital_data, load_hospital_location

nfile = "./data/hhs_weekly/" + str(sys.argv[1])
insert_data = clean_hhs_data(nfile)

# Subset data to insert (Testing Purposes)
insert_data = insert_data.iloc[0:10, ]
print(insert_data)

# Start Insertion
num_rows_inserted = 0
failed_insertion_data = []
failed_insertion_location = []
conn = connect_to_sql()

with conn.transaction():
    for i in range(insert_data.shape[0]):
        data = insert_data.loc[int(i), ]
        try:
            with conn.transaction():
                load_hospital_data(conn, data)
        except Exception:
            failed_insertion_data.append(i)
            print("Insertion into hospital_data failed at line " + str(i))
        try:
            with conn.transaction():
                load_hospital_location(conn, data)
        except Exception:
            failed_insertion_location.append(i)
            print("Insertion into hospital_location failed at line " + str(i))
        else:
            num_rows_inserted += 1

print("Read in " + str(insert_data.shape[0]) + " lines in total")
print("Successfully added " + str(num_rows_inserted))

# Output csv with lines that failed to insert
if failed_insertion_data:
    failed_lines = insert_data.iloc[failed_insertion_data]
    curr_time = time.strftime("%H_%M_%S", time.localtime())
    fname = "./data/hhs_weekly/" + curr_time + "_failed_insertion_data.csv"
    failed_lines.to_csv(fname)
    print("Saved lines that failed to insert in " + fname)

if failed_insertion_location:
    failed_lines = insert_data.iloc[failed_insertion_location]
    curr_time = time.strftime("%H_%M_%S", time.localtime())
    fname = "./data/hhs_weekly/" + curr_time + "_failed_insertion_loca.csv"
    failed_lines.to_csv(fname)
    print("Saved lines that failed to insert in " + fname)

# Only run these part if all is done, make some kind of fail save.
conn.commit()
conn.close()