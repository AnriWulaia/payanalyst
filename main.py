from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import pandas as pd
import io
import os
from openai import OpenAI
from analyst import analyze
from report import generate_pdf
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["payanalyst-production.up.railway.app"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
    base_url="https://openrouter.ai/api/v1"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    return FileResponse("static/index.html")

def parse_csv(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(file_bytes))
    df.columns = [c.strip().lower() for c in df.columns]
    required = {"merchant", "amount", "status"}
    if not required.issubset(set(df.columns)):
        raise HTTPException(status_code=400, detail=f"CSV must have columns: merchant, amount, status")
    return df

@app.post("/stats")
async def stats_only(file: UploadFile = File(...)):
    contents = await file.read()
    df = parse_csv(contents)
    return analyze(df)

@app.post("/analyze")
async def analyze_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    contents = await file.read()
    df = parse_csv(contents)
    stats = analyze(df)

    failure_reason_summary = ""
    if stats["failure_reasons"]:
        lines = [f"{r}: {c} cases" for r, c in stats["failure_reasons"].items()]
        failure_reason_summary = "\n".join(lines)
    else:
        failure_reason_summary = "No failure reason data available"

    merchant_reason_summary = ""
    if stats["failure_reason_by_merchant"]:
        lines = [f"{m}: {r}" for m, r in stats["failure_reason_by_merchant"].items()]
        merchant_reason_summary = "\n".join(lines)

    prompt = f"""
You are a senior payments analyst. Analyze this transaction data and write a structured report.
Use only plain ASCII characters. Use - instead of dashes, if you need to use words with dashes use - it is important.

Data summary:
- Total transactions: {stats['total_transactions']}
- Successful: {stats['successful']}
- Failed: {stats['failed']}
- Success rate: {stats['success_rate']}%
- Total volume: ${stats['total_volume']:,}
- Average transaction: ${stats['average_amount']:,}
- Top merchants by volume: {stats['top_merchants_by_volume']}
- Top failing merchants: {stats['top_failing_merchants']}
- Failure reasons breakdown: {failure_reason_summary}
- Top failure reason per merchant: {merchant_reason_summary}
- High value transactions (>$10,000): {len(stats['high_value_transactions'])} found

Write the report in these exact sections:
**Executive Summary**
**Key Observations**
**Failure Analysis**
**Risk Flags**
**Recommendation**

Be specific, reference the actual failure reasons and merchants by name. No filler sentences.
"""

    response = client.chat.completions.create(
        model="nvidia/nemotron-3-super-120b-a12b:free",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=900
    )

    ai_report = response.choices[0].message.content
    #remove nonascii characters 
    import re
    ai_report = re.sub(r'[^\x00-\x7F]+', '-', ai_report)
    pdf_bytes = generate_pdf(stats, ai_report)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=payment_report.pdf"}
    )