# Innerwear Pricing Intelligence

Python and Power BI analysis of **33.7K innerwear listings across 9 US retailers** (June–July 2017).

## Project Overview

This project explores how innerwear brands position their products through pricing, discounting, retail channels, colors, and product descriptions.

**Key Questions**
- Which brands position themselves at a premium?
- Which brands rely more heavily on discounts?
- Does the same brand have consistent pricing across retail channels?
- What colors and descriptive language characterize each brand?
- Is there a relationship between product prices and customer ratings?

**Note:** These are listing prices, not actual sales. The analysis reflects how brands position and discount their products, not which products sell best.

## Dashboard

**[View Full Dashboard – Retail Analytics Dashboard (PDF)](Retail%20Analytics%20Dashboard.pdf)**

The Power BI report includes eight pages:

| Page | What It Shows |
|---|---|
| Home | Key metrics and dashboard navigation |
| Price Positioning | Median prices and price distributions by brand |
| Discounting | Share of discounted listings and average markdowns |
| Channels | Brand pricing comparisons across retail channels and categories |
| Color & Language | Color preferences and frequently used product-description keywords |
| Price vs. Rating | Relationships between listing prices and customer ratings |
| Brand Profile | Detailed drill-through analysis for individual brands |
| Methodology | Data cleaning procedures and analytical limitations |

## Key Findings

### 1. Brand Price Positioning

Wacoal had the highest overall median listing price (approximately $50), while Aerie was among the lowest (approximately $16). Within the bras category, Hanky Panky had a slightly higher median price (~$57) than Wacoal (~$54), although the sample was smaller.

### 2. Discounting Strategies

Aerie discounted approximately 66% of its listings, with an average markdown of 39%. In contrast, Hanky Panky discounted only about 3%. Victoria's Secret discounted 35% of listings but had the deepest average markdown among major brands (~47%).

### 3. Retail Channel Pricing

Price differences across channels became much smaller when comparing products within the same category. For example, Calvin Klein bra prices remained between $36 and $42 across channels. Wacoal panties showed a clearer difference, with a median price of approximately $26 on Amazon versus $15–$17.50 at Macy's and Nordstrom.

### 4. Color & Product Language

Although black was common across all brands, each brand showed distinctive color preferences. Aerie leaned toward blue (24% of named colors), Wacoal toward nude (25%), and Topshop toward pink (24%). Product descriptions also reflected different brand identities: Wacoal emphasized support and underwire, while Aerie used words such as "real," "soft," and "comfy." Hanky Panky emphasized lace and its signature line.

### 5. Price vs. Customer Ratings

Across the 10 brands, the correlation between brand-level median prices and average ratings was approximately 0.5. However, within individual brands, correlations were weak or negative (-0.32 to +0.15). Across all listings, the relationship was essentially zero (0.01).

Ratings were available for only 65% of listings.

## Data Source

**Source:** PromptCloud, Kaggle – *Innerwear Data from Victoria's Secret and Others*.

The dataset contains nine retailer files:

- Amazon
- American Eagle (Aerie)
- b.tempt'd
- Calvin Klein
- Hanky Panky
- Macy's
- Nordstrom
- Topshop
- Victoria's Secret

The original raw CSV files are not included because of their size and redistribution restrictions. Victoria's Secret's raw file alone is approximately 390 MB. See [`data/README.md`](data/README.md) for download instructions.

**Data Granularity**
- Raw data: One row per product, color, and size.
- Cleaned data: One row per product and color.

## Data Cleaning & Processing

`build_dataset.py` processes the nine raw CSV files into a consolidated Excel workbook containing two tables: `listings` and `keywords`.

### Data Processing Summary

| Processing Stage | Rows |
|---|---:|
| Raw records | 613,143 |
| After removing duplicate rows | 82,996 |
| Product-color listings (12,298 product pages) | 34,307 |
| Final dataset after removing 575 multi-pack listings | 33,732 |

### Key Cleaning Steps

- **Prices
