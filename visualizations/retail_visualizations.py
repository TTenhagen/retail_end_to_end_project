import os, warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.patches as mpatches
import seaborn as sns

warnings.filterwarnings('ignore')

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Output folder ─────────────────────────────────────────────────────────────
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'RETAIL_charts')
os.makedirs(OUT, exist_ok=True)

# ── RETAIL palette ───────────────────────────────────────────────────────────
WMT_BLUE   = '#0070C0'
WMT_DARK   = '#002060'
WMT_GRAY   = '#595959'
WMT_LIGHT  = '#BDD7EE'
WMT_YELLOW = '#FFC000'
WMT_RED    = '#C00000'

TYPE_COLORS  = {'A': WMT_BLUE, 'B': WMT_GRAY, 'C': WMT_RED}
YEAR_COLORS  = [WMT_BLUE, WMT_GRAY, WMT_LIGHT, WMT_YELLOW]

MONTH_ORDER = ['January','February','March','April','May','June',
               'July','August','September','October','November','December']

# ── Global matplotlib style ───────────────────────────────────────────────────
plt.rcParams.update({
    'figure.facecolor':  'white',
    'axes.facecolor':    'white',
    'axes.grid':         True,
    'grid.color':        '#E5E5E5',
    'grid.linewidth':    0.7,
    'axes.spines.top':   False,
    'axes.spines.right': False,
    'font.family':       'DejaVu Sans',
    'axes.titlesize':    14,
    'axes.titleweight':  'bold',
    'axes.titlecolor':   WMT_DARK,
    'axes.labelcolor':   WMT_DARK,
    'axes.labelsize':    11,
    'xtick.color':       WMT_GRAY,
    'ytick.color':       WMT_GRAY,
    'xtick.labelsize':   9,
    'ytick.labelsize':   9,
})

DPI = 150   # output resolution

def fmt_millions(x, _):
    if abs(x) >= 1e9:  return f'${x/1e9:.1f}bn'
    if abs(x) >= 1e6:  return f'${x/1e6:.0f}M'
    return f'${x:,.0f}'

def add_bar_labels(ax, rects, fmt_fn=None, fontsize=7, color=WMT_DARK, pad=0.01):
    """Add value labels above each bar."""
    ymax = ax.get_ylim()[1]
    for rect in rects:
        h = rect.get_height()
        if h == 0 or np.isnan(h): continue
        label = fmt_fn(h) if fmt_fn else f'{h:,.0f}'
        ax.text(rect.get_x() + rect.get_width()/2, h + ymax*pad,
                label, ha='center', va='bottom', fontsize=fontsize,
                color=color, fontweight='bold')

