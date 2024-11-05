import altair as alt

def custom_theme():

    return {
        "config": {
            "title": {
                "fontSize": 16,           # Size of plot titles
                "font": "Helvetica",      # Font for titles
                "anchor": "start",        # Align title to the start
                "color": "#333333"        # Title color
            },
            "axis": {
                "labelFontSize": 12,      # Size of axis labels
                "titleFontSize": 14,      # Size of axis titles
                "labelFont": "Arial",     # Font for axis labels
                "titleFont": "Arial",     # Font for axis titles
                "labelColor": "#333333",  # Color for axis labels
                "titleColor": "#333333"   # Color for axis titles
            },
            "legend": {
                "labelFontSize": 10,      # Size of legend labels
                "titleFontSize": 12,      # Size of legend title
                "labelFont": "Arial",     # Font for legend labels
                "titleFont": "Arial"      # Font for legend title
            },
            "view": {
                "width": 600,             # Default chart width
                "height": 400             # Default chart height
            },
            "range": {
                "category": ["#742183", "#166417", "#f8c7cc", "#edae49",
                             "#81a684", "#113447", "#AACEBE", "#c6e2e9",
                             "#2c8c99", "#73eedc"],
                "diverging": {"scheme": "purplegreen"},
                "heatmap": {"scheme": "purplegreen"},
                "ordinal": ["#166417", "#742183"]
            }
        }


    }

alt.themes.register("custom_theme", custom_theme)
alt.themes.enable("custom_theme")
