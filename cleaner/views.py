from django.shortcuts import render, redirect
import pandas as pd
from .data_quality.checks import uniqueness_check
from .data_quality.checks import completeness_check
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

    # Run completeness check
    completeness_score, completeness_issues = completeness_check(
        df, id_column="Observation ID", total_fields=total_fields
    )

    checks = [
        {
            "name": "Completeness",
            "description": "Missing values and null checks",
            "status": "passed" if completeness_score > 90 else "warning" if completeness_score > 70 else "failed",
            "score": completeness_score,
            "issues": completeness_issues,
            "last_checked": "just now",
        },
        # other checks will be added later…
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