def save(fig, filename):
    fig.savefig(os.path.join(OUT, filename), dpi=DPI,
                bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  -> {filename}')


# ══════════════════════════════════════════════════════════════════════════════
# SNOWFLAKE CONNECTION
# ══════════════════════════════════════════════════════════════════════════════

def get_connection():
    import snowflake.connector
    required = ['SNOWFLAKE_ACCOUNT','SNOWFLAKE_USER','SNOWFLAKE_PASSWORD',
                'SNOWFLAKE_WAREHOUSE','SNOWFLAKE_DATABASE','SNOWFLAKE_SCHEMA']
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise EnvironmentError(
            f"Missing Snowflake credentials in environment: {missing}\n"
            "Add them to a .env file in the same folder as this script."
        )
    conn = snowflake.connector.connect(
        account   = os.environ['SNOWFLAKE_ACCOUNT'],
        user      = os.environ['SNOWFLAKE_USER'],
        password  = os.environ['SNOWFLAKE_PASSWORD'],
        warehouse = os.environ['SNOWFLAKE_WAREHOUSE'],
        database  = os.environ['SNOWFLAKE_DATABASE'],
        schema    = os.environ['SNOWFLAKE_SCHEMA'],
        role      = os.environ.get('SNOWFLAKE_ROLE', ''),
    )
    print(f"  Connected: "
          f"{os.environ['SNOWFLAKE_DATABASE']}.{os.environ['SNOWFLAKE_SCHEMA']}\n")
    return conn


def qry(conn, sql, label=''):
    if label: print(f'  Querying {label} ...', end=' ', flush=True)
    df = pd.read_sql(sql, conn)
    df.columns = [c.upper() for c in df.columns]
    if label: print(f'{len(df):,} rows')
    return df


# ══════════════════════════════════════════════════════════════════════════════
# SQL QUERIES
# ══════════════════════════════════════════════════════════════════════════════

SQL_R1_HOLIDAY = """
SELECT d.IS_HOLIDAY AS "IsHoliday",
       SUM(f.STORE_WEEKLY_SALES) AS "Weekly_Sales"
FROM   RETAIL_FACT_TABLE f
JOIN   RETAIL_DATE_DIM d ON f.DATE_ID = d.DATE_ID
GROUP BY 1"""

SQL_R1_STORE = """
SELECT f.STORE_ID AS "Store", d.IS_HOLIDAY AS "IsHoliday",
       SUM(f.STORE_WEEKLY_SALES) AS "Weekly_Sales"
FROM   RETAIL_FACT_TABLE f
JOIN   RETAIL_DATE_DIM d ON f.DATE_ID = d.DATE_ID
GROUP BY 1,2 ORDER BY 1"""

SQL_R1_KPI = """
SELECT SUM(f.STORE_WEEKLY_SALES) AS "Total_Sales",
       MIN(d.IS_HOLIDAY)         AS "First_IsHoliday"
FROM   RETAIL_FACT_TABLE f
JOIN   RETAIL_DATE_DIM d ON f.DATE_ID = d.DATE_ID"""

SQL_R2 = """
SELECT
    CASE
        WHEN f.STORE_TEMPERATURE < 0  THEN '< 0'
        WHEN f.STORE_TEMPERATURE < 10 THEN '0-10'
        WHEN f.STORE_TEMPERATURE < 20 THEN '10-20'
        WHEN f.STORE_TEMPERATURE < 30 THEN '20-30'
        WHEN f.STORE_TEMPERATURE < 40 THEN '30-40'
        WHEN f.STORE_TEMPERATURE < 50 THEN '40-50'
        WHEN f.STORE_TEMPERATURE < 60 THEN '50-60'
        WHEN f.STORE_TEMPERATURE < 70 THEN '60-70'
        WHEN f.STORE_TEMPERATURE < 80 THEN '70-80'
        WHEN f.STORE_TEMPERATURE < 90 THEN '80-90'
        ELSE '> 90'
    END                       AS "TempBucket",
    YEAR(d.STORE_DATE)        AS "Year",
    SUM(f.STORE_WEEKLY_SALES) AS "Weekly_Sales",
    MIN(d.STORE_DATE)         AS "Earliest_Date"
FROM RETAIL_FACT_TABLE f
JOIN RETAIL_DATE_DIM  d ON f.DATE_ID  = d.DATE_ID
JOIN RETAIL_STORE_DIM s ON f.STORE_ID = s.STORE_ID AND f.DEPT_ID = s.DEPT_ID
                        AND d.STORE_DATE BETWEEN s.VRSN_START_DATE
                            AND COALESCE(s.VRSN_END_DATE,'9999-12-31')
GROUP BY 1,2 ORDER BY 2,1"""

SQL_R3 = """
SELECT s.STORE_ID AS "Store", s.STORE_SIZE AS "Size",
       SUM(f.STORE_WEEKLY_SALES) AS "Weekly_Sales"
FROM RETAIL_FACT_TABLE f
JOIN RETAIL_DATE_DIM  d ON f.DATE_ID  = d.DATE_ID
JOIN RETAIL_STORE_DIM s ON f.STORE_ID = s.STORE_ID AND f.DEPT_ID = s.DEPT_ID
                        AND d.STORE_DATE BETWEEN s.VRSN_START_DATE
                            AND COALESCE(s.VRSN_END_DATE,'9999-12-31')
GROUP BY 1,2 ORDER BY 2"""

SQL_R4 = """
SELECT MONTH(d.STORE_DATE) AS "Month", MONTHNAME(d.STORE_DATE) AS "MonthName",
       s.STORE_TYPE AS "Type", SUM(f.STORE_WEEKLY_SALES) AS "Weekly_Sales"
FROM RETAIL_FACT_TABLE f
JOIN RETAIL_DATE_DIM  d ON f.DATE_ID  = d.DATE_ID
JOIN RETAIL_STORE_DIM s ON f.STORE_ID = s.STORE_ID AND f.DEPT_ID = s.DEPT_ID
                        AND d.STORE_DATE BETWEEN s.VRSN_START_DATE
                            AND COALESCE(s.VRSN_END_DATE,'9999-12-31')
GROUP BY 1,2,3 ORDER BY 1,3"""

SQL_R5 = """
SELECT YEAR(d.STORE_DATE) AS "Year",
       SUM(f.MARKDOWN1) AS "MarkDown1", SUM(f.MARKDOWN2) AS "MarkDown2",
       SUM(f.MARKDOWN3) AS "MarkDown3", SUM(f.MARKDOWN4) AS "MarkDown4",
       SUM(f.MARKDOWN5) AS "MarkDown5"
FROM   RETAIL_FACT_TABLE f
JOIN   RETAIL_DATE_DIM d ON f.DATE_ID = d.DATE_ID
GROUP BY 1 ORDER BY 1"""

SQL_R6_PIE = """
SELECT s.STORE_TYPE AS "Type", SUM(f.STORE_WEEKLY_SALES) AS "Weekly_Sales"
FROM RETAIL_FACT_TABLE f
JOIN RETAIL_DATE_DIM  d ON f.DATE_ID  = d.DATE_ID
JOIN RETAIL_STORE_DIM s ON f.STORE_ID = s.STORE_ID AND f.DEPT_ID = s.DEPT_ID
                        AND d.STORE_DATE BETWEEN s.VRSN_START_DATE
                            AND COALESCE(s.VRSN_END_DATE,'9999-12-31')
GROUP BY 1 ORDER BY 1"""

SQL_R6_STORE = """
SELECT s.STORE_TYPE AS "Type", f.STORE_ID AS "Store",
       SUM(f.STORE_WEEKLY_SALES) AS "Weekly_Sales"
FROM RETAIL_FACT_TABLE f
JOIN RETAIL_DATE_DIM  d ON f.DATE_ID  = d.DATE_ID
JOIN RETAIL_STORE_DIM s ON f.STORE_ID = s.STORE_ID AND f.DEPT_ID = s.DEPT_ID
                        AND d.STORE_DATE BETWEEN s.VRSN_START_DATE
                            AND COALESCE(s.VRSN_END_DATE,'9999-12-31')
GROUP BY 1,2 ORDER BY 1,3 DESC"""

SQL_R7_DONUT = """
SELECT YEAR(d.STORE_DATE) AS "Year", SUM(f.FUEL_PRICE) AS "Fuel_Price"
FROM   RETAIL_FACT_TABLE f
JOIN   RETAIL_DATE_DIM d ON f.DATE_ID = d.DATE_ID
GROUP BY 1 ORDER BY 1"""

SQL_R7_TABLE = """
SELECT f.STORE_ID AS "Store", YEAR(d.STORE_DATE) AS "Year",
       SUM(f.FUEL_PRICE) AS "Fuel_Price"
FROM   RETAIL_FACT_TABLE f
JOIN   RETAIL_DATE_DIM d ON f.DATE_ID = d.DATE_ID
GROUP BY 1,2 ORDER BY 1,2"""

SQL_R8_YEAR  = """
SELECT YEAR(d.STORE_DATE) AS "Year",
       SUM(f.STORE_WEEKLY_SALES) AS "Weekly_Sales"
FROM   RETAIL_FACT_TABLE f JOIN RETAIL_DATE_DIM d ON f.DATE_ID=d.DATE_ID
GROUP BY 1 ORDER BY 1"""

SQL_R8_MONTH = """
SELECT MONTH(d.STORE_DATE) AS "Month", MONTHNAME(d.STORE_DATE) AS "MonthName",
       SUM(f.STORE_WEEKLY_SALES) AS "Weekly_Sales"
FROM   RETAIL_FACT_TABLE f JOIN RETAIL_DATE_DIM d ON f.DATE_ID=d.DATE_ID
GROUP BY 1,2 ORDER BY 1"""

SQL_R8_DAY   = """
SELECT DAY(d.STORE_DATE) AS "Day",
       SUM(f.STORE_WEEKLY_SALES) AS "Weekly_Sales"
FROM   RETAIL_FACT_TABLE f JOIN RETAIL_DATE_DIM d ON f.DATE_ID=d.DATE_ID
GROUP BY 1 ORDER BY 1"""

SQL_R9 = """
SELECT ROUND(f.CPI,2) AS "CPI", SUM(f.STORE_WEEKLY_SALES) AS "Weekly_Sales"
FROM   RETAIL_FACT_TABLE f WHERE f.CPI IS NOT NULL
GROUP BY 1 ORDER BY 1"""

SQL_R10 = """
SELECT f.DEPT_ID AS "Dept", SUM(f.STORE_WEEKLY_SALES) AS "Weekly_Sales"
FROM   RETAIL_FACT_TABLE f GROUP BY 1 ORDER BY 1"""


# ══════════════════════════════════════════════════════════════════════════════
# CHART BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def report1(r1_holiday, r1_store, r1_kpi):
    """Report 1 — Weekly Sales by Store and Holiday (single main chart)."""
    total   = float(r1_kpi['TOTAL_SALES'].iloc[0])
    first_h = str(r1_kpi['FIRST_ISHOLIDAY'].iloc[0])

    fig, ax_bar = plt.subplots(figsize=(16, 7))

    stores  = sorted(r1_store['STORE'].unique())
    x       = np.arange(len(stores))
    width   = 0.4
    hvals   = sorted(r1_store['ISHOLIDAY'].unique())
    colors  = [WMT_BLUE, WMT_GRAY]

    for i, hval in enumerate(hvals):
        sub = r1_store[r1_store['ISHOLIDAY']==hval].set_index('STORE')
        vals = [sub.loc[s,'WEEKLY_SALES'] if s in sub.index else 0 for s in stores]
        rects = ax_bar.bar(x + i*width - width/2, vals, width,
                           label=f'Holiday={hval}', color=colors[i],
                           linewidth=0)
        add_bar_labels(ax_bar, rects, lambda v: f'${v/1e6:.0f}M', fontsize=6)

    ax_bar.set_xticks(x); ax_bar.set_xticklabels(stores, fontsize=8)
    ax_bar.set_xlabel('Store'); ax_bar.set_ylabel('Weekly Sales ($)')
    ax_bar.yaxis.set_major_formatter(mtick.FuncFormatter(fmt_millions))
    ax_bar.set_title(
        f'Weekly Sales by Store and Holiday  |  Total: ${total/1e9:.2f}bn  '
        f'|  First IsHoliday: {first_h.upper()}',
        fontsize=14, fontweight='bold', color=WMT_DARK)
    ax_bar.legend(title='IsHoliday', fontsize=9)
    plt.tight_layout()
    save(fig, 'report1_weekly_sales_by_store_holiday.png')


def report2(df):
    """Report 2 — Weekly Sales by Temperature and Year."""
    BUCKET_ORDER = ['< 0','0-10','10-20','20-30','30-40',
                    '40-50','50-60','60-70','70-80','80-90','> 90']
    pivot = df.pivot_table(index='TEMPBUCKET', columns='YEAR',
                           values='WEEKLY_SALES', aggfunc='sum').fillna(0)
    pivot = pivot.reindex([b for b in BUCKET_ORDER if b in pivot.index])
    earliest = pd.to_datetime(df['EARLIEST_DATE'].min()).strftime('%b %d, %Y')

    years  = sorted(pivot.columns)
    x      = np.arange(len(pivot))
    width  = 0.8 / len(years)

    fig, ax = plt.subplots(figsize=(16, 7))
    for i, yr in enumerate(years):
        offset = (i - len(years)/2 + 0.5) * width
        rects  = ax.bar(x + offset, pivot[yr], width,
                        label=str(yr), color=YEAR_COLORS[i % len(YEAR_COLORS)],
                        linewidth=0)
        add_bar_labels(ax, rects, lambda v: f'${v/1e6:.1f}M', fontsize=6)

    ax.set_xticks(x); ax.set_xticklabels(pivot.index, fontsize=9)
    ax.set_xlabel('Temperature Range (°F)'); ax.set_ylabel('Weekly Sales ($)')
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(fmt_millions))
    ax.set_title(f'Weekly Sales by Temperature and Year  |  Earliest: {earliest}',
                 fontsize=14, fontweight='bold', color=WMT_DARK)
    ax.legend(title='Year', fontsize=9)
    plt.tight_layout()
    save(fig, 'report2_weekly_sales_by_temperature_year.png')


