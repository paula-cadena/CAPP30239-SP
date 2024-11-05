import pandas as pd
import os
import numpy as np

def join_datasets():

    folder_path = '/Users/paulacadena/CAPP30239-SP/data'
    dataframes = []

    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(folder_path, filename)
            try:
                df = pd.read_csv(file_path, encoding='ISO-8859-1')
                dataframes.append(df)
            except UnicodeDecodeError:
                print(f'Could not decode {filename}. Skipping.')

    return pd.concat(dataframes, ignore_index=True)

def clean_dataset():

    world_bank = join_datasets()

    # Correctly name missing values
    world_bank.replace('..', np.nan, inplace=True)
    # Drop missing values in identificating columns
    world_bank.dropna(subset=['Series Code',
                              'Country Code', 'Series Name'], inplace=True)
    # Drop wrongly identified country codes
    world_bank = world_bank[world_bank['Country Code'].str.len() <= 3]

    return world_bank

def wide_long_wb():
    world_bank = clean_dataset()
    # Identify the columns to transform
    value_vars = [col for col in world_bank.columns if 'YR' in col]
    # Melt the DataFrame
    long_format = pd.melt(world_bank,
                          id_vars=[col for col in world_bank.columns if col not in value_vars],
                          value_vars=value_vars,
                          var_name='YEAR',
                          value_name='Value')
    # Extract the year from the 'YEAR' column
    long_format['YEAR'] = long_format['YEAR'].str.extract(
        r'(\d{4})')[0].astype(int)
    # Change Value column to numeric
    long_format['Value'] = pd.to_numeric(long_format['Value'], errors='coerce')

    return long_format

def add_continents(df):
    continents = pd.read_csv('/Users/paulacadena/CAPP30239-SP/data/old/continents2.csv',
                             usecols=['alpha-3', 'region',
                                      'sub-region', 'country-code'])
    df = df.merge(continents, left_on='Country Code', right_on='alpha-3',
                  how='left')
    df['country-code'] = df['country-code'].fillna(-1).astype(int)
    df.drop(columns='alpha-3', inplace=True)
    df.loc[df['Country Name'] == 'Kosovo', 'region'] = 'Europe'
    df.loc[df['Country Name'] == 'Channel Islands', 'region'] = 'Europe'
    df['region'] = df['region'].fillna('Aggregated data')
    return df

def add_decade(df):

    df['YEAR'] = df['YEAR'].astype(int)
    df['DECADE'] = (df['YEAR'] // 10) * 10
    return df

def world_bank_complete():

    df = wide_long_wb()
    df = add_continents(df)
    df = add_decade(df)
    df = df.rename(columns={'Country Name': 'Country', 'Series Name': 'Series',
                            'YEAR': 'Year', 'region': 'Region',
                            'sub-region': 'Sub-region'})
    if 'Value' in df.columns:
        df['Value'] = df['Value'].round(2)
    return df
