"""
build_dataset.py  -  Clean 9 retailer CSVs and build the Excel file for Power BI.

HOW TO RUN (from the project folder that contains the data/ folder):
    python build_dataset.py

INPUT : data/*.csv                      (the 9 raw files from Kaggle)
OUTPUT: output/fashion_powerbi.xlsx     (2 Excel tables: listings, keywords)
        output/listings.csv, output/keywords.csv   (CSV copies, handy for GitHub)

WHAT IT DOES (same steps as the notebook, in order):
  1. Load the 9 files and drop duplicate rows
  2. Parse prices (4 different formats -> numbers)
  3. Standardize retailer and brand names
  4. Group 500+ category labels into a few categories
  5. Group colors into color families
  6. Collapse "one row per size" into "one row per product + color"
  7. Remove multi-packs, add helper columns (0/1 flags, discount %)
  8. Build the keyword table from product descriptions
  9. Write the Excel file
"""
import glob
import os
import re

import numpy as np
import pandas as pd

DATA_DIR = os.environ.get("DATA_DIR", "data")
OUT_DIR = os.environ.get("OUT_DIR", "output")
os.makedirs(OUT_DIR, exist_ok=True)

# ----------------------------------------------------------------------------
# 1. LOAD
# ----------------------------------------------------------------------------
USECOLS = ["retailer", "product_name", "brand_name", "product_category", "color",
           "mrp", "price", "rating", "review_count", "pdp_url", "description"]

files = sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
if not files:
    raise SystemExit(f"No CSV files found in '{DATA_DIR}/'. Put the 9 raw files there.")

frames = []
raw_rows = 0
for f in files:
    d = pd.read_csv(f, usecols=USECOLS)   # "available_size" is skipped on purpose:
    raw_rows += len(d)                    # rows that differ only by size become exact duplicates
    d = d.drop_duplicates()
    frames.append(d)
    print(f"  loaded {os.path.basename(f):28s} {len(d):>8,} rows after dedupe")

df = pd.concat(frames, ignore_index=True)
del frames
print(f"\n1. Raw rows: {raw_rows:,}  ->  after dropping duplicates: {len(df):,}")