def report3(df):
    """Report 3 — Weekly Sales by Store Size."""
    df = df.sort_values('SIZE')
    fig, ax = plt.subplots(figsize=(16, 7))
    ax.fill_between(df['SIZE'], df['WEEKLY_SALES'],
                    color=WMT_BLUE, alpha=0.25, linewidth=0)
    ax.plot(df['SIZE'], df['WEEKLY_SALES'],
            color=WMT_BLUE, linewidth=2)

    # Label top 6 stores
    for _, row in df.nlargest(6, 'WEEKLY_SALES').iterrows():
        ax.annotate(f"Store {int(row['STORE'])}\n${row['WEEKLY_SALES']/1e6:.0f}M",
                    xy=(row['SIZE'], row['WEEKLY_SALES']),
                    xytext=(0, 18), textcoords='offset points',
                    ha='center', fontsize=8, color=WMT_DARK, fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color=WMT_BLUE, lw=1.2))

    ax.set_xlabel('Store Size (sq ft)'); ax.set_ylabel('Weekly Sales ($)')
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x,_: f'{x:,.0f}'))
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(fmt_millions))
    ax.set_title('Weekly Sales by Store Size', fontsize=14,
                 fontweight='bold', color=WMT_DARK)
    plt.tight_layout()
    save(fig, 'report3_weekly_sales_by_store_size.png')


