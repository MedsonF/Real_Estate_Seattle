import pandas as pd
import numpy as np
import streamlit as st
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
import plotly.express as px
from datetime import datetime

st.set_page_config(layout='wide')

@st.cache_data()
def get_data(path):
    df = pd.read_csv(path)
    return df

def set_feature(data):
    # add new features
    data['price_m2'] = data['price'] / data['sqft_lot']
    data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')

    return data

def overview_data(data):
    # data overview
    f_attributes = st.sidebar.multiselect('Enter columns', data.columns)
    f_zipcode = st.sidebar.multiselect('Enter zipcode', data['zipcode'].unique())

    st.title('Data Overview')
    # st.write(f"Selected attributes: {f_attributes}")
    # st.write(f"Selected zipcodes: {f_zipcode}")

    if (f_attributes != []) & (f_zipcode != []):
        data = data.loc[data['zipcode'].isin(f_zipcode), f_attributes]

    elif (f_attributes == []) & (f_zipcode != []):
        data = data.loc[data['zipcode'].isin(f_zipcode), :]

    elif (f_attributes != []) & (f_zipcode == []):
        data = data.loc[:, f_attributes]

    else:
        data = data.copy()

    st.dataframe(data)

    c1, c2 = st.columns((1, 1))
    # avarage metrics
    df1 = data[['id', 'zipcode']].groupby('zipcode').count().reset_index()
    df2 = data[['price', 'zipcode']].groupby('zipcode').mean().reset_index()
    df3 = data[['sqft_living', 'zipcode']].groupby('zipcode').mean().reset_index()
    df4 = data[['price_m2', 'zipcode']].groupby('zipcode').mean().reset_index()

    # merge
    m1 = pd.merge(df1, df2, on='zipcode', how='inner')
    m2 = pd.merge(m1, df3, on='zipcode', how='inner')
    df = pd.merge(m2, df4, on='zipcode', how='inner')

    df.columns = ['Zipcode', 'Total Houses', 'Price', 'Sqft Living', 'Price/M2']

    c1.header('Avarege Values')
    c1.dataframe(df, height=700)

    # statistic descriptive

    num_attributes = data.select_dtypes(include=['int64', 'float64'])
    media = pd.DataFrame(num_attributes.apply(np.mean))
    mediana = pd.DataFrame(num_attributes.apply(np.median))
    std = pd.DataFrame(num_attributes.apply(np.std))

    max_ = pd.DataFrame(num_attributes.apply(np.max))
    min_ = pd.DataFrame(num_attributes.apply(np.min))

    df1 = pd.concat([max_, min_, media, mediana, std], axis=1).reset_index()

    df1.columns = ['Attributes', 'Max', 'Min', 'Mean', 'Median', 'Std']

    c2.header('Descriptive Analysis')
    c2.dataframe(df1, height=700)

    return None

def portifolio_density(data):
    st.title('Region Overview')
    st.header('Portifolio Density')
    density_map = folium.Map(location=[data['lat'].mean(),
                                       data['long'].mean()],
                             default_zoom_start=15)

    marker_cluster = MarkerCluster().add_to(density_map)
    data = pd.DataFrame(data)
    dict_map = {j: i for i, j in enumerate(data.columns)}
    for row in data.values:
        folium.Marker([row[dict_map['lat']], row[dict_map['long']]],
                      popup='Sold R${0} on: {1}. Features: {2} sqft, {3} bedrooms, {4} bathrooms, ' \
                            'year built: {5}'.format(row[dict_map['price']], row[dict_map['date']],
                                                     row[dict_map['sqft_living']], row[dict_map['bedrooms']],
                                                     row[dict_map['bathrooms']], row[dict_map['yr_built']])).add_to(marker_cluster)

    folium_static(density_map)

    return None

def commercial_distribution(data):
    st.sidebar.title('Commercial Option')
    st.title('Commercial Attributes')

    ##------------ avarage price/year

    data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')

    # filter
    min_year_built = int(data['yr_built'].min())
    max_year_built = int(data['yr_built'].max())

    st.sidebar.subheader('Select Max Year Built')
    f_year_built = st.sidebar.slider('Year Built', min_year_built,
                                     max_year_built,
                                     min_year_built)

    st.header('Avarage Price per Year Built')

    # data slect
    df = data.loc[data['yr_built'] < f_year_built]
    df = df[['yr_built', 'price']].groupby('yr_built').mean().reset_index()

    # plot
    fig = px.line(df, x='yr_built', y='price')
    st.plotly_chart(fig, use_container_width=True)

    ##----------- avarage price/day

    st.header('Avarage Price per day')
    st.sidebar.subheader('Select Max date')

    # filter
    min_date = datetime.strptime(data['date'].min(), '%Y-%m-%d')
    max_date = datetime.strptime(data['date'].max(), '%Y-%m-%d')

    f_date = st.sidebar.slider('Date', min_date, max_date, min_date)

    # data filtering
    data['date'] = pd.to_datetime(data['date'])
    df = data.loc[data['date'] < f_date]
    df = df[['date', 'price']].groupby('date').mean().reset_index()

    # plot
    fig = px.line(df, x='date', y='price')
    st.plotly_chart(fig, use_container_width=True)

    # ---------- Histograma
    st.header('Price Distribuition')
    st.sidebar.subheader('Select Max Price')

    min_price = int(data['price'].min())
    max_price = int(data['price'].max())
    avg_price = int(data['price'].mean())

    # filter
    f_price = st.sidebar.slider('Price', min_price, max_price, avg_price)
    df = data.loc[data['price'] < f_price]

    # data plot
    fig = px.histogram(df, x='price', nbins=50)
    st.plotly_chart(fig, use_container_width=True)

    return None

def attributes_distribution(data):
    st.sidebar.title('Attributes Options')
    st.title('House Attributes')

    # filters
    f_bedrooms = st.sidebar.selectbox('Max number of bedrooms',
                                      sorted(set(data['bedrooms'].unique())))
    f_bathrooms = st.sidebar.selectbox('Max number of bathrooms',
                                       sorted(set(data['bathrooms'].unique())))
    f_floors = st.sidebar.selectbox('Max number of floors',
                                    sorted(set(data['floors'].unique())))
    f_waterview = st.sidebar.checkbox('Only Houses with Water View')

    c1, c2 = st.columns(2)

    # House per bedroms
    c1.header('House per bedrooms')
    df = data[data['bedrooms'] < f_bedrooms]
    fig = px.histogram(df, x='bedrooms', nbins=19)
    c1.plotly_chart(fig, use_container_width=True)

    # House per bathrooms
    c2.header('Houses per bathrooms')
    df = data[data['bathrooms'] < f_bathrooms]
    fig = px.histogram(df, x='bathrooms', nbins=19)
    c2.plotly_chart(fig, use_container_width=True)

    # House per floors
    c1.header('House per floors')
    df = data[data['floors'] < f_floors]
    fig = px.histogram(df, x='floors', nbins=19)
    c1.plotly_chart(fig, use_container_width=True)

    # House per water view
    if f_waterview:
        df = data[data['waterfront'] == 1]

    else:
        df = data.copy()

    c2.header('Water Front')
    fig = px.histogram(df, x='waterfront', nbins=10)
    c2.plotly_chart(fig, use_container_width=True)
    return None

if __name__ == "__main__":
    # ETL
    # data extration
    path = 'kc_house_data.csv'

    data = get_data(path)
    
    # transformation
    data = set_feature(data)

    overview_data(data)

    portifolio_density(data)

    commercial_distribution(data)

    attributes_distribution(data)

