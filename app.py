# imports
import streamlit as st
import pandas as pd
import numpy as np



# Define some custom functions
def read_file(data_file):
    if data_file.type == "text/csv":
        df = pd.read_csv(data_file)
    elif data_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        df = pd.read_excel(data_file, sheet_name=0)
    return (df)



def jumptwice():
    st.write("##")
    st.write("##")


def columnize( itemlist ):
    NEWLINE_DASH = ' \n- '
    if len(itemlist) > 1:
        return f"- {itemlist[0]}{NEWLINE_DASH.join(itemlist[1:])}"
    else:
        return f"- {itemlist[0]}"

def validate_table(table: pd.DataFrame, table_name: str, CDE: pd.DataFrame):

    retval = 1

    # Filter out rows specific to the given table_name from the CDE
    specific_cde_df = CDE[CDE['Table'] == table_name]
    
    # Extract fields that have a data type of "Enum" and retrieve their validation entries
    enum_fields_dict = dict(zip(specific_cde_df[specific_cde_df['DataType'] == "Enum"]['Field'], 
                               specific_cde_df[specific_cde_df['DataType'] == "Enum"]['Validation']))
    
    # Extract fields that are marked as "Required"
    required_fields = specific_cde_df[specific_cde_df['Required'] == "Required"]['Field'].tolist()
    optional_fields = specific_cde_df[specific_cde_df['Required'] == "Optional"]['Field'].tolist()

    table = force_enum_string(table, table_name, CDE)

    # Check for missing "Required" fields
    missing_required_fields = [field for field in required_fields if field not in table.columns]
    
    if missing_required_fields:
        st.error(f"Missing Required Fields in {table_name}: {', '.join(missing_required_fields)}")
    else:
        st.markdown(f"All required fields are present in *{table_name}* table.")

    jumptwice()
    # Check for empty or NaN values
    empty_fields = []
    total_rows = table.shape[0]
    for test_field,test_name in zip([required_fields, optional_fields], ["Required", "Optional"]):
        empty_or_nan_fields = {}
        for field in test_field:
            if field in table.columns:
                invalid_count = table[field].isna().sum()
                if invalid_count > 0:
                    empty_or_nan_fields[field] = invalid_count
                    
        if empty_or_nan_fields:
            st.error(f"{test_name} Fields with Empty (nan) values:")
            # st.write(empty_or_nan_fields)
            for field, count in empty_or_nan_fields.items():
                st.markdown(f"- {field}: {count}/{total_rows} empty rows")
            retval = 0
        else:
            st.markdown(f"No empty entries (Nan) found in _{test_name}_ fields.")
    
    # Check for invalid Enum field values
    invalid_field_values = {}
    valid_field_values = {}

    invalid_fields = []
    invalid_nan_fields = []
    for field, validation_str in enum_fields_dict.items():
        valid_values = eval(validation_str)
        if field in table.columns:
            invalid_values = table[~table[field].isin(valid_values)][field].unique()
            if invalid_values.any():

                if 'Nan' in invalid_values:
                    invalid_nan_fields.append(field)
        
                invalids = [x for x in invalid_values if x != 'Nan' ]
                if len(invalids)>0:
                    invalid_fields.append(field)    
                    invalid_field_values[field] = invalids
                    valid_field_values[field] = valid_values
                


    jumptwice()
    if invalid_field_values:
        st.subheader("Enums")
        st.error("Invalid entries")
        # tmp = {key:value for key,value in invalid_field_values.items() if key not in invalid_nan_fields}
        # st.write(tmp)

        for field, values in invalid_field_values.items():
            if field in invalid_fields:
                st.markdown(f"- {field}:{', '.join(map(str, values))}")
                st.markdown(f"> change to: {', '.join(map(str, valid_field_values[field]))}")

        if len(invalid_nan_fields) > 0:
            st.error("Found unexpected NULL (nan):")
            st.markdown(columnize(invalid_nan_fields))

        
        retval = 0
        # if len(invalid_fields) > 0:
        #     st.text('First 10 entries invalid entries')
        #     st.write(table[invalid_fields].head(10))
        # if len(invalid_nan_fields) > 0:
        #     st.markdown('First 10 entries invalid _empty_ entries')
        #     st.write(table[invalid_nan_fields].head(10))

    else:
        st.text(f"All Enum fields have valid values in {table_name}. 🥳")

    return retval

######## HELPERS ########
# Define a function to only capitalize the first letter of a string
def capitalize_first_letter(s):
    if not isinstance(s, str) or len(s) == 0:  # Check if the value is a string and non-empty
        return s
    return s[0].upper() + s[1:]