def report4(df):
    """Report 4 — Weekly Sales by Store Type and Month."""
    df['MONTHNAME'] = pd.Categorical(df['MONTHNAME'],
                                     categories=MONTH_ORDER, ordered=True)
    df = df.sort_values('MONTHNAME')
    fig, ax = plt.subplots(figsize=(16, 7))

    for t, grp in df.groupby('TYPE'):
        ax.plot(grp['MONTHNAME'].astype(str), grp['WEEKLY_SALES'],
                marker='o', linewidth=2.5, markersize=7,
                color=TYPE_COLORS.get(t, WMT_BLUE), label=f'Type {t}')
        for _, row in grp.iterrows():
            ax.text(row['MONTHNAME'], row['WEEKLY_SALES'] * 1.015,
                    f"${row['WEEKLY_SALES']/1e6:.0f}M",
                    ha='center', fontsize=7, color=TYPE_COLORS.get(t, WMT_DARK))

    ax.set_xlabel('Month'); ax.set_ylabel('Weekly Sales ($)')
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(fmt_millions))
    ax.set_title('Weekly Sales by Store Type and Month', fontsize=14,
                 fontweight='bold', color=WMT_DARK)
    ax.tick_params(axis='x', rotation=30)
    ax.legend(title='Store Type', fontsize=10)
    plt.tight_layout()
    save(fig, 'report4_weekly_sales_by_type_month.png')


