import pandas as pd

def analyze(df: pd.DataFrame) -> dict:
    df.columns = [c.strip().lower() for c in df.columns]

    total = len(df)
    failed_df = df[df["status"].str.lower() == "failed"]
    success = total - len(failed_df)
    success_rate = round((success / total) * 100, 1) if total else 0
    total_volume = round(df["amount"].sum(), 2)
    avg_amount = round(df["amount"].mean(), 2)

    by_merchant = (
        df.groupby("merchant")["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .round(2)
        .to_dict()
    )

    failure_by_merchant = (
        failed_df.groupby("merchant")
        .size()
        .sort_values(ascending=False)
        .head(5)
        .to_dict()
    )

    # Failure reasons
    failure_reasons = {}
    if "reason" in df.columns:
        failure_reasons = (
            failed_df[failed_df["reason"].notna()]
            .groupby("reason")
            .size()
            .sort_values(ascending=False)
            .to_dict()
        )

    # Failure reason per merchant
    failure_reason_by_merchant = {}
    if "reason" in df.columns:
        for merchant, group in failed_df.groupby("merchant"):
            top_reason = group["reason"].value_counts().idxmax() if not group["reason"].isna().all() else "unknown"
            failure_reason_by_merchant[merchant] = top_reason

    high_value_rows = df[df["amount"] > 10000].copy()
    if "reason" in df.columns:
        high_value_rows["reason"] = high_value_rows["reason"].fillna("—")
    high_value = high_value_rows[["merchant", "amount", "status", "reason"] if "reason" in df.columns else ["merchant", "amount", "status"]].to_dict(orient="records")

    return {
        "total_transactions": int(total),
        "successful": int(success),
        "failed": int(len(failed_df)),
        "success_rate": float(success_rate),
        "total_volume": float(total_volume),
        "average_amount": float(avg_amount) if not pd.isna(avg_amount) else 0.0,
        "top_merchants_by_volume": {k: float(v) for k, v in by_merchant.items()},
        "top_failing_merchants": {k: int(v) for k, v in failure_by_merchant.items()},
        "failure_reasons": {k: int(v) for k, v in failure_reasons.items()},
        "failure_reason_by_merchant": failure_reason_by_merchant,
        "high_value_transactions": high_value[:10],
    }