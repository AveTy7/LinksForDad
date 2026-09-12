import json
import requests
from bs4 import BeautifulSoup


def scrape_boxing():
  url = "https://en.wikipedia.org/wiki/List_of_current_world_boxing_champions"
  headers = {"User-Agent": "Mozilla/5.0"}
  response = requests.get(url, headers=headers)
  soup = BeautifulSoup(response.text, "html.parser")

  boxing_data = []
  tables = soup.find_all("table", {"class": "wikitable"})

  for table in tables:
    rows = table.find_all("tr")
    if len(rows) < 2:
      continue

    # Identify weight class from the preceding h3 or table headers
    weight_name = "Unknown"
    prev_h3 = table.find_previous(["h3", "h4", "span"])
    if prev_h3:
      headline = prev_h3.find("span", {"class": "mw-headline"})
      if headline:
        weight_name = headline.get_text(strip=True)
      else:
        weight_name = prev_h3.get_text(strip=True)

    # Clean up weight name string
    weight_name = (
        weight_name.split("(")[0]
        .replace("Men's", "")
        .replace("Women's", "")
        .strip()
    )

    # Check if this table actually contains champion organizations (WBA, WBC, etc.)
    header_row = rows[0].get_text()
    if "WBA" in header_row and "WBC" in header_row:
      # Look for the row containing the primary champions
      for row in rows[1:]:
        cols = row.find_all(["th", "td"])
        # Standard layout has 5+ columns: Division/Notes + 4 major bodies
        if len(cols) >= 5:
          wba = cols[0].get_text(strip=True).split("[")[0]
          wbc = cols[1].get_text(strip=True).split("[")[0]
          ibf = cols[2].get_text(strip=True).split("[")[0]
          wbo = cols[3].get_text(strip=True).split("[")[0]

          # Sometimes the weight name is embedded in the first column
          potential_weight = cols[0].get_text(strip=True)
          if (
              "lb" in potential_weight
              or "kg" in potential_weight
              or "Heavyweight" in potential_weight
          ):
            weight_name = potential_weight.split("(")[0].strip()
            wba = cols[1].get_text(strip=True).split("[")[0]
            wbc = cols[2].get_text(strip=True).split("[")[0]
            ibf = cols[3].get_text(strip=True).split("[")[0]
            wbo = cols[4].get_text(strip=True).split("[")[0]

          boxing_data.append({
              "weight": weight_name if weight_name else "Division",
              "wba": wba,
              "wbc": wbc,
              "ibf": ibf,
              "wbo": wbo,
          })
          break  # Found the champion row for this table

  return boxing_data


def scrape_ufc():
  url = "https://en.wikipedia.org/wiki/UFC_rankings"
  headers = {"User-Agent": "Mozilla/5.0"}
  response = requests.get(url, headers=headers)
  soup = BeautifulSoup(response.text, "html.parser")

  ufc_data = []
  tables = soup.find_all("table", {"class": "wikitable"})

  for table in tables:
    rows = table.find_all("tr")
    if len(rows) < 3:
      continue

    weight_name = "Unknown"
    caption = table.find("caption")
    if caption:
      weight_name = caption.get_text(strip=True)
    else:
      prev_h3 = table.find_previous(["h3", "h4", "span"])
      if prev_h3:
        headline = prev_h3.find("span", {"class": "mw-headline"})
        if headline:
          weight_name = headline.get_text(strip=True)
        else:
          weight_name = prev_h3.get_text(strip=True)

        weight_name = (
            weight_name.replace("Men's", "").replace("Women's", "").strip()
        )

    champion = "Vacant"
    rankings = []

    for row in rows:
      text = row.get_text()
      if "Champion" in text:
        cols = row.find_all(["th", "td"])
        if len(cols) > 1:
          champion = cols[1].get_text(strip=True).split("[")[0]
      else:
        cols = row.find_all(["th", "td"])
        if len(cols) >= 2:
          fighter_name = cols[1].get_text(strip=True).split("[")[0]
          if (
              fighter_name
              and fighter_name != "Fighter"
              and fighter_name != champion
          ):
            rankings.append(fighter_name)

    if weight_name and weight_name != "Unknown":
      ufc_data.append({
          "weight": weight_name,
          "champion": champion,
          "rankings": rankings[:10],
      })

  return ufc_data


if __name__ == "__main__":
  data = {"boxing": scrape_boxing(), "ufc": scrape_ufc()}

  with open("rankings.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)
  print("Successfully updated rankings.json from Wikipedia.")