def report5(df):
    """Report 5 — Markdown Sales by Year."""
    md_cols   = [c for c in ['MARKDOWN1','MARKDOWN2','MARKDOWN3','MARKDOWN4','MARKDOWN5']
                 if c in df.columns]
    md_labels = [f'MarkDown{c[-1]}' for c in md_cols]
    md_colors = [WMT_BLUE, WMT_GRAY, WMT_RED, '#7F5300', WMT_DARK]
    years     = df['YEAR'].astype(str).tolist()
    x         = np.arange(len(years))
    width     = 0.8 / len(md_cols)

    fig, ax = plt.subplots(figsize=(14, 7))
    for i, (col, label) in enumerate(zip(md_cols, md_labels)):
        offset = (i - len(md_cols)/2 + 0.5) * width
        rects  = ax.bar(x + offset, df[col], width,
                        label=label, color=md_colors[i], linewidth=0)
        add_bar_labels(ax, rects,
                       lambda v: f'${v/1e9:.2f}bn' if v > 3e8 else f'${v/1e6:.0f}M',
                       fontsize=7)

    ax.set_xticks(x); ax.set_xticklabels(years)
    ax.set_xlabel('Year'); ax.set_ylabel('Markdown Amount ($)')
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(fmt_millions))
    ax.set_title('Markdown Sales by Year', fontsize=14,
                 fontweight='bold', color=WMT_DARK)
    ax.legend(title='Markdown Type', fontsize=9)
    plt.tight_layout()
    save(fig, 'report5_markdown_sales_by_year.png')


