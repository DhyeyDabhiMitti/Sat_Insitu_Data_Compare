import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import datetime
from PIL import Image
import boto3
import io
from ast import literal_eval

def safe_literal_eval(input_str):
    try:
        return literal_eval(input_str)
    except:
        return None


st.title('Satellite-In Situ Data Comparision!')

if 's3' not in st.session_state:
    id = st.secrets['aws_access_key_id']
    access_key = st.secrets['aws_secret_access_key']
    region_name = st.secrets['region_name']
    st.session_state['bucket_name'] = st.secrets['bucket_name']
    s3 = boto3.client('s3', aws_access_key_id=id,
                  aws_secret_access_key=access_key,
                  region_name=region_name)
    st.session_state['s3'] = s3

sat_data = pd.read_csv('./data/sat_data.csv')
sat_data.Date = pd.to_datetime(sat_data.Date)
land_data = pd.read_csv('./data/land_data.csv')
land_data.Date = pd.to_datetime(land_data.Date)

threshold = st.slider('Select the threshold range of days: ',min_value=0,max_value=10,step=1,value=2)
merged_table = pd.merge_asof(sat_data,land_data,on='Date',by='croppableAreaId',tolerance=datetime.timedelta(days=threshold))
field_ids = list(merged_table.croppableAreaId.unique())
try:
    field_id = st.selectbox('Select Field ID:',field_ids)
except:
    st.write("Enter a Integer Value!")
filtered_table = merged_table[merged_table['croppableAreaId']==field_id]
filtered_table.Date = filtered_table.Date.dt.date


temp_table = filtered_table[['Date','pd','ps','pv','FieldPhot1hldr','FieldPhot2hldr','Soilmoist5hldr']].reset_index().drop(columns=['index'])
st.dataframe(temp_table)
temp_table['days']= temp_table.Date.apply(lambda x: x-temp_table.loc[0,'Date'])
fig, ax = plt.subplots()
ax.plot(temp_table['days'], temp_table['pd'])
ax.set_xlabel('Days')
ax.set_ylabel('Satellite Data')
ax.set_title('Simple Line Plot')
st.pyplot(fig)
selected_index = st.slider('Select the index of the table: ',min_value=0,max_value=temp_table.shape[0]-1,step=1,value=0)
selected_date = temp_table.iloc[selected_index,0]

col1,col2 = st.columns(2)
with col1:
    st.write(pd.DataFrame(temp_table.iloc[selected_index,1:4]).rename(columns={selected_index:selected_date}))
with col2:
    fig, ax = plt.subplots()
    sizes = temp_table.iloc[selected_index,1:4].values
    sum_sizes = sizes.sum()
    for size in sizes:
        size=(size*100/sum_sizes)
    labels = ['pd','ps','pv']
    ax.pie(sizes, labels=labels, autopct='%1.1f%%')
    ax.axis('equal')
    st.pyplot(fig)

col1,col2 = st.columns(2)
with col1:
    if temp_table.loc[selected_index,'FieldPhot1hldr']!='None':
        print('Starting Image 1 processing!')
        key = 'CropIn_Photos/'+str(temp_table.loc[selected_index,'FieldPhot1hldr'])
        try:
            response = st.session_state['s3'].get_object(Bucket=st.session_state['bucket_name'], Key=key)
            image_content = response['Body'].read()
            image = Image.open(io.BytesIO(image_content))
            st.image(image)
        except:
            pass
with col2:
    if temp_table.loc[selected_index,'FieldPhot2hldr']!='None':
        print('Starting Image 2 processing!')
        try:
            key = 'CropIn_Photos/'+temp_table.loc[selected_index,'FieldPhot2hldr']
            response = st.session_state['s3'].get_object(Bucket=st.session_state['bucket_name'], Key=key)
            image_content = response['Body'].read()
            image = Image.open(io.BytesIO(image_content))
            st.image(image)
        except:
            pass

if not pd.isna(temp_table.loc[selected_index,'Soilmoist5hldr']):
    st.write('Moisture Sensor Photos:')
    lst = safe_literal_eval(temp_table.loc[selected_index,'Soilmoist5hldr'])
    for image in lst:
        try:
            key = 'CropIn_Photos/'+image['originalFileName']
            response = st.session_state['s3'].get_object(Bucket=st.session_state['bucket_name'], Key=key)
            image_content = response['Body'].read()
            image = Image.open(io.BytesIO(image_content))
            st.image(image)
        except:
            pass
