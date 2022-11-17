"""Driver file to load and clean Hospital General Information data."""

import sys
import time
import datetime
from cleandata import clean_quality_data
from loaddata import connect_to_sql, load_hospital_info


nfile = "./data/hospital_quality/" + str(sys.argv[2])
insert_data = clean_quality_data(nfile)

collect_date = str(sys.argv[1])
collect_date = datetime.datetime.strptime(collect_date, "%Y-%m-%d")

# Subset data to insert (Testing Purposes)
insert_data = insert_data.iloc[0:5, ]
print(insert_data)

# Start Insertion
num_rows_inserted = 0
failed_insertion = []
conn = connect_to_sql()

with conn.transaction():
    for i in range(insert_data.shape[0]):
        data = insert_data.loc[int(i), ]
        try:
            with conn.transaction():
                print("loading line " + str(i))  # Temporary debug code
                load_hospital_info(conn, data, collect_date)
        except Exception:
            failed_insertion.append(i)
            print("Insertion failed at line " + str(i))
        else:
            num_rows_inserted += 1

print("Read in " + str(insert_data.shape[0]) + " lines in total")
print("Successfully added " + str(num_rows_inserted))

# Output csv with lines that failed to insert
if failed_insertion:
    failed_lines = insert_data.iloc[failed_insertion]
    curr_time = time.strftime("%H_%M_%S", time.localtime())
    fname = "./data/hospital_quality/" + curr_time + "_failed_insertion.csv"
    failed_lines.to_csv(fname)
    print("Saved lines that failed to insert in " + fname)

# Only run these part if all is done, make some kind of fail save.
conn.commit()
conn.close()