def report6(r6_pie, r6_store):
    """Report 6 — Weekly Sales by Store Type (single main chart)."""
    total = r6_pie['WEEKLY_SALES'].sum()
    share_str = '  |  '.join(
        f"{t}: {v/total*100:.1f}%"
        for t, v in zip(r6_pie['TYPE'], r6_pie['WEEKLY_SALES'])
    )

    fig, ax_bar = plt.subplots(figsize=(15, 9))

    # Horizontal bars — one group per type
    palette = plt.cm.get_cmap('tab20').colors
    yticks, ylabels = [], []
    y_pos = 0
    for t in sorted(r6_store['TYPE'].unique()):
        grp = r6_store[r6_store['TYPE']==t].sort_values('WEEKLY_SALES')
        for j, (_, row) in enumerate(grp.iterrows()):
            color = TYPE_COLORS.get(t, palette[j % len(palette)])
            ax_bar.barh(y_pos, row['WEEKLY_SALES'], color=color,
                        alpha=0.85, linewidth=0, height=0.7)
            ax_bar.text(row['WEEKLY_SALES']*1.005, y_pos,
                        f"${row['WEEKLY_SALES']/1e6:.0f}M",
                        va='center', fontsize=7, color=WMT_DARK)
            yticks.append(y_pos); ylabels.append(f"{t}-{int(row['STORE'])}")
            y_pos += 1
        y_pos += 0.5   # gap between types

    ax_bar.set_yticks(yticks); ax_bar.set_yticklabels(ylabels, fontsize=7)
    ax_bar.set_xlabel('Weekly Sales ($)')
    ax_bar.xaxis.set_major_formatter(mtick.FuncFormatter(fmt_millions))
    ax_bar.set_title(
        f'Weekly Sales by Store Type  |  Share: {share_str}',
        fontsize=14, fontweight='bold', color=WMT_DARK)

    # Type legend
    handles = [mpatches.Patch(color=TYPE_COLORS[t], label=f'Type {t}')
               for t in sorted(TYPE_COLORS)]
    ax_bar.legend(handles=handles, fontsize=9, loc='lower right')
    plt.tight_layout()
    save(fig, 'report6_weekly_sales_by_store_type.png')


