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

    header_row = rows[0].get_text()
    if "WBA" in header_row and "WBC" in header_row:
      weight_name = "Division"
      prev = table.find_previous(["h3", "h4", "span"])
      if prev:
        headline = prev.find("span", {"class": "mw-headline"})
        weight_name = (
            (headline.get_text() if headline else prev.get_text())
            .split("(")[0]
            .replace("Men's", "")
            .replace("Women's", "")
            .strip()
        )

      for row in rows[1:]:
        cols = row.find_all(["th", "td"])
        if len(cols) >= 5:
          pot_weight = cols[0].get_text(strip=True)
          if (
              "lb" in pot_weight
              or "kg" in pot_weight
              or "Heavyweight" in pot_weight
          ):
            weight_name = pot_weight.split("(")[0].strip()
            wba = cols[1].get_text(strip=True).split("[")[0].split("(")[0].strip()
            wbc = cols[2].get_text(strip=True).split("[")[0].split("(")[0].strip()
            ibf = cols[3].get_text(strip=True).split("[")[0].split("(")[0].strip()
            wbo = cols[4].get_text(strip=True).split("[")[0].split("(")[0].strip()
          else:
            wba = cols[0].get_text(strip=True).split("[")[0].split("(")[0].strip()
            wbc = cols[1].get_text(strip=True).split("[")[0].split("(")[0].strip()
            ibf = cols[2].get_text(strip=True).split("[")[0].split("(")[0].strip()
            wbo = cols[3].get_text(strip=True).split("[")[0].split("(")[0].strip()

          boxing_data.append({
              "weight": weight_name,
              "wba": wba,
              "wbc": wbc,
              "ibf": ibf,
              "wbo": wbo,
          })
          break
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
      prev = table.find_previous(["h3", "h4", "span"])
      if prev:
        headline = prev.find("span", {"class": "mw-headline"})
        weight_name = (
            (headline.get_text() if headline else prev.get_text())
            .replace("Men's", "")
            .replace("Women's", "")
            .strip()
        )

    champion = "Vacant"
    rankings = []

    for row in rows:
      text = row.get_text()
      cols = row.find_all(["th", "td"])
      if "C" in row.get_text() and len(cols) > 1:
        # Check if it's the champion row
        cell_text = cols[0].get_text(strip=True)
        if cell_text == "C" or "C" in cell_text:
          champion = cols[1].get_text(strip=True).split("[")[0].strip()
      
      if len(cols) >= 2:
        fighter_name = cols[1].get_text(strip=True).split("[")[0].strip()
        rank_text = cols[0].get_text(strip=True)
        if rank_text.isdigit():
          if fighter_name and fighter_name != champion:
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
  print("Successfully updated rankings.json matching frontend layout.")