def force_enum_string(df, df_name, CDE):

    string_enum_fields = CDE[(CDE["Table"] == df_name) & 
                                (CDE["DataType"].isin(["Enum", "String"]))]["Field"].tolist()
    # Convert the specified columns to string data type using astype() without a loop
    columns_to_convert = {col: 'str' for col in string_enum_fields if col in df.columns}
    df = df.astype(columns_to_convert)

    # enum_fields = CDE[ (CDE["Table"] == df_name) & 
    #                             (CDE["DataType"]=="Enum") ]["Field"].tolist()
    
    for col in string_enum_fields:
        if col in df.columns and col not in ["assay", "file_type"]:
            df[col] = df[col].apply(capitalize_first_letter)

    return df




# Provide template
st.markdown('<p class="big-font"> ASAP single cell data fields self-QC </p>', unsafe_allow_html=True)
st.markdown('<p class="medium-font"> This app is intended to make sure ASAP contributing with single cell data provide standard ASAP required fields </p>', unsafe_allow_html=True)
st.markdown('<p class="medium-font"> Download the template from the link below. Once you open the link, go to "File"> "Download" > "xlsx" or "csv" format </p>', unsafe_allow_html=True)
st.markdown('[Access the data dictionary and template](https://docs.google.com/spreadsheets/d/1xjxLftAyD0B8mPuOKUp5cKMKjkcsrp_zr9yuVULBLG8/edit?usp=sharing)', unsafe_allow_html=True)



# Read file from streamlit and create a copy to do the maps
data_file = st.sidebar.file_uploader("Upload Your meta-tables (SAMPLE.csv, STUDY.csv, PROTOCOL.csv, CLINPATH.csv, and/or SUBJECT.csv)", type=['xlsx', 'csv'],accept_multiple_files=True)

if data_file is None or len(data_file)==0: 
    st.stop()
elif len(data_file)>1:
    table = [dat_f.name.split('.')[0] for dat_f in data_file]
    data = [ read_file(dat_f) for dat_f in data_file]
else:
    table = data_file.name.split('.')[0] 
    data = read_file(data_file)


datamaps_copy = [dat.copy() for dat in data]
# Construct the path to CSD.csv
cde_file_path = "ASAP_CDE.csv"
CDE_df = pd.read_csv(cde_file_path)

for table_name,dat in zip(table,data):

    st.header(f"{table_name} ({table_name}.csv)")
    # data_file = "https://docs.google.com/spreadsheets/d/1xjxLftAyD0B8mPuOKUp5cKMKjkcsrp_zr9yuVULBLG8/edit?usp=sharing"
    # Load the CDE.csv file and the reference table

    retval = validate_table(dat, table_name, CDE_df)
    if retval == 0:
        st.error(f"{table_name} FAILED ! \n Please try again 😃")

    st.divider()


# Check all columns are present in the input 
# We can do something such as checking the number of columns matches what we would expect ( a bit unsafe tho)
# Otherwise, create a list with all col names



# # Check all required columns are not missing
# required_cols = [col for col in data.columns if col not in optional_cols]

# data_non_miss_check = data[required_cols].copy()

# if data_non_miss_check.isna().sum().sum()>0:
#     st.error('There are some missing entries in the required columns. Please fill the missing cells ')
#     st.text('First 30 entries with missing data in any required fields')
#     st.write(data_non_miss_check[data_non_miss_check.isna().sum(1)>0].head(30))
#     st.stop()
# else:
#     st.text('Check missing data in the required fields --> OK')



# Perform numeric variables specific checks (ie, are thay on a sensible range or we can detect errors?)



# # Example on how to map users code to our standard codes
# # If we use this approach I would like to avoid code repetition and try to wrap this on a function and a for loop 
# # I do not want to have this same thing 100 times
# # Also, let's think if we can come up with something cooler to do this, something that looks nicer

# # sex for qc
# st.subheader('Create "biological_sex_for_qc"')
# st.text('Count per sex group')
# st.write(data.sex.value_counts())

# sexes=data.sex.dropna().unique()
# n_sexes = st.columns(len(sexes))
# mapdic={}
# for i, x in enumerate(n_sexes):
#     with x:
#         sex = sexes[i]
#         mapdic[sex]=x.selectbox(f"[{sex}]: For QC, please pick a word below",
#                             ["Male", "Female","Intersex","Unnown"], key=i)
# data['sex_qc'] = data.sex.replace(mapdic)

# # cross-tabulation
# st.text('=== sex_qc x sex ===')
# xtab = data.pivot_table(index='sex_qc', columns='sex', margins=True,
#                         values='sample_id', aggfunc='count', fill_value=0)
# st.write(xtab)

# sex_conf = st.checkbox('Confirm sex_qc?')
# if sex_conf:
#     st.info('Thank you')