def report7(r7_donut, r7_table):
    """Report 7 — Fuel Price by Year (single main chart)."""
    pivot = r7_table.pivot(index='STORE', columns='YEAR',
                           values='FUEL_PRICE').reset_index().fillna(0)
    years = sorted([c for c in pivot.columns if isinstance(c, (int, np.integer))])
    total = r7_donut['FUEL_PRICE'].sum()
    share_str = '  |  '.join(
        f"{int(y)}: {v/total*100:.1f}%"
        for y, v in zip(r7_donut['YEAR'], r7_donut['FUEL_PRICE'])
    )

    fig, ax_bar = plt.subplots(figsize=(16, 7))
    donut_colors = [WMT_BLUE, WMT_GRAY, WMT_LIGHT, WMT_YELLOW]

    # Grouped bar — top 15 stores
    top15  = pivot.nlargest(15, years[-1]) if years else pivot.head(15)
    x      = np.arange(len(top15))
    width  = 0.8 / len(years)
    for i, yr in enumerate(years):
        offset = (i - len(years)/2 + 0.5) * width
        ax_bar.bar(x + offset, top15[yr], width,
                   label=str(yr), color=donut_colors[i % len(donut_colors)],
                   linewidth=0)

    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels(top15['STORE'].astype(int), fontsize=8)
    ax_bar.set_xlabel('Store'); ax_bar.set_ylabel('Fuel Price ($)')
    ax_bar.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x,_: f'{x:,.0f}'))
    ax_bar.set_title(
        f'Fuel Price by Store & Year (Top 15 Stores)  |  Total: ${total/1e6:.2f}M  '
        f'|  Share: {share_str}',
        fontsize=13, fontweight='bold', color=WMT_DARK)
    ax_bar.legend(title='Year', fontsize=9)
    plt.tight_layout()
    save(fig, 'report7_fuel_price_by_year.png')


def report8(r8_year, r8_month, r8_day):
    """Report 8 — Weekly Sales by Year, Month and Day (single main chart)."""
    r8_month['MONTHNAME'] = pd.Categorical(r8_month['MONTHNAME'],
                                           categories=MONTH_ORDER, ordered=True)
    r8_month = r8_month.sort_values('MONTHNAME')

    year_str = '  |  '.join(
        f"{int(y)}: ${v/1e9:.2f}bn"
        for y, v in zip(r8_year['YEAR'], r8_year['WEEKLY_SALES'])
    )
    best_month = r8_month.loc[r8_month['WEEKLY_SALES'].idxmax(), 'MONTHNAME']

    fig, ax = plt.subplots(figsize=(16, 7))
    rects = ax.bar(r8_day['DAY'], r8_day['WEEKLY_SALES'],
                   color=WMT_BLUE, linewidth=0)
    add_bar_labels(ax, rects, lambda v: f'${v/1e6:.0f}M' if v > 1.8e8 else '',
                   fontsize=7)
    ax.set_xlabel('Day of Month'); ax.set_ylabel('Weekly Sales ($)')
    ax.xaxis.set_major_locator(mtick.MultipleLocator(1))
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(fmt_millions))
    ax.set_title(
        f'Weekly Sales by Day of Month  |  By Year: {year_str}  |  Best Month: {best_month}',
        fontsize=13, fontweight='bold', color=WMT_DARK)

    plt.tight_layout()
    save(fig, 'report8_weekly_sales_year_month_day.png')


def report9(df):
    """Report 9 — Weekly Sales by CPI."""
    df = df.sort_values('CPI')
    fig, ax = plt.subplots(figsize=(16, 7))

    ax.fill_between(df['CPI'], df['WEEKLY_SALES'],
                    color=WMT_BLUE, alpha=0.15, linewidth=0)
    ax.plot(df['CPI'], df['WEEKLY_SALES'],
            color=WMT_BLUE, linewidth=1.2, linestyle='--', marker='o',
            markersize=2, markeredgewidth=0)

    # Annotate top peaks
    for _, row in df.nlargest(6, 'WEEKLY_SALES').iterrows():
        ax.annotate(f'${row["WEEKLY_SALES"]/1e6:.1f}M',
                    xy=(row['CPI'], row['WEEKLY_SALES']),
                    xytext=(0, 12), textcoords='offset points',
                    ha='center', fontsize=8, color=WMT_DARK, fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color=WMT_BLUE, lw=1))

    ax.set_xlabel('CPI'); ax.set_ylabel('Weekly Sales ($)')
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(fmt_millions))
    ax.set_title('Weekly Sales by CPI', fontsize=14,
                 fontweight='bold', color=WMT_DARK)
    plt.tight_layout()
    save(fig, 'report9_weekly_sales_by_cpi.png')


