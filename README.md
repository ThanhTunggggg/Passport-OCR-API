# Passport OCR API
 
## Running Locally


```bash
pip install -r requirements.txt
```

```bash
python manage.py migrate
```

```bash
python manage.py runserver
```

```bash
curl -X POST "http://localhost:8000/api/ocr/" -F "image=@AC.jpg";echo""
```