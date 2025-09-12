import google.generativeai as genai
from dotenv import load_dotenv
import os
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
        prompt = f"""return only the categorical column names from the provided list of column names.  
        
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
                return categorical_cols
        except Exception:
            pass

        # fallback → return empty list if parsing failed
        return []

    except Exception as e:
        print(f"AI error: {e}")
        return []

print(categorical_columns('["name","gender","age"]'))