from django.shortcuts import render, redirect
import pandas as pd

# Global variable to store CSV info (for MVP purposes)
CSV_INFO = {}

def home(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get("csv_file")
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                global CSV_INFO
                CSV_INFO = {
                    "filename": uploaded_file.name,
                    "rows": len(df),
                    "columns": df.columns.tolist()
                }
                return redirect('dashboard')
            except Exception as e:
                return render(request, 'home.html', {'error': str(e)})
    return render(request, 'home.html')

def dashboard(request):
    if not CSV_INFO:
        return redirect('home')
    return render(request, 'dashboard.html', {'file_info': CSV_INFO})
