import streamlit as st
import pandas as pd 
import numpy as np 

st.title('Uber Pickups in Merida')
DATA_URL = ('https://s3-us-west-2.amazonaws.com/'
            'streamlit-demo-data/uber-raw-data-sep14.csv.gz') 
DATE_COLUMN = 'date/time'

@st.cache_data
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
    return data



#-------- 
#     DATA 
#--------   
#Text element yo let the user know that data is loading
data_load_state = st.text('Loading data...')
#loading 1000 rows of data into the df
data = load_data(1000)
#notify that data is already saved
data_load_state.text("Done! (using st.cache_data)")


if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(data)

#--------------------------
#       HISTOGRAM
#--------------------------
st.subheader('Number of pickups by hour')
hist_values = np.histogram(
        data[DATE_COLUMN].dt.hour, bins=24, range=(0,24))[0]

st.bar_chart(hist_values)

#hist_values now contains the 24 bin values


#------------------------------------
#               MAPS
#------------------------------------
st.subheader('Map of all pickups')
st.map(data)


#PLOTTING THE DATA ON A MAP BY BUSIEST HOUR
hour_to_filter = 17
filtered_data = data[data[DATE_COLUMN].dt.hour == hour_to_filter]
st.subheader(f'Map of all pickups at {hour_to_filter}:00')
st.map(filtered_data)

#USING A SLIDER TO FILTER THE DATA BY HOUR
hour_to_filter = st.slider('hour', 0, 23, 17, step=1) #min, max, default value 
filtered_data = data[data[DATE_COLUMN].dt.hour == hour_to_filter]
st.subheader(f'Map of all pickups at selected hour: {hour_to_filter}:00')
st.map(filtered_data)


#--------------------------
#       INTERACTIVE
#--------------------------

