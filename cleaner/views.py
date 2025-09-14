from django.shortcuts import render, redirect
import pandas as pd
from .data_quality.checks import uniqueness_check
from .data_quality.checks import completeness_check, check_categorical_validity_ai
from .ai_checks.llm import categorical_columns, identify_id_column_prompt
CSV_INFO = {}

def home(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get("csv_file")
        if uploaded_file:
            try:
                global df
                df = pd.read_csv(uploaded_file)

                # Run uniqueness check
                columns = df.columns.tolist()
                total_fields = df.size
                results_df, score, duplicates = uniqueness_check(
                    df,
                    columns=columns,
                    id_column=columns[0],  # assuming first column is ID
                    total_fields=total_fields,
                    excluded_category_columns=[]
                )

                global CSV_INFO
                CSV_INFO = {
                    "filename": uploaded_file.name,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "uniqueness_score": score,
                    "total_duplicates": duplicates,
                    "uniqueness_results": results_df.to_dict(orient="records"),
                }
                return redirect("dashboard")
            except Exception as e:
                return render(request, "home.html", {"error": str(e)})
    return render(request, "home.html")

def dashboard(request):
    if not CSV_INFO:
        return redirect("home")

    total_fields = df.shape[0] * df.shape[1]  # total cells
    columns = df.columns
    categorical_columns_ = categorical_columns(columns)
    id_column = identify_id_column_prompt(columns)
    # Run completeness check
    completeness_score, completeness_issues = completeness_check(
        df, total_fields=total_fields
    )

    error_df, categorical_validity_score, total_invalid = check_categorical_validity_ai(df, categorical_columns_, id_column, total_fields)

    checks = [
        {
            "name": "Completeness",
            "description": "Missing values and null checks",
            "status": "passed" if completeness_score > 90 else "warning" if completeness_score > 70 else "failed",
            "score": completeness_score,
            "issues": completeness_issues,
            "last_checked": "just now",
        },
        {
            "name": "Accuracy",
            "description": "Correctness and validity of data",
            "status": "warning",
            "score": 78,
            "issues": 3,
            "last_checked": "5 min ago",
        },
        {
            "name": "Consistency",
            "description": "Format and standard compliance",
            "status": "passed",
            "score": 91,
            "issues": 0,
            "last_checked": "1 min ago",
        },
        {
            "name": "Timeliness",
            "description": "Freshness and update frequency",
            "status": "failed",
            "score": 45,
            "issues": 12,
            "last_checked": "10 min ago",
        },
        {
            "name": "Uniqueness",
            "description": "Duplicate record detection",
            "status": "passed",
            "score": 98,
            "issues": 0,
            "last_checked": "3 min ago",
        },
        {
            "name": "Validity",
            "description": "Business rule compliance",
            "status": "warning",
            "score": categorical_validity_score,
            "issues": 5,
            "last_checked": "just now",
        },
        {
            "name": "Integrity",
            "description": "Referential integrity checks",
            "status": "passed",
            "score": 89,
            "issues": 1,
            "last_checked": "4 min ago",
        },
    ]

    overall_score = sum(c["score"] for c in checks) // len(checks)

    return render(request, "dashboard.html", {
        "file_info": CSV_INFO,
        "checks": checks,
        "overall_score": overall_score,
        "passed": len([c for c in checks if c["status"] == "passed"]),
        "warnings": len([c for c in checks if c["status"] == "warning"]),
        "failed": len([c for c in checks if c["status"] == "failed"]),
    })