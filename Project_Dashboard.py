#!/usr/bin/env python
# coding: utf-8

# In[11]:


import pandas as pd
import streamlit as st
import altair as alt
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode

# Load the data
url = "https://raw.githubusercontent.com/James-bot-maker/CT_Doses/main/CT_doses_anonymised.csv"
df = pd.read_csv(url)

# Preprocess the data
df['Booked Date'] = pd.to_datetime(df['Booked Date'], format='%d/%m/%Y', errors='coerce')

# Order examination types by frequency
exam_freq = df['Exam Name'].value_counts()
exam_types = ['All'] + exam_freq.index.tolist()

# Sidebar Filters
st.sidebar.header("Filters")
exam_filter = st.sidebar.selectbox("Select Examination Type", options=exam_types, key="exam_filter")
date_range = st.sidebar.slider(
    "Select Date Range",
    min_value=df['Booked Date'].min().date(),
    max_value=df['Booked Date'].max().date(),
    value=(df['Booked Date'].min().date(), df['Booked Date'].max().date()),
    key="date_filter"
)
age_groups = ['All'] + df['Age Group'].unique().tolist()
age_filter = st.sidebar.radio("Select Age Group", options=age_groups, key="age_filter")

# Filter the data
filtered_df = df.copy()
if exam_filter != "All":
    filtered_df = filtered_df[filtered_df['Exam Name'] == exam_filter]

filtered_df = filtered_df[
    (filtered_df['Booked Date'] >= pd.to_datetime(date_range[0])) &
    (filtered_df['Booked Date'] <= pd.to_datetime(date_range[1]))
]

if age_filter != "All":
    filtered_df = filtered_df[filtered_df['Age Group'] == age_filter]

# Histogram Section
st.subheader("Histogram of Dosage Values")
if not filtered_df.empty:
    hist = alt.Chart(filtered_df).mark_bar(opacity=0.7, color='blue').encode(
        x=alt.X('Dosage:Q', bin=alt.Bin(maxbins=50), title='Dosage (mGy)'),
        y=alt.Y('count()', title='Frequency'),
        tooltip=['Dosage', 'count()']
    )

    kde = alt.Chart(filtered_df).transform_density(
        'Dosage',
        as_=['Dosage', 'Density']
    ).mark_line(color='red').encode(
        x=alt.X('Dosage:Q', title='Dosage (mGy)'),
        y=alt.Y('Density:Q', title='Density'),
        tooltip=[alt.Tooltip('Dosage:Q', title='Dosage'), alt.Tooltip('Density:Q', title='Density')]
    )

    st.altair_chart(hist + kde, use_container_width=True)
else:
    st.warning("No data available for the selected filters.")

# Scatter Plot Section
st.subheader("Scatter Plot of Dosage Over Time")
if not filtered_df.empty:
    scatter = alt.Chart(filtered_df).mark_circle(size=60).encode(
        x=alt.X('Booked Date:T', title='Booked Date'),
        y=alt.Y('Dosage:Q', title='Dosage (mGy)'),
        tooltip=['Booked Date', 'Exam Name', 'Dosage', 'Age Group']
    )

    regression_line = (
        alt.Chart(filtered_df)
        .transform_regression('Booked Date', 'Dosage')
        .mark_line(color='red')
        .encode(x='Booked Date:T', y='Dosage:Q')
    )

    st.altair_chart(scatter + regression_line, use_container_width=True)
else:
    st.warning("No data available for the selected filters.")

# Highlight outliers: 2 standard deviations away from the mean
def highlight_outliers(df):
    outliers = []
    for exam in df['Exam Name'].unique():
        exam_data = df[df['Exam Name'] == exam]
        mean = exam_data['Dosage'].mean()
        std = exam_data['Dosage'].std()
        exam_data['Mean Examination Dose'] = round(mean, 1)  # Round mean dose to 1 decimal place
        outliers.append(
            exam_data[
                (exam_data['Dosage'] < mean - 2 * std) |
                (exam_data['Dosage'] > mean + 2 * std) |
                (exam_data['Dosage'].isnull()) |  # Include null dosages
                (exam_data['Dosage'] == 0)        # Include zero dosages
            ]
        )
    return pd.concat(outliers)

# Possible Incorrect/Missing Dosage Data Section
st.subheader("Possible Incorrect/Missing Dosage Data")
filtered_df_table = highlight_outliers(filtered_df)

# Filter outliers further by date range
filtered_df_table = filtered_df_table[
    (filtered_df_table['Booked Date'] >= pd.to_datetime(date_range[0])) &
    (filtered_df_table['Booked Date'] <= pd.to_datetime(date_range[1]))
]

# Show number of entries
st.write(f"Number of Entries: {len(filtered_df_table)}")

if not filtered_df_table.empty:
    # Configure AgGrid
    gb = GridOptionsBuilder.from_dataframe(filtered_df_table)
    gb.configure_default_column(editable=True)
    gb.configure_selection('multiple', use_checkbox=True)
    grid_options = gb.build()

    grid_response = AgGrid(
        filtered_df_table,
        gridOptions=grid_options,
        data_return_mode=DataReturnMode.AS_INPUT,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
    )

    updated_data = grid_response['data']

    # Save updated data to the CSV file
    if st.button("Submit Changes"):
        updated_data.to_csv("updated_CT_doses.csv", index=False)
        st.success("Changes saved successfully!")
else:
    st.warning("No data available for the selected filters.")


# In[ ]:




