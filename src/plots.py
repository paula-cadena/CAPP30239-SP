import altair as alt
import pandas as pd
import os
from vega_datasets import data
alt.data_transformers.enable('vegafusion')
from theme import custom_theme
alt.themes.register("custom_theme", custom_theme)
alt.themes.enable("custom_theme")
from clean_data import world_bank_complete

# World Map

def world_map(series):

    world_bank = world_bank_complete()

    # Filter data based on the selected series
    world_bank = world_bank[world_bank['Series'] == series]

    # Filtering the first year and last year available data for each country
    first_data = world_bank.sort_values(
        by=['Country', 'Year']).groupby('Country').first().reset_index()
    last_data = world_bank.sort_values(
        by=['Country', 'Year'], ascending=False).groupby('Country'
                                                         ).first(
                                                         ).reset_index()

    # Calculate the min and max for the legend
    combined_data = pd.concat([first_data, last_data])
    min_value = combined_data['Value'].min()
    max_value = combined_data['Value'].max()

    # Load important world map
    source = alt.topo_feature(data.world_110m.url, 'countries')
    background = alt.Chart(source).mark_geoshape(fill='lightgray',
                                                 stroke='white')

    # First map layer for first year available data
    first_map = (
        background
        + alt.Chart(source)
        .mark_geoshape(stroke='black', strokeWidth=0.15)
        .encode(
            color=alt.Color(
                'Value:Q',
                scale=alt.Scale(
                    domain=[min_value, 0, max_value]
                ),
                legend=alt.Legend()
            ),
            tooltip=[
                alt.Tooltip('Country:N', title='Country'),
                alt.Tooltip('Year:O', title='Year'),
                alt.Tooltip('Value:Q', title='Value')
            ]
        )
        .transform_lookup(
            lookup='id',
            from_=alt.LookupData(first_data, 'country-code',
                                 ['Value', 'Country', 'Year'])
        )
    ).properties(title='First Available Year by Country').project('equalEarth')

    # Second map layer for last year available data
    last_map = (
        background
        + alt.Chart(source)
        .mark_geoshape(stroke='black', strokeWidth=0.15, fillOpacity=1)
        .encode(
            color=alt.Color(
                'Value:Q',
                scale=alt.Scale(
                    domain=[min_value, 0, max_value]
                ),
                legend=alt.Legend()
            ),
            tooltip=[
                alt.Tooltip('Country:N', title='Country'),
                alt.Tooltip('Year:O', title='Year'),
                alt.Tooltip('Value:Q', title='Value')
            ]
        )
        .transform_lookup(
            lookup='id',
            from_=alt.LookupData(last_data, 'country-code',
                                 ['Value', 'Country', 'Year'])
        )
    ).properties(title='Last Available Year by Country').project('equalEarth')

    final_map = alt.vconcat(
        first_map,
        last_map
    ).configure_view(strokeWidth=0).properties(title=f'{series}')

    return final_map

# Heatmap

def heat_map_series(series):

    world_bank = world_bank_complete()
    # Filter data by series, exclude aggregate obs
    world_bank = world_bank[(world_bank['Series'] == series) &
                            (world_bank['Region'] != 'Aggregated data') &
                            (world_bank['Year'] < 2023)]  # Incomplete info
    # Pivot to create a column for series
    pivot_data = world_bank.pivot(index=['Country', 'Region', 'Year'],
                                columns='Series', values='Value').reset_index()
    # 2D Histogram Heatmap
    heat_map = alt.Chart(pivot_data).mark_rect().encode(
        alt.X('Year:Q').bin(maxbins=62),
        alt.Y(series, title='% Population').bin(maxbins=40),
        alt.Color('count():Q', title='Count')
        ).properties(
        title=f'{series}'
    )
    return heat_map

# Bar chart

def top_bottom_bars(series, year):

    world_bank = world_bank_complete()
    # Filter data based on the provided series
    world_bank = world_bank[(world_bank['Series'] == series) &
                            (world_bank['Region'] != 'Aggregated data') &
                            (world_bank['Year'] == year)]

    # Drop any missing values in 'Value' to avoid issues in sorting
    world_bank = world_bank.dropna(subset=['Value'])

    # Sort by 'Value' and select top 10 and bottom 10
    top_10 = world_bank.nlargest(10, 'Value')
    bottom_10 = world_bank.nsmallest(10, 'Value')

    # Concatenate top and bottom 10 data
    top_bottom = pd.concat([top_10, bottom_10])

    # Create a bar chart
    bar_chart = alt.Chart(top_bottom).mark_bar().encode(
        x=alt.X('Value:Q', title=f'{series} Value'),
        y=alt.Y('Country:N', sort='-x', title='Country'),
        color=alt.condition(
            alt.datum['Value'] > 0,
            alt.value('#166417'),
            alt.value('#742183')),
        tooltip=['Country', 'Value']
    ).properties(
        title=f'{year}'
    )

    return bar_chart

def bars_twoyears(series, year):

    initial_year = top_bottom_bars(series, year)
    year_before = top_bottom_bars(series, year - 1)

    min_value = min(initial_year.data['Value'].min(),
                    year_before.data['Value'].min())
    max_value = max(initial_year.data['Value'].max(),
                    year_before.data['Value'].max())

    # Update the x-axis scale for both charts
    initial_year = initial_year.encode(
        x=alt.X('Value:Q', scale=alt.Scale(domain=[min_value, max_value])))
    year_before = year_before.encode(
        x=alt.X('Value:Q', scale=alt.Scale(domain=[min_value, max_value])))

    # Concatenate both charts
    final_chart = alt.vconcat(
        year_before,
        initial_year
    ).properties(title=f'{series}: Top 10 and Bottom 10 Countries')

    return final_chart

# Lines

def lines_subregion(series):

    world_bank = world_bank_complete()
    # Data adjusted for chart
    world_bank = world_bank[(world_bank['Series'] == series)]
    world_bank = world_bank.dropna(subset=['Value'])
    world_bank = world_bank.dropna(subset=['Sub-region'])
    world_bank = world_bank.groupby(['Year', 'Sub-region'],
                                    as_index=False)['Value'].mean()

    # Lines by subregion
    base = alt.Chart(world_bank).encode(color=alt.Color("Sub-region",
                                                        legend=None)
                                        ).properties(
                                            width=600,  # Same as theme
                                            height=800)  # Double theme
    lines = base.mark_line().encode(x='Year:T', y='Value:Q')

    # Identify last obs
    last_obs = base.mark_circle().encode(
        x=alt.X("last_year['Year']:T"),
        y=alt.Y("last_year['Value']:Q")
    ).transform_aggregate(
        last_year="argmax(Year)",
        groupby=["Sub-region"]
    )

    # Add text for identification
    sub_region = last_obs.mark_text(align='left', dx=4
                                    ).encode(text="Sub-region")

    final_chart = (lines + last_obs + sub_region
                   ).encode(x=alt.X(title='Year'),
                            y=alt.Y(title='Ratio',
                                     scale=alt.Scale(domain=[30, 90]))
                                     ).properties(
                                         title=f'{series} by Sub-region')
    return final_chart

# Area

def area_pop(series1, series2):

    world_bank = world_bank_complete()

    # Data adjusted for chart
    world_bank = world_bank[(world_bank['Series'].isin([series1, series2])) &
                            (world_bank['Region'] != 'Aggregated data')]
    world_bank = world_bank.dropna(subset=['Value'])
    world_bank = world_bank.groupby(['Year', 'Series'], as_index=False
                                    )['Value'].sum()

    # Area chart
    area = alt.Chart(world_bank).mark_area().encode(
            x="Year:T",
            y=alt.Y("Value:Q", stack="normalize",
                    title='Percentage of total population'),
            color="Series:O"
        ).properties(title=f'{series1} vs {series2}: Worldwide')
    return area

# Scatter plot

