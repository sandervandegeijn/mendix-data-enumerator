# mendix-data-enumerator
This tool makes it possible to view exposed data in Mendix applications

## Standlone usage
```
python3 -m venv .
source bin/activate
pip install -r requirements.txt
pip install playwright && playwright install-deps && playwright install chromium
streamlit run webversion.py
```

## Docker usage
```
docker build . -t mendix-data-enumerator
docker run -p 8501:8501 mendix-data-enumerator
```

Go to http://localhost:8501/ to view the application
Enter an URL to a Mendix application and click on "Get data" to get all exposed data.