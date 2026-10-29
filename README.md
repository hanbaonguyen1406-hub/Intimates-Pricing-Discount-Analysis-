Innerwear Pricing Intelligence

Python and Power BI analysis of 33.7K innerwear listings from 9 US retailers (June to July 2017).

Questions: Which brands are premium? Which ones rely on discounts? Does the same brand cost the same on every channel? What colors and words does each brand sell with?

These are listing prices, not sales. The data says how brands position and discount their products, not which ones sell best.

Home page
Key findings

1."Premium" depends on what you compare. Across all listings Wacoal has the highest median price (about $50) and Aerie one of the lowest (about $16). Within bras only, Hanky Panky (about $57) edges ahead of Wacoal (about $54), on a small sample.

2.Discounting differs sharply. Aerie puts about two in three listings on sale (66%, average markdown 39%), Hanky Panky about 3%. Victoria's Secret discounts 35% of listings but cuts deepest among the large brands (about 47% off).

3.Channels look different only when you mix categories. Within one category, prices for the same brand are close across channels (Calvin Klein bras stay between $36 and $42 everywhere). The clearest gap is Wacoal panties: about $26 on Amazon against $15 to $17.50 at Macy's and Nordstrom. Without a category filter Calvin Klein looks like $33 on Amazon against $13 on its own site, but that is mostly a difference in product mix.

4.Every brand sells black, but each has a signature color. Aerie leans blue (24% of named colors), Wacoal nude (25%), Topshop pink (24%); Calvin Klein is the blackest brand (32%). Descriptions differ too: Wacoal talks about support and underwire, Aerie about "real", soft and comfy, Hanky Panky about lace and its signature line.

5.Price does not predict rating. Across the 10 brands, pricier brands rate slightly higher (correlation about 0.5). Inside a brand the link is weak or negative (from -0.32 to +0.15), and across all listings it is essentially zero (0.01). Ratings exist for only 65% of listings.

Dashboard

Page      	        What it shows
Home	              Key numbers and a table of contents
Price positioning	  Median price by brand, price spread (P25 to P75), median/average toggle
Discounting	        Share of listings on sale, by brand and by channel
Channels	          Same brand, different channel: price and premium vs the brand median, by category
Color & language	  Color mix by brand and top description keywords
Price vs rating	    Brand-level and within-brand relationship between price and rating
Brand profile	      Drill-through page for one brand
Methodology	        How the data was cleaned and what it cannot tell you

Screenshots: Price positioning · Discounting · Channels · Color & language · Price vs rating · Brand profile · Methodology

The dashboard was built in the Power BI service on top of output/fashion_powerbi.xlsx. The report file is in dashboard/ (open it with Power BI Desktop, which runs on Windows).

Data
Source: PromptCloud data on Kaggle, "Innerwear Data from Victoria's Secret and Others". Nine files, one per retailer: Amazon, American Eagle (Aerie), b.tempt'd, Calvin Klein, Hanky Panky, Macy's, Nordstrom, Topshop and Victoria's Secret.
Not included in this repository. The raw files are large (Victoria's Secret alone is about 390 MB) and are not mine to redistribute. See data/README.md for where to get them.
Raw grain: one row per product, color and size. Clean grain: one row per product and color.
Cleaning pipeline

build_dataset.py turns the nine raw files into one Excel workbook with two tables (listings and keywords).

Step	                                         Rows
Raw rows (one per product, color and size)	   613,143
After removing duplicate rows	                 82,996
Product-color listings (12,298 product pages)	 34,307
After removing 575 multi-pack listings	       33,732

Prices: four text formats (single price, range, USD text, "was/now") parsed into numbers.
Brands: 33 spellings merged into 10 brands.
Categories: 525 labels grouped into 6, classifying by product name first.
Colors: names mapped to 12 color families.
Retailers: renamed so brand sites and department stores are easy to tell apart.

Problems found and fixed
Every Macy's item was filed under Shapewear. Macy's category paths start with "Lingerie & Shapewear", which matched the word "shapewear". The prefix is now stripped and the product name is checked first.
The b.tempt'd site labels its own line as "WACOAL". Relabelled by channel so the two brands are not mixed.
Amazon stores sizes in the color column. Set to empty before grouping colors.
Multi-packs distort prices (for example a 30-pack of thongs). 575 listings removed.

Limitations
Listing prices, not sales or popularity.
June to July 2017 only, so there is no time trend.
About 18% of listings use brand-style color names (for example "night" or "dusk") that cannot be mapped to a color family. The color chart excludes them, and also leaves out b.tempt'd, whose names mostly fall into that group. Calvin Klein (29% unmapped) and PINK (25%) are included but approximate.
Ratings exist for 65% of listings: 0% on the Calvin Klein and b.tempt'd sites, 9% on Topshop. Brand averages are not strictly comparable.
Swimwear is about 0.6% of listings, so this is effectively an innerwear dataset.
Nordstrom Lingerie (74 listings) and Vanity Fair (226) are small samples.
A brand may not carry the same styles on every channel.

Reproduce
bash
pip install pandas openpyxl
# put the nine raw CSV files in a folder called data/
python build_dataset.py
The workbook is written to output/fashion_powerbi.xlsx.

Tools
Python (pandas, openpyxl), Power BI (DAX measures, bookmarks, drill-through).

Repository structure
README.md
build_dataset.py
data/README.md        where to download the raw data
output/               cleaned workbook used by the dashboard
screenshots/          dashboard pages
License

The code is released under the MIT license. The underlying data belongs to its original sources (PromptCloud and the retailers).
