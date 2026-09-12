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

  if tables:
    # Typically the first main table contains the men's or primary champions
    table = tables[0]
    rows = table.find_all("tr")[1:]
    for row in rows:
      cols = row.find_all(["th", "td"])
      if len(cols) >= 5:
        weight = cols[0].get_text(strip=True).split("[")[0]
        wba = cols[1].get_text(strip=True).split("[")[0]
        wbc = cols[2].get_text(strip=True).split("[")[0]
        ibf = cols[3].get_text(strip=True).split("[")[0]
        wbo = cols[4].get_text(strip=True).split("[")[0]
        boxing_data.append({
            "weight": weight,
            "wba": wba,
            "wbc": wbc,
            "ibf": ibf,
            "wbo": wbo,
        })
  return boxing_data


def scrape_ufc():
  url = "https://en.wikipedia.org/wiki/UFC_rankings"
  headers = {"User-Agent": "Mozilla/5.0"}
  response = requests.get(url, headers=headers)
  soup = BeautifulSoup(response.text, "html.parser")

  ufc_data = []
  tables = soup.find_all("table", {"class": "wikitable"})

  # Wikipedia UFC rankings page lists weight classes in separate tables
  for table in tables:
    rows = table.find_all("tr")
    if len(rows) < 3:
      continue

    # Try to extract weight class name from the table header or preceding heading
    weight_name = "Unknown"
    caption = table.find("caption")
    if caption:
      weight_name = caption.get_text(strip=True)
    else:
      prev_h3 = table.find_previous("h3")
      if prev_h3:
        weight_name = (
            prev_h3.find("span", {"class": "mw-headline"})
            .get_text(strip=True)
            .replace("Men's", "")
            .replace("Women's", "")
            .strip()
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

    if weight_name != "Unknown":
      ufc_data.append({
          "weight": weight_name,
          "champion": champion,
          "rankings": rankings[:10],  # Keep top 10
      })

  return ufc_data


if __name__ == "__main__":
  data = {"boxing": scrape_boxing(), "ufc": scrape_ufc()}

  with open("rankings.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)
  print("Successfully updated rankings.json from Wikipedia.")
