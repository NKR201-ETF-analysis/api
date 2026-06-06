import pandas as pd

from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection

from api.config import (
    MYSQL_ACCOUNT,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
)

# 建立 Engine
DATABASE_URL = (
    f"mysql+pymysql://"
    f"{MYSQL_ACCOUNT}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}"
    f"/mydb"
)

engine: Engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

app = FastAPI()

# 建立 Dependency
def get_db():
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()

# ROOT API
@app.get("/")
def read_root():
    return {"Hello": "World"}

# etf_top20

@app.get("/etf_top20")
def etf_top20(
    stock_id: str = "",
    start_date: str = "",
    end_date: str = "",
    db: Connection = Depends(get_db),
):
    sql = text("""
        SELECT *
        FROM EtfTop20BuyInstitutionalV2
        WHERE stock_id = :stock_id
          AND date >= :start_date
          AND date <= :end_date
    """)

    data_df = pd.read_sql(
        sql,
        con=db,
        params={
            "stock_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    )

    return {
        "data": data_df.to_dict("records")
    }

@app.get("/etf/latest-top20")
def get_latest_top20(
    db: Connection = Depends(get_db),
):
    sql = text("""
        SELECT
            rank_num,
            stock_id,
            stock_name,
            open_price,
            close_price,
            trading_volume_shares,
            trading_value,
            five_day_trend_pct
        FROM EtfTop20BuyInstitutionalV2
        WHERE date = (
            SELECT MAX(date)
            FROM EtfTop20BuyInstitutionalV2
        )
        ORDER BY rank_num
    """)

    df = pd.read_sql(sql, con=db)

    return {
        "data": df.to_dict("records")
    }

@app.get("/etf/top20-frequency")
def get_top20_frequency(
    days: int = 30,
    db: Connection = Depends(get_db),
):
    sql = text("""
        SELECT
            stock_id,
            stock_name,
            COUNT(*) AS days_in_top20,
            AVG(rank_num) AS avg_rank
        FROM EtfTop20BuyInstitutionalV2
        WHERE date >= DATE_SUB(CURDATE(), INTERVAL :days DAY)
        GROUP BY stock_id, stock_name
        ORDER BY days_in_top20 DESC, avg_rank ASC
        LIMIT 20
    """)

    df = pd.read_sql(
        sql,
        con=db,
        params={
            "days": days
        }
    )

    return {
        "data": df.to_dict("records")
    }