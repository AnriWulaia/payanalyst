# PayAnalyst

Payment transaction analysis tool. Upload a CSV, get an AI-generated analyst report as a PDF.

**Live:** https://payanalyst-production.up.railway.app

---

## What it does

- Upload a payments CSV → get charts + downloadable PDF report
- PDF includes key metrics, failure breakdown, risk flags, and AI recommendations

---

## Stack

- **Backend:** Python, FastAPI
- **Analysis:** Pandas
- **AI:** Nemotron 3 Super via OpenRouter
- **PDF:** ReportLab
- **Frontend:** HTML, CSS, JavaScript, Chart.js
- **Hosting:** Railway

---

## CSV format

Required columns: `merchant`, `amount`, `status`
Optional column: `reason`

---

## Run locally

```bash
git clone git@github.com:AnriWulaia/payanalyst.git
cd payanalyst
pip install -r requirements.txt
```

Create a `.env` file:
```
OPENROUTER_API_KEY=your-key-here
```

Start the server:
```bash
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`

---

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Frontend |
| POST | `/analyze` | Upload CSV → returns PDF report (10/hour) |
| POST | `/stats` | Upload CSV → returns JSON stats (20/hour) |

---