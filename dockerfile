# Start med et Python-bilde
FROM python:3.10-slim

# Sett arbeidskatalogen til /app
WORKDIR /app

# Kopier requirements.txt inn i containeren
COPY requirements.txt .

# Installer nødvendige avhengigheter
RUN pip install --no-cache-dir -r requirements.txt

# Kopier resten av applikasjonen inn i containeren
COPY . .

# Exponer porten som Streamlit kjører på
EXPOSE 8501

# Kjør Streamlit-applikasjonen
CMD ["streamlit", "run", "app.py", "--server.fileWatcherType=none"]
#CMD ["streamlit", "run", "export.py", "--server.fileWatcherType=none"]
#CMD ["streamlit", "run", "utetemp.py", "--server.fileWatcherType=none"]

