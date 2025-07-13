
from shiny import reactive
from shiny.express import input, render, ui
import pandas as pd
import io

raw_data = reactive.Value(None)  #None value at the beginning
cleaned_data = reactive.Value(None) 

ui.page_opts(title = "Data Cleaner", fillable=True) 
with ui.layout_sidebar():
    with ui.sidebar(

        id = "sidebar",
        position="left",
        open= "open",):

        ui.input_file(
            id= "File_csv",
            label="Upload CSV file",
            accept= [".csv"],
            button_label='Browse...',
            placeholder='No file selected',
        ),  #is a list

        ui.input_action_button(
            id = "analyze_button",
            label = "Analyze"
        )
        ui.hr()
        ui.input_selectize(
            id = "columns_selector",
            label = "Remove columns",
            choices = [],
            multiple=True,
            options={"create": False}
        )
        ui.input_select(
            id = "handle_NaN_values",
            label= "With NaNs:",
            choices= ["No change","Replace with 0", "Replace with column mean","Replace with column median","Drop rows with missing values"],
            selected= "No change"
        )
        ui.input_selectize(
            id = "numeric_columns_selector",
            label = "Columns to transform",
            choices = [],
            multiple=True,
            options={"create": False}
        )
        ui.input_select(
            id = "transform",
            label= "Transform strategy:",
            choices= ["No change","Normalization", "Standardization"],
            selected= "No change"
        )
        ui.hr()
        ui.input_action_button(
            id = "clean_button",
            label = "Clean"
        )
        @render.download(label= " Download Cleaned Data", filename="cleaned_data.csv")
        def download_cleaned_data():
            data = cleaned_data.get()
            if data is not None:
                with io.BytesIO() as buf:
                    data.to_csv(buf, index = False)
                    yield buf.getvalue()
            else:
                yield "".encode("utf-8") # empty byte string

        ui.input_action_button(
            id = "reset_button",
            label = "Reset"
        )
        ui.input_dark_mode()
    with ui.navset_pill(id="selected_navset_pill"):
        with ui.nav_panel("Data"):
            @render.data_frame
            def display_table():
                data = cleaned_data.get()
                if data is None:
                    return pd.DataFrame()
                return data

        with ui.nav_panel("Analysis"):
            @render.data_frame
            @reactive.event(input.analyze_button)
            def display_analysis():
                data = cleaned_data.get()
                if data is None:
                    return pd.DataFrame()
                analyzed = pd.DataFrame({
                        "Column": data.columns,
                        "Missing values": data.isna().sum(),
                        "Data type": data.dtypes,
                        "Nr. of unique values": data.nunique(),
                    })
                analyzed = analyzed.sort_values(by = 'Missing values',ascending=False)
                return analyzed
                
                  
#on file change
@reactive.effect            # set to reactive
@reactive.event(input.File_csv)       #update only on file input
def load_csv_file():
    try:
        raw_data.set(pd.read_csv(input.File_csv()[0]["datapath"]) )  #set path to data path variable, use first file in the list
        choices = raw_data.get().columns.values.tolist()
        choices_numeric = raw_data.get().select_dtypes(include='number').columns.values.tolist()
        ui.update_selectize("columns_selector", choices=choices)
        ui.update_selectize("numeric_columns_selector",choices=choices_numeric)
        ui.update_select("handle_NaN_values", selected="No change")
        ui.update_select("transform", selected="No change")
        cleaned_data.set(raw_data.get())
    except Exception as exception:
        ui.notification_show(f"Error loading file: {exception}",duration=5, type= 'error' )


# on clean 
@reactive.effect 
@reactive.event(input.clean_button)
def clean():
    data = raw_data.get()
    if data is None:
        return pd.DataFrame
    # dropping columns
    excluded_columns = input.columns_selector()
    data = data[[col for col in data.columns if col not in excluded_columns]]   #exclude removed columns
    # choose numeric columns
    data_numeric = data.select_dtypes(include='number')
    # missing values
    way = input.handle_NaN_values.get()
    match way:
        case "Replace with 0":
            data = data.fillna(0)
        case "Replace with column mean":
            mean = data_numeric.mean()
            data = data.fillna(mean)
        case "Replace with column median":
            median = data_numeric.median()
            data = data.fillna(median)
        case "Drop rows with missing values":
            data = data.dropna()
        case "No change":
            data = data
    #choose columns to transform
    transform_columns = input.numeric_columns_selector()
    data_transform = data[[col for col in data.columns if col in transform_columns]]
    # transform
    way = input.transform.get()
    if way == "No change":
        data = data
    elif way == "Normalization":
        data[data_transform.columns] = (data_transform - data_transform.min())/(data_transform.max()- data_transform.min())
    elif way =="Standardization":
        data[data_transform.columns] = (data_transform - data_transform.mean())/ data_transform.std()
    cleaned_data.set(data)


@reactive.effect 
@reactive.event(input.reset_button)
def reset():
    data = raw_data.get()
    if data is None:
        ui.update_select("handle_NaN_values", selected="No change")
        ui.update_select("transform", selected="No change")
        return pd.DataFrame
    cleaned_data.set(data)
    choices = data.columns.values.tolist()
    choices_numeric = data.select_dtypes(include='number').columns.values.tolist()
    ui.update_selectize("columns_selector",choices=choices)
    ui.update_selectize("numeric_columns_selector",choices=choices_numeric)
    ui.update_select("handle_NaN_values", selected="No change")
    ui.update_select("transform", selected="No change")


