# Raw data

The raw files are **not stored in this repository**. They are large (the Victoria's Secret file alone is about 390 MB, above GitHub's 100 MB per-file limit) and they belong to their original source.

## Where to get them

Dataset: **"Innerwear Data from Victoria's Secret and Others"**, published on Kaggle. The data was collected from retailer websites by PromptCloud, covering June to July 2017.

## Files expected

Place these nine CSV files in this folder (`data/`) before running `build_dataset.py`:

| File | Retailer |
|---|---|
| `ae_com.csv` | American Eagle (Aerie) |
| `amazon_com.csv` | Amazon |
| `btemptd_com.csv` | b.tempt'd |
| `calvinklein_com.csv` | Calvin Klein |
| `hankypanky_com.csv` | Hanky Panky |
| `macys_com.csv` | Macy's |
| `shop_nordstrom_com.csv` | Nordstrom |
| `us_topshop_com.csv` | Topshop |
| `victoriassecret_com.csv` | Victoria's Secret |

## Columns used

`retailer`, `product_name`, `brand_name`, `product_category`, `color`, `mrp`, `price`, `rating`, `review_count`, `pdp_url`, `description`.

Each raw row is one product in one color and one size, so the files contain many near-duplicate rows. The cleaning script collapses them to one row per product and color.
