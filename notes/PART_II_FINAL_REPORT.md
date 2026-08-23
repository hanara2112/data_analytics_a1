# Final Report: NYC Airbnb Listings

## Data and approach

I started with 30,259 Airbnb listings from New York City in June 2026. Only
21,515 listings, or 71.1%, have a usable nightly price. Most missing prices
come from the older scrape source, so I left them missing. I cleaned the
dates, prices, booleans, and amenities without dropping rows or hiding unusual
prices. Questions that did not need price used all listings.

## 1. Price Segmentation & Market Overview

The three price tiers describe different parts of the market. Budget listings
cost up to $121.18, Mid-range listings cost above $121.18 and up to $247.47,
and Premium listings cost above $247.47. Their median prices are about $75,
$175, and $396. A typical Premium
listing accommodates four guests and lists 35 amenities, compared with two
guests and 26 amenities in Budget. Premium supply is also concentrated in
Manhattan, which contains 64.6% of that tier.

## 2. City-Level Comparative Analysis: Manhattan vs Brooklyn

Manhattan stays more expensive when I compare it fairly with Brooklyn. Entire
homes have median prices of $262 in Manhattan and $198 in Brooklyn, while
private rooms have medians of $154 and $92. Median capacity is three guests
for entire homes, two for private rooms, and one for shared rooms in both
boroughs. The mix of properties is still different: entire rental units make
up 59.5% of Manhattan's residential market but 37.3% of Brooklyn's. Hotel
rooms are a small segment, with median prices of $474 and $399.

## 3. Location-Based Premium Analysis

Location remains important even within each borough. I called a neighborhood
prime when its median price was in the top quarter for that borough. Prime
neighborhoods have a higher median price per guest in all five boroughs. The
gap remains when entire homes and private rooms are compared separately,
ranging from 16% for Queens entire homes to 79% for Manhattan private rooms.
Amenity counts change little, although prime listings can accommodate more
guests in some boroughs. Location matters, but it is not the only difference.

## 4. Value-for-Money Opportunities

For a budget-conscious guest, I measured value as the number of guests
accommodated per $100. The highest individual scores often depend on unusually
low prices and need to be checked before calling them genuine deals. Some
Bronx and Staten Island groups have the highest numerical scores, but they are
small. Queens entire homes for five or more guests stand out as the more
convincing market opportunity because the result covers 424 listings, with a
median value of 2.89 guests per $100.

## 5. Feature & Amenity Impact on Price

Pools and gyms initially show price differences of about 121% and 119%. When
I compare listings in the same borough and room type, those gaps fall to about
45% and 44%. The differences are about 26% for pets allowed, 11% for
elevators, and 4% for hot tubs. Superhost listings cost more in Brooklyn and
Queens but less in Manhattan. These patterns do not prove that the features
caused the price differences.

## 6. Timeline & Readiness Effect on Pricing

Availability and listing age do not give one simple pricing rule. Among
listings requiring at least 30 nights, readily available homes are more
expensive than listings with no availability: roughly $150 versus $110 in
Brooklyn and $266 versus $171 in Manhattan. Short-stay listings are generally
more expensive, but price does not rise steadily with availability. Older
listings are not always more expensive, and some unreviewed listings are
costly. Zero availability can also mean blocked dates rather than a fully
booked listing.

## 7. Host ("Developer") Impact on Listings

Larger host portfolios contain more high-priced inventory. Hosts with
21 or more listings have the highest median price at $220 and the largest
Premium share at 42.6%. Their median amenity count is 29, so they do not show
a clear advantage in the number of amenities. Their listings are 64.4% entire
homes and 5.7% hotel rooms. The price pattern remains when each host is given
equal weight, although some large hosts have prices for only a small share of
their listings.

## Overall conclusion

Overall, the strongest differences are linked to location and listing type.
Manhattan and prime neighborhoods cost more, Queens gives a convincing balance
of capacity and price, and large hosts manage more Premium listings without
clearly offering more amenities. These conclusions come from one market
snapshot. Listed prices are not completed bookings, availability is not
occupancy, and the results describe relationships rather than causes.