# ----------------------------------------------------------------------------
# 2. PRICES  ("$24.50", "9.50 USD", "$52.00-$56.00", "$35.00 ... Now $10.00")
# ----------------------------------------------------------------------------
def numbers_in(cell):
    return [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*\.?\d*", str(cell))]


def parse_sale(cell):
    nums = numbers_in(cell)
    if not nums:
        return np.nan
    if "now" in str(cell).lower() and len(nums) >= 2:
        return nums[-1]                       # "was $35 now $10" -> 10
    if len(nums) >= 2:
        return (nums[0] + nums[1]) / 2        # range "$52-$56" -> average
    return nums[0]


def parse_list(cell):
    nums = numbers_in(cell)
    if not nums:
        return np.nan
    if "now" in str(cell).lower() and len(nums) >= 2:
        return nums[0]                        # "was $35 now $10" -> 35
    if len(nums) >= 2:
        return (nums[0] + nums[1]) / 2
    return nums[0]


df["sale_price"] = df.price.map(parse_sale)
df["list_price"] = df.mrp.map(parse_list)
bad = df.sale_price > df.list_price           # list price can never be below sale price
df.loc[bad, "list_price"] = df.loc[bad, "sale_price"]
print(f"2. Prices parsed. Missing sale_price: {df.sale_price.isna().sum():,}")

# ----------------------------------------------------------------------------
# 3. RETAILER + BRAND
# ----------------------------------------------------------------------------
RETAILER_MAP = {
    "Ae US": "American Eagle", "Amazon US": "Amazon", "Btemptd US": "b.tempt'd (site)",
    "Calvin Klein US": "Calvin Klein (site)", "Hankypanky US": "Hanky Panky (site)",
    "Macys US": "Macy's", "Nordstrom US": "Nordstrom", "Topshop US": "Topshop (site)",
    "Victoriassecret US": "Victoria's Secret (site)",
}
df["retailer"] = df.retailer.str.strip().replace(RETAILER_MAP)


def clean_brand(raw_brand, product_name):
    text = re.sub(r"[^a-z0-9' ]", " ", str(raw_brand).lower().replace("-", " "))
    text = re.sub(r"\s+", " ", text).strip()
    if "victoria" in text and "pink" in text: return "Victoria's Secret PINK"
    if "victoria" in text:                    return "Victoria's Secret"
    if "hanky" in text:                       return "Hanky Panky"
    if "tempt" in text:                       return "b.tempt'd"
    if "wacoal" in text:                      return "Wacoal"
    if "calvin" in text:                      return "Calvin Klein"
    if text in ("aerie", "aeo"):              return "Aerie"
    if "topshop" in text:                     return "Topshop"
    if "vanity" in text:                      return "Vanity Fair"
    if "nordstrom" in text:                   return "Nordstrom Lingerie"
    name = str(product_name).lower()          # junk brand value: try the product name
    for key, brand in [("wacoal", "Wacoal"), ("hanky", "Hanky Panky"), ("calvin", "Calvin Klein"),
                       ("tempt", "b.tempt'd"), ("vanity", "Vanity Fair")]:
        if key in name:
            return brand
    return "Other"


df["brand"] = [clean_brand(b, n) for b, n in zip(df.brand_name, df.product_name)]
# the b.tempt'd site sells its own line but labels it "WACOAL": relabel so brands compare fairly
df.loc[df.retailer == "b.tempt'd (site)", "brand"] = "b.tempt'd"
print(f"3. Brand names: {df.brand_name.nunique()} raw variants -> {df.brand.nunique()} brands")

# ----------------------------------------------------------------------------
# 4. CATEGORY  (product name first, then category label; strip the retailer path prefix,
#    otherwise every Macy's item matches the word "shapewear")
# ----------------------------------------------------------------------------
CATEGORY_RULES = [
    ("Sports Bra", r"sport|athletic|yoga"),
    ("Shapewear",  r"shapewear|shaper|slimm|control"),
    ("Bralette",   r"bralet|bandeau|triangle|halter|crop"),
    ("Bra",        r"\bbra\b|bras\b|demi|push-up|pushup|push up|underwire|balconette|plunge|strapless|minimizer"),
    ("Panty",      r"cheekster|knicker|vikini|boypant|panty|panties|thong|brief|boyshort|hipster|cheeky|bikini|undie"),
]
PATH_PREFIX = re.compile(r"^\s*women\s*-\s*lingerie\s*&\s*shapewear\s*-\s*", re.I)


def group_category(product_name, product_category):
    cat_clean = PATH_PREFIX.sub("", str(product_category))
    for text in (str(product_name).lower(), cat_clean.lower()):
        for label, pattern in CATEGORY_RULES:
            if re.search(pattern, text):
                return label
    return "Other / Unclassified"


# classify each unique (name, category) pair once - much faster than row by row
pairs = df[["product_name", "product_category"]].drop_duplicates()
pairs["category"] = [group_category(n, c) for n, c in zip(pairs.product_name, pairs.product_category)]
df = df.merge(pairs, on=["product_name", "product_category"], how="left")
print("4. Categories grouped.")

# ----------------------------------------------------------------------------
# 5. COLOR
# ----------------------------------------------------------------------------
SIZE_WORDS = {"small", "medium", "large", "x-large", "xx-large", "xs", "s", "m", "l", "xl", "one size"}
COLOR_RULES = [
    ("Black",           r"black|noir|onyx|ebony|midnight|caviar|darkness"),
    ("White / Ivory",   r"white|ivory|cream|coconut|pearl|marshmallow|muslin|vanilla|ecru|snow"),
    ("Nude / Beige",    r"nude|beige|buff|bare|champagne|taupe|natural|sand|latte|almond|skin"),
    ("Pink",            r"pink|rose|rosy|blush|coral|peach|mauve|berry|fuchsia|magenta"),
    ("Red",             r"red|burgundy|wine|maroon|cherry|ruby|scarlet"),
    ("Blue",            r"blue|navy|ensign|denim|teal|aqua|turquoise|sapphire|cobalt"),
    ("Green",           r"green|olive|emerald|sage|mint|jade|forest"),
    ("Purple",          r"purple|lilac|lavender|violet|plum|orchid"),
    ("Grey / Silver",   r"gr[ae]y|silver|charcoal|heather|marl|granite|pewter|slate|steel"),
    ("Brown",           r"brown|chocolate|espresso|cocoa|coffee|caramel|mocha|cappuccino|cinnamon"),
    ("Yellow / Orange", r"yellow|gold|orange|lemon|mustard|amber|tangerine"),
    ("Print / Multi",   r"print|stripe|floral|dot|leopard|animal|multi|plaid|check|paisley|camo|graphic"),
]


def clean_color(color):
    text = re.sub(r"\s+", " ", str(color)).strip().lower()
    if text in SIZE_WORDS or text in ("", "nan", "none"):
        return np.nan                           # Amazon puts sizes in the color column
    return text


def group_color(color):
    if pd.isna(color):
        return np.nan
    for label, pattern in COLOR_RULES:
        if re.search(pattern, color):
            return label
    return "Other"


colors = df[["color"]].drop_duplicates()
colors["color_clean"] = colors.color.map(clean_color)
colors["color_family"] = colors.color_clean.map(group_color)
df = df.merge(colors, on="color", how="left")
print("5. Colors grouped.")

# ----------------------------------------------------------------------------
# 6. ONE ROW PER (retailer, product URL, color)   -- instead of one row per size
# ----------------------------------------------------------------------------
df["rating"] = pd.to_numeric(df.rating, errors="coerce")
df["review_count"] = pd.to_numeric(df.review_count, errors="coerce")
df["color_key"] = df.color_clean.fillna("(unknown)")   # otherwise groupby silently drops these rows

listings = (
    df.groupby(["retailer", "pdp_url", "color_key"], as_index=False, sort=False)
      .agg(product_name=("product_name", "first"),
           brand=("brand", "first"),
           category=("category", "first"),
           color_family=("color_family", "first"),
           list_price=("list_price", "median"),
           sale_price=("sale_price", "median"),
           rating=("rating", "first"),
           review_count=("review_count", "first"),
           description=("description", "first"))
)
listings["color"] = listings.color_key.replace("(unknown)", np.nan)
print(f"6. One row per product+color: {len(df):,} -> {len(listings):,} rows "
      f"({listings.pdp_url.nunique():,} unique product URLs)")
del df

# ----------------------------------------------------------------------------
# 7. FILTERS + HELPER COLUMNS
# ----------------------------------------------------------------------------
MULTIPACK = r"\d+[- ]?pack|pack of|\d+[- ]day|\bset of\b|\bpk\b"
is_multipack = listings.product_name.str.contains(MULTIPACK, case=False, regex=True)
print(f"7. Multi-packs removed: {is_multipack.sum():,};  unknown brand removed: {(listings.brand == 'Other').sum():,}")
listings = listings[~is_multipack & (listings.brand != "Other")].copy()

listings["discount_pct"] = (1 - listings.sale_price / listings.list_price).clip(lower=0)
listings["on_sale_flag"] = (listings.discount_pct > 0).astype(int)
listings["has_rating_flag"] = listings.rating.notna().astype(int)

# ----------------------------------------------------------------------------
# 8. KEYWORDS  (one row per brand x word, counted per product, not per color)
# ----------------------------------------------------------------------------
STOP = set("""a an the and or of to in for with on by at from is are be this that it its as your you our
we can will one all any more also made makes make has have not no up out into per than then them they
their these those which who what when where while about over under just only very each other such
women womens woman bra panty panties underwear wash hand machine imported cotton nylon spandex
polyester elastane lining fabric style fit size sizes front back wear read less more color colors
calvin klein hanky panky wacoal tempt victoria secret victorias aerie pink topshop vanity fair
nordstrom designed""".split())


def tokens(text):
    clean = re.sub(r"read more|read less", " ", str(text), flags=re.I).lower()
    return {w for w in re.findall(r"[a-z][a-z\-]{3,}", clean) if w not in STOP}


products = listings.drop_duplicates(["retailer", "pdp_url"])
rows = []
for brand, desc, price, rating in zip(products.brand, products.description,
                                      products.sale_price, products.rating):
    for word in tokens(desc):
        rows.append((brand, word, price, rating))

keywords = pd.DataFrame(rows, columns=["brand", "keyword", "sale_price", "rating"])
keywords = (keywords.groupby(["brand", "keyword"])
            .agg(n_products=("keyword", "size"),
                 avg_price=("sale_price", "mean"),
                 avg_rating=("rating", "mean"))
            .reset_index())
keywords = keywords[keywords.n_products >= 5].round(2)
print(f"8. Keyword table: {len(keywords):,} rows")

# ----------------------------------------------------------------------------
# 9. SAVE
# ----------------------------------------------------------------------------
listings = listings[["retailer", "brand", "product_name", "category", "color", "color_family",
                     "list_price", "sale_price", "discount_pct", "on_sale_flag",
                     "rating", "review_count", "has_rating_flag"]]
listings = listings.round({"list_price": 2, "sale_price": 2, "discount_pct": 4})

listings.to_csv(os.path.join(OUT_DIR, "listings.csv"), index=False)
keywords.to_csv(os.path.join(OUT_DIR, "keywords.csv"), index=False)

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

xlsx_path = os.path.join(OUT_DIR, "fashion_powerbi.xlsx")
with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
    listings.to_excel(writer, sheet_name="data_listings", index=False)
    keywords.to_excel(writer, sheet_name="data_keywords", index=False)

# Power BI only reads Excel data that is formatted as an Excel "Table"
wb = load_workbook(xlsx_path)
for sheet, table_name in [("data_listings", "listings"), ("data_keywords", "keywords")]:
    ws = wb[sheet]
    ref = f"A1:{get_column_letter(ws.max_column)}{ws.max_row}"
    table = Table(displayName=table_name, ref=ref)
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(table)
wb.save(xlsx_path)

# ----------------------------------------------------------------------------
# SELF-CHECK  (compare with the "expected" numbers in the guide)
# ----------------------------------------------------------------------------
print("\n================ SELF-CHECK ================")
print(f"listings rows : {len(listings):,}      (expect ~33,700)")
print(f"brands        : {listings.brand.nunique()}               (expect 10)")
print(f"retailers     : {listings.retailer.nunique()}               (expect 9)")
print(f"missing sale_price: {listings.sale_price.isna().sum()}   (expect 0)")
print("\ncategory share (expect Panty ~36%, Bra ~31%, Bralette ~19%, Sports Bra ~9%, Other ~5%):")
print((listings.category.value_counts(normalize=True) * 100).round(1).to_string())
print("\nmedian price by brand:")
print(listings.groupby("brand").sale_price.median().sort_values(ascending=False).round(2).to_string())
print(f"\nSaved: {xlsx_path}")
