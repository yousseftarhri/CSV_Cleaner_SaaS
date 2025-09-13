import google.generativeai as genai
from dotenv import load_dotenv
import os
import logging
import ast
import pandas as pd
# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Specify the model to use (e.g., "gemini-2.5-flash")
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

def generate_ai(input):
    response = model.generate_content(
        input,
        generation_config=genai.types.GenerationConfig(
            temperature=0.6
        )
    )
    return response.text


def categorical_columns(columns):
    """
    Ask an LLM to classify which columns are categorical.

    Args:
        columns (list): List of column names.

    Returns:
        list: Columns considered categorical.
    """
    try:
        prompt = f"""Identify and return only list of the categorical column names from the provided list of column names.  
        Categorical columns typically contain a limited set of distinct values, such as categories or labels  
        (e.g., 'Gender', 'Country', 'Marital Status' etc.).  
        Do not consider descriptive fields like 'Full Name', 'Street Address', 'City', or similar as categorical.

        ### Instructions:
        - Return the categorical column names as a list.  
        - Do not include any extra information or explanations.  
        - If no categorical columns are found, return the string `'not found'` (without a list).

        Example:  
        Column names: ['Age', 'Gender', 'Country', 'Income']  
        Categorical columns: ['Gender', 'Country']

        Column names: {columns}
        Categorical columns:"""



        # Parse LLM output safely
        text_output= generate_ai(prompt)

        # Try to evaluate as Python list
        try:
            print(text_output)
            categorical_cols = eval(text_output)
            if isinstance(categorical_cols, list):
                print(categorical_cols)
                return categorical_cols
        except Exception:
            pass

        # fallback → return empty list if parsing failed
        return []

    except Exception as e:
        print(f"AI error: {e}")
        return []

def invalid_categorical_values(df, column_name):
    try:
        prompt = f"""You are a data validation expert. I will provide you with a list of unique values from a categorical column in a dataset. Your task is to analyze the values and determine which ones are likely outliers or invalid based on common patterns and domain knowledge.
        Return only the values that are likely invalid in a list format, if you do not find any invalid values, return empty list. Do not provide explanations, context, or any extra details—just a plain list.
        Step 1: Identify common values that logically belong in the column.
        Step 2: Detect values that do not fit the expected pattern or meaning.
        Step 3: Return a list of invalid values.
        Example: 
        user question: my column name: "Gender". unique values from my categorical column: ['F', 'M', 'Female', 'Male', nan, 'said']
        AI: "['F', 'M', 'nan', 'said']"

        user question: my column name: {column_name}. unique values from my categorical column: {list(df[column_name].unique())}
        AI:"""
        list_llm = generate_ai(prompt)
        list_llm = ast.literal_eval(list_llm)

        return list_llm

    except Exception as e:
        logging.exception("An error occurred")
        return f"error"
df = pd.read_excel("new_test_data.xlsx")

c=categorical_columns(df.columns)
print(invalid_categorical_values(df,c[-1]))