"""
Driver file to generate weekly reports using interactive dashboard

Run by typing 'streamlit run dashboard.py 2022-10-07' in terminal

Authors: Carol Ling     <caroll2@andrew.cmu.edu>
#        Xiaochen Sun   <xsun3@andrew.cmu.edu>
#        Xiaonuo Xu     <xiaonuox@andrew.cmu.edu>
"""

import sys
import datetime
import warnings
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from getdata import connect_to_sql2
from getdata import get_records_number, get_beds_detail, get_beds_sum_by, \
                    get_covid_change, get_distinct_collection_date

# Ignore the warning message from the code
warnings.filterwarnings("ignore")

# Display all columns from pandas data frame
# pd.set_option('display.max_columns', None)

collect_date = str(sys.argv[1])
collect_date = datetime.datetime.strptime(collect_date, "%Y-%m-%d").date()

# Create connection object
conn = connect_to_sql2()
cur = conn.cursor()

# Begin generating analysis

# Title of the report
title = "Hospital Beds and COVID Cases Report for Week " + str(collect_date)
st.title(title)

# Part 1
st.header("1. Hospital records loaded")

st.markdown("A summary of how many hospital records were loaded in the most" +
            "recent week, and how that compares to previous weeks.")

st.subheader("Health and Human Services (HHS) Data")
record_number = get_records_number(conn, "hospital_data", collect_date)

if not record_number:
    st.text("Server lacks HHS data on " + str(collect_date))
else:
    for key, value in record_number.items():
        st.text("PostgreSQL server contains " + str(value) +
                " HHS records from " + str(key))

# Part 2
st.header("2. Hospital beds available and in use")

st.markdown("A table summarizing the number of adult and pediatric beds " +
            "available this week, the number used, and the number used by " +
            "patients with COVID, compared to the 4 most recent weeks.")

bed_recent = get_beds_detail(conn, collect_date, True)
bed_recent = bed_recent.iloc[:, [0, 1, 3, 4, 5, -2]]
bed_recent = bed_recent.set_index('collection_date')

if bed_recent is False:
    st.text("Server lacks HHS data on " + str(collect_date))
else:
    st.dataframe(bed_recent)

st.header("3. Hospital beds information by quality rating")

st.markdown("A table summarizing the number of beds in use by " +
            "hospital quality rating, so we can compare high-quality " +
            "and low-quality hospitals.")

bed_by_quality = get_beds_sum_by(conn, collect_date, "quality_rating")
bed_by_quality = bed_by_quality.iloc[:, 3:8]
bed_by_quality = bed_by_quality.round(0).astype('Int64')

if bed_by_quality is False:
    st.text("Server lacks HHS and CMS data on " + str(collect_date))
else:
    st.dataframe(bed_by_quality)

st.header("4. Hospital bed use by all cases and covid of all time")

st.markdown("A plot of the total number of hospital beds used " +
            "per week, over all time, split into all cases " +
            "and COVID cases.")

bed_all_time = get_beds_detail(conn, collect_date, False)
bed_all_time = bed_all_time.iloc[:, 3:]
bed_all_time = bed_all_time.set_index('collection_date')

if bed_all_time is False:
    st.text("Server lacks HHS data on " + str(collect_date))
else:
    st.dataframe(bed_all_time)
    xtick = list(bed_all_time.index)
    xtick = sorted([date.strftime("%y-%m-%d") for date in xtick])
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    plt.plot(xtick, bed_all_time["covid_beds_use"], label="COVID Only")
    plt.plot(xtick, bed_all_time["covid_beds_use"] +
             bed_all_time["non_covid_beds_use"], label="Total")
    ax.set_xticklabels(sorted(xtick), rotation=45, ha="right")
    ax.set_ylim(bottom=0)
    plt.title("Cumulative Sum of all Hospital Bed Usage per Week")
    plt.xlabel("Date (YY-MM-DD)")
    plt.ylabel("Cumulative Beds in Use")
    plt.fill_between(
        x=xtick,
        y1=bed_all_time["covid_beds_use"],
        color="#1F77B4",
        alpha=0.4)
    plt.fill_between(
        x=xtick,
        y1=bed_all_time["covid_beds_use"] + bed_all_time["non_covid_beds_use"],
        color="#FF7F0E",
        alpha=0.2)
    plt.legend()
    st.write(fig)

st.header("5. Hospital utilization by type of hospital ownership")

st.markdown("Graphs of hospital utilization (the percent of " +
            "available beds being used) by type of hospital " +
            "(private or public), over time.")

listofdate = get_distinct_collection_date(cur, "hospital_data")
for i in listofdate:
    bed_by_ownership = get_beds_sum_by(conn, i, "ownership")
    bed_by_ownership = bed_by_ownership.iloc[:, 7:] 

    if bed_by_ownership is False:
        st.text("Server lacks HHS and CMS data on " + str(collect_date))
    else:
        labels = bed_by_ownership["ownership"]
        adult_util = bed_by_ownership["adult_utilization"]
        ped_util = bed_by_ownership["pediatric_utilization"]
        icu_util = bed_by_ownership["icu_utilization"]
        x = np.arange(len(labels))
        width = 0.35
        fig, ax = plt.subplots()
        rects1 = ax.bar(x - width/2, adult_util, width, label='adult_utilization')
        rects2 = ax.bar(x + width/2, ped_util, width, label='pediatric_utilization')
        rects3 = ax.bar(x + width/2, icu_util, width, label='icu_utilization')
        ax.set_ylabel('Proportion')
        ax.set_title('Hospital utilization of different hospital ownership')
        ax.set_xticks(x, labels)
        ax.legend()
        ax.bar_label(rects1, padding=3)
        ax.bar_label(rects2, padding=3)
        ax.bar_label(rects3, padding=3)
    
        st.write(fig)



st.header("6. Rank states by change in covid case since last week")

st.markdown("A table of the states in which the number of cases " +
            "has increased by the most since last week.")

state_rank = get_covid_change(conn, collect_date, 10, "state")

if state_rank is False:
    st.text("Server lacks HHS and CMS data on " + str(collect_date))
else:
    st.dataframe(state_rank)

st.header("7. Rank hospital by change in covid case since last week")

st.markdown("A table of the hospitals (including names and locations) " +
            "with the largest changes in COVID cases in the last week.")

hospital_rank = get_covid_change(conn, collect_date, 10, "hospital_id")

if hospital_rank is False:
    st.text("Server lacks HHS and CMS data on " + str(collect_date))
else:
    st.dataframe(hospital_rank)

st.text("Made by Team Pipers, 2022")

# Close the connection to psql server
cur.close()
conn.close()
