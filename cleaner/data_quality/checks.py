import pandas as pd
import logging
from ..ai_checks.llm import invalid_categorical_values
def uniqueness_check(df, columns, id_column, total_fields, excluded_category_columns=None):
    """
    Check for duplicate values across given columns.

    Args:
        df (pd.DataFrame): Input dataframe.
        columns (list): List of columns to check.
        id_column (str): Identifier column (used to return duplicate row IDs).
        total_fields (int): Total number of fields to calculate uniqueness score.
        excluded_category_columns (list): Columns to exclude from uniqueness check.

    Returns:
        results_df (pd.DataFrame): Detailed duplicate findings.
        uniqueness_score (float): Score between 0-100.
        total_duplicates (int): Number of duplicate entries found.
    """
    try:
        logging.info("Starting uniqueness_check")

        if not columns or columns == "error":
            logging.warning("Invalid or empty columns list provided.")
            return pd.DataFrame([]), 100, 0

        if excluded_category_columns and excluded_category_columns != "error":
            columns = [col for col in columns if col not in excluded_category_columns]

        use_index_as_id = id_column not in df.columns
        total_duplicates = 0
        results = []

        for column in columns:
            if column not in df.columns:
                logging.warning(f"Column '{column}' not found in DataFrame. Skipping.")
                continue

            duplicate_mask = df[column].duplicated(keep=False)
            duplicate_df = df[duplicate_mask]

            total_duplicates += duplicate_mask.sum()

            if not duplicate_df.empty:
                duplicate_counts = duplicate_df[column].value_counts()

                for value, count in duplicate_counts.items():
                    id_values = "; ".join(
                        map(
                            str,
                            duplicate_df.loc[duplicate_df[column] == value, id_column]
                            if not use_index_as_id else duplicate_df.index
                        )
                    )
                    results.append({
                        "Column Name": column,
                        "Findings": f"{value}: {count} duplicates",
                        "ID": id_values
                    })

        results_df = pd.DataFrame(results)

        if total_fields == 0:
            uniqueness_score = 100
        else:
            uniqueness_score = max(0, 100 * ((total_fields - total_duplicates) / total_fields))

        logging.info(f"Uniqueness check completed. Score: {uniqueness_score:.2f}")
        return results_df, round(uniqueness_score, 2), total_duplicates

    except Exception as e:
        logging.exception("An error occurred in uniqueness_check")
        return pd.DataFrame([]), 100, 0

def completeness_check(input_df, total_fields):
    """
    Computes completeness score and total missing values.

    Args:
        input_df (pd.DataFrame): Input dataset.
        id_column (str): Unique identifier column (not used directly here).
        total_fields (int): Total number of fields in the dataset.

    Returns:
        completeness_score (float): Data completeness score (0–100).
        total_issues (int): Number of missing values detected.
    """
    try:
        print("completeness_check")

        # Replace blank or whitespace-only strings with NaN
        df = input_df.replace(r'^\s*$', pd.NA, regex=True)

        # Count missing values across all columns
        total_issues = df.isna().sum().sum()

        # Compute completeness score
        completeness_score = 100 if total_fields == 0 else max(
            0, (total_fields - total_issues) / total_fields * 100
        )

        logging.info(f"Completeness check completed. Score: {completeness_score:.2f}%, Issues: {total_issues}")

        return round(completeness_score, 2), int(total_issues)

    except Exception as e:
        logging.exception("An error occurred in completeness_check")
        return 100.0, 0

def check_categorical_validity_ai(df, categorical_columns, id_column, total_fields):
    """
    Checks categorical validity using AI and calculates a validity score.

    Parameters:
        df (pd.DataFrame): The DataFrame to validate.
        categorical_columns (list): Categorical columns to check.
        id_column (str): The name of the ID column.

    Returns:
        - DataFrame with each invalid value, its ID, field, error, and explanation.
        - Validity score (0-100).
        - Invalid-to-total ratio.
    """
    try:
        print("check_categorical_validity_ai")
        if categorical_columns == "error" or not categorical_columns:
            return pd.DataFrame([]), 100, 0

        total_checked = 0  # Total checked values (excluding NaN)
        total_invalid = 0  # Total invalid values found
        errors = []

        for column in categorical_columns:
            if column in df.columns:
                invalid_values = invalid_categorical_values(df, column)  # Get invalid values (list)

                if not invalid_values:
                    continue  # Skip if no invalid values

                # Find rows where the column contains invalid values
                invalid_rows = df[df[column].isin(invalid_values)]

                for _, row in invalid_rows.iterrows():
                    error_entry = {
                        "ID": row[id_column] if id_column in df.columns else row.name,
                        # Use index if ID column is missing
                        "Field": column,
                        "Invalid Value": row[column],
                        "Error": "Invalid categorical value",
                        "Explanation": f"'{row[column]}' is not among the predefined valid categories, which may impact data consistency."
                    }

                    errors.append(error_entry)

                total_invalid += len(invalid_rows)
        # Convert results to DataFrame
        errors_df = pd.DataFrame(errors)

        # Compute validity score
        if total_checked == 0:
            score = 100  # No categorical values to check
        else:
            score = max(0, (total_fields - total_invalid) / total_fields * 100)
        return errors_df, round(score, 2), total_invalid

    except Exception as e:
        logging.exception("An error occurred in check_categorical_validity_ai")
        return pd.DataFrame([]), 100, 0