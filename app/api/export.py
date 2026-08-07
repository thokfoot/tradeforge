from __future__ import annotations

import io

from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException
from fastapi.responses import StreamingResponse

from app.api import deps

router = APIRouter(prefix="/api/export")


@router.get("/csv")
def export_csv(
    market: str = Query(...),
    symbol: str = Query(...),
    interval: str = Query("1d"),
) -> StreamingResponse:
    df = deps.parquet_store().read(market, interval, symbol)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"no data for {symbol}")
    buffer = io.StringIO()
    df.to_csv(buffer)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{symbol}_{interval}.csv"'
        },
    )