def report10(df):
    """Report 10 — Department-Wise Weekly Sales (single main chart)."""
    df          = df.sort_values('DEPT')
    top5        = df.nlargest(5, 'WEEKLY_SALES')
    grand_total = df['WEEKLY_SALES'].sum()
    top5_str = '  |  '.join(
        f"Dept {int(d)}: ${v/1e6:.0f}M"
        for d, v in zip(top5['DEPT'], top5['WEEKLY_SALES'])
    )

    fig, ax_all = plt.subplots(figsize=(18, 9))

    # All departments — coloured by seaborn palette
    palette = sns.color_palette('husl', len(df))
    ax_all.bar(df['DEPT'].astype(str), df['WEEKLY_SALES'],
               color=palette, linewidth=0)
    ax_all.set_xlabel('Department'); ax_all.set_ylabel('Weekly Sales ($)')
    ax_all.yaxis.set_major_formatter(mtick.FuncFormatter(fmt_millions))
    ax_all.tick_params(axis='x', rotation=70, labelsize=7)
    ax_all.set_title(
        f'Department-Wise Weekly Sales  |  Grand Total: ${grand_total/1e9:.3f}bn\n'
        f'Top 5 \u2014 {top5_str}',
        fontsize=13, fontweight='bold', color=WMT_DARK)

    plt.tight_layout()
    save(fig, 'report10_department_wise_sales.png')


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print('=' * 65)
    print('  RETAIL BI — Python Visualizations (Snowflake → PNG)')
    print('=' * 65)

    conn = get_connection()
    try:
        print('Fetching data from Snowflake GOLD schema...\n')

        r1_holiday = qry(conn, SQL_R1_HOLIDAY, 'R1  holiday split')
        r1_store   = qry(conn, SQL_R1_STORE,   'R1  store totals')
        r1_kpi     = qry(conn, SQL_R1_KPI,     'R1  KPI')
        r2         = qry(conn, SQL_R2,         'R2  temp + year')
        r3         = qry(conn, SQL_R3,         'R3  store size')
        r4         = qry(conn, SQL_R4,         'R4  type + month')
        r5         = qry(conn, SQL_R5,         'R5  markdowns')
        r6_pie     = qry(conn, SQL_R6_PIE,     'R6  type pie')
        r6_store   = qry(conn, SQL_R6_STORE,   'R6  store bars')
        r7_donut   = qry(conn, SQL_R7_DONUT,   'R7  fuel donut')
        r7_table   = qry(conn, SQL_R7_TABLE,   'R7  fuel table')
        r8_year    = qry(conn, SQL_R8_YEAR,    'R8  year')
        r8_month   = qry(conn, SQL_R8_MONTH,   'R8  month')
        r8_day     = qry(conn, SQL_R8_DAY,     'R8  day')
        r9         = qry(conn, SQL_R9,         'R9  CPI')
        r10        = qry(conn, SQL_R10,        'R10 departments')

        print(f'\nAll queries done. Writing PNGs to {OUT}/\n')
        print('-' * 65)

        print('Report 1:  Weekly Sales by Store and Holiday')
        report1(r1_holiday, r1_store, r1_kpi)

        print('Report 2:  Weekly Sales by Temperature and Year')
        report2(r2)

        print('Report 3:  Weekly Sales by Store Size')
        report3(r3)

        print('Report 4:  Weekly Sales by Store Type and Month')
        report4(r4)

        print('Report 5:  Markdown Sales by Year')
        report5(r5)

        print('Report 6:  Weekly Sales by Store Type')
        report6(r6_pie, r6_store)

        print('Report 7:  Fuel Price by Year')
        report7(r7_donut, r7_table)

        print('Report 8:  Weekly Sales by Year, Month and Day')
        report8(r8_year, r8_month, r8_day)

        print('Report 9:  Weekly Sales by CPI')
        report9(r9)

        print('Report 10: Department-Wise Weekly Sales')
        report10(r10)

    finally:
        conn.close()
        print('\n  Snowflake connection closed.')

    print('\n' + '=' * 65)
    print('  All 10 PNGs saved:')
    for f in sorted(os.listdir(OUT)):
        if f.endswith('.png'):
            print(f'    {f}')
    print('=' * 65)


if __name__ == '__main__':
    main()