def scatter_plot(series1, series2, title, axis1, axis2):

    world_bank = world_bank_complete()

    # Data filter
    world_bank = world_bank[(world_bank['Series'].isin([series1, series2])) &
                            (world_bank['Region'] != 'Aggregated data')]
    world_bank = world_bank.dropna(subset=['Value'])

    # Sort and Drop duplicates to keep only the last available year for country
    world_bank = world_bank.sort_values(['Country', 'Series', 'Year'],
                                        ascending=[True, True, False])
    world_bank = world_bank.drop_duplicates(subset=['Country', 'Series'],
                                            keep='first')
    # Define axis max value for equal axis
    max_value = 100
    # Pivot the data to create 'series1' and 'series2' columns
    world_bank = world_bank.pivot(index=['Country', 'Region', 'Year'],
                                  columns='Series', values='Value'
                                  ).reset_index()
    # Scatter plot with guide line
    scatter = alt.Chart(world_bank).mark_circle(size=60).encode(
        alt.X(series1, title=axis1, scale=alt.Scale(domain=[0, max_value])),
        alt.Y(series2, title=axis2, scale=alt.Scale(domain=[0, max_value])),
        alt.Color('Region:N'),
        tooltip=['Country', 'Region', 'Year', series1, series2]
    )

    diagonal_line = alt.Chart(pd.DataFrame({'x': [0, max_value],
                                            'y': [0, max_value]})).mark_line(
        color='black',
        opacity=0.3
    ).encode(
        x='x:Q',
        y='y:Q'
    )

    final_plot = (scatter + diagonal_line
                  ).properties(title=f'{title}')

    return final_plot

# Double axis

def double_axis(series1, series2, plot_title):

    world_bank = world_bank_complete()

    # Filter and prepare the data
    world_bank = world_bank[(world_bank['Series'].isin([series1, series2])) &
                            (world_bank['Region'] != 'Aggregated data') &
                            (world_bank['Year'] > 1989)]
    world_bank = world_bank.dropna(subset=['Value'])
    world_bank = world_bank.groupby(['DECADE', 'Region', 'Series'],
                                    as_index=False)['Value'].mean()

    # Pivot data to have separate columns for series1 and series2
    world_bank_pivoted = world_bank.pivot(index=['Region', 'DECADE'],
                                          columns='Series',
                                          values='Value').reset_index()
    base = alt.Chart(world_bank_pivoted).encode(x='DECADE:O')
    title_bars = "At least completed upper secondary, population 25+, total (%)"
    bars = base.mark_bar().encode(y=alt.Y(series1,
                            title=title_bars),
                    xOffset="Region:N",
                    color="Region:N")

    line = base.mark_line(point=alt.OverlayMarkDef(filled=False, fill="white")
                          ).encode(y=alt.Y(series2, title=series2),
                                   color='Region:N')

    chart = alt.layer(bars, line).resolve_scale(y='independent'
                                                ).properties(title=plot_title)
    return chart

# Saving the plots

os.chdir('/Users/paulacadena/CAPP30239-SP/static-final/')

world_map('Population growth (annual %)').save('map.svg')
heat_map_series('Literacy rate, adult total (% of people ages 15 and above)'
                ).save('heat_hist.svg')
bars_twoyears('Net migration', 2023).save('bars.svg')
lines_subregion('Ratio of female to male labor force participation rate (%) (modeled ILO estimate)'
                ).save('lines.svg')
area_pop('Rural population', 'Urban population').save('area.svg')
scatter_plot('Wage and salaried workers, female (% of female employment) (modeled ILO estimate)',
             'Wage and salaried workers, male (% of male employment) (modeled ILO estimate)',
             'Wage and salaried workers by gender, modeled ILO estimate',
             '% Female', '% Male').save('scatter_wage.svg')
scatter_plot('Share of youth not in education, employment or training, female (% of female youth population) (modeled ILO estimate)',
             'Share of youth not in education, employment or training, male (% of male youth population)  (modeled ILO estimate)',
             'Youth not in education, employment or training by gender, modeled ILO estimate',
             '% Female', '% Male').save('scatter_youth.svg')
double_axis('Educational attainment, at least completed upper secondary, population 25+, total (%) (cumulative)',
            'GDP per capita, PPP (current international $)',
            'Comparison between Educational Attainment and GDP per capita by Decade and Region'
            ).save('double.svg')