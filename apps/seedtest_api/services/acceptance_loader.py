from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Dict, Optional

from apps.seedtest_api.settings import settings


def _load_from_json(path: str) -> Dict:
    with open(path, "r") as f:
        data = json.load(f)
    # normalize: string/int keys to int when possible, values to float
    out = {}
    for k, v in (data or {}).items():
        try:
            kk = int(k)
        except Exception:
            kk = k
        try:
            out[kk] = float(v)
        except Exception:
            continue
    return out


def _load_from_csv(path: str) -> Dict:
    out = {}
    import csv

    with open(path, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            # expect: item_id, p (header optional)
            try:
                iid = int(row[0]) if row[0] and row[0].strip() else None
                p = float(row[1])
            except Exception:
                # skip header or malformed lines
                continue
            if iid is not None:
                out[iid] = p
    return out


def _load_from_s3(uri: str) -> Optional[Dict]:
    # s3://bucket/key[.json|.csv|.tsv]
    try:
        import boto3  # type: ignore
    except Exception:
        return None
    if not uri.startswith("s3://"):
        return None
    without = uri[5:]
    parts = without.split("/", 1)
    if len(parts) != 2:
        return None
    bucket, key = parts
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=bucket, Key=key)
    body = obj["Body"].read()
    # Write to a temp file-like pathless buffer; detect by extension
    lower = key.lower()
    import tempfile

    with tempfile.NamedTemporaryFile(delete=True) as tmp:
        tmp.write(body)
        tmp.flush()
        if lower.endswith(".json"):
            return _load_from_json(tmp.name)
        if lower.endswith(".csv") or lower.endswith(".tsv"):
            return _load_from_csv(tmp.name)
        # default to json
        return _load_from_json(tmp.name)


def _load_from_db(directive: str) -> Optional[Dict]:
    # directive example: db:table=item_acceptance,item=item_id,p=p
    # Uses settings.DATABASE_URL
    dsn = settings.DATABASE_URL
    if not dsn:
        return None
    try:
        import psycopg2  # type: ignore
    except Exception:
        return None
    # parse params
    table = "acceptance_probs"
    item_col = "item_id"
    p_col = "p"
    bank_col = None
    bank_id = None
    active_col = None
    active_val = None
    if directive.startswith("db:"):
        payload = directive[3:]
        for part in payload.split(","):
            if not part or "=" not in part:
                continue
            k, v = part.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k == "table":
                table = v
            elif k == "item":
                item_col = v
            elif k == "p":
                p_col = v
            elif k == "bank_col":
                bank_col = v
            elif k == "bank_id":
                try:
                    bank_id = int(v)
                except Exception:
                    bank_id = None
            elif k == "active_col":
                active_col = v
            elif k == "active_val":
                active_val = v

    sql = f"SELECT {item_col}, {p_col} FROM {table}"
    where = []
    params = []
    if bank_col and bank_id is not None:
        where.append(f"{bank_col} = %s")
        params.append(bank_id)
    if active_col and active_val is not None:
        # attempt type conversion for booleans and numerics
        val: object = active_val
        vl = str(active_val).strip().lower()
        if vl in ("true", "false"):
            val = (vl == "true")
        else:
            try:
                val = int(active_val)
            except Exception:
                try:
                    val = float(active_val)
                except Exception:
                    val = active_val
        where.append(f"{active_col} = %s")
        params.append(val)
    if where:
        sql += " WHERE " + " AND ".join(where)
    out: Dict = {}
    try:
        conn = psycopg2.connect(dsn)
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params or None)
                for row in cur.fetchall():
                    try:
                        iid = int(row[0])
                        p = float(row[1])
                    except Exception:
                        continue
                    out[iid] = p
        finally:
            conn.close()
    except Exception:
        return None
    return out or None


@lru_cache(maxsize=1)
def load_acceptance_probs(source: Optional[str]) -> Optional[Dict]:
    if not source:
        return None
    # S3
    if source.startswith("s3://"):
        return _load_from_s3(source)
    # DB shorthand
    if source.startswith("db:"):
        return _load_from_db(source)
    # Postgres URL directly
    if source.startswith("postgres://") or source.startswith("postgresql://"):
        # assume default table and columns
        # override DATABASE_URL temporarily
        prev = settings.DATABASE_URL
        try:
            settings.DATABASE_URL = source  # type: ignore
            return _load_from_db("db:table=acceptance_probs,item=item_id,p=p")
        finally:
            settings.DATABASE_URL = prev  # type: ignore
    path = os.path.expanduser(source)
    if not os.path.exists(path):
        return None
    lower = path.lower()
    try:
        if lower.endswith(".json"):
            return _load_from_json(path)
        if lower.endswith(".csv") or lower.endswith(".tsv"):
            return _load_from_csv(path)
        # default: try json first
        return _load_from_json(path)
    except Exception:
        return None
