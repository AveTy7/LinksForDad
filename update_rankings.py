import json
import re
import requests
from bs4 import BeautifulSoup


def clean_text(text):
  if not text:
    return ""
  # Remove Wikipedia citation brackets like [1]
  text = re.sub(r"\[\d+\]", "", text)
  # Remove dates like "July 1, 2026" or "December 13, 2025"
  text = re.sub(
      r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
      "",
      text,
  )
  # Clean up trailing parentheses or extra dashes left behind from date removal
  text = re.sub(r"\s*-\s*$", "", text)
  text = re.sub(r"\s*\(\s*\)", "", text)
  return text.strip()


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
        raw_head = headline.get_text() if headline else prev.get_text()
        weight_name = (
            raw_head.split("(")[0]
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
              or "Cruiserweight" in pot_weight
              or "Middleweight" in pot_weight
          ):
            weight_name = pot_weight.split("(")[0].strip()
            wba = clean_text(cols[1].get_text(strip=True))
            wbc = clean_text(cols[2].get_text(strip=True))
            ibf = clean_text(cols[3].get_text(strip=True))
            wbo = clean_text(cols[4].get_text(strip=True))
          else:
            wba = clean_text(cols[0].get_text(strip=True))
            wbc = clean_text(cols[1].get_text(strip=True))
            ibf = clean_text(cols[2].get_text(strip=True))
            wbo = clean_text(cols[3].get_text(strip=True))

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

    weight_name = ""
    caption = table.find("caption")
    if caption:
      weight_name = caption.get_text(strip=True)
    else:
      prev = table.find_previous(["h3", "h4", "span"])
      if prev:
        headline = prev.find("span", {"class": "mw-headline"})
        raw_head = headline.get_text() if headline else prev.get_text()
        weight_name = (
            raw_head.replace("Men's", "")
            .replace("Women's", "")
            .replace("rankings", "")
            .strip()
        )

    if not weight_name or weight_name.lower() in [
        "pound-for-pound",
        "pound for pound",
    ]:
      continue

    champion = "Vacant"
    rankings = []

    for row in rows:
      cols = row.find_all(["th", "td"])
      row_text = row.get_text()

      if len(cols) >= 2:
        rank_text = cols[0].get_text(strip=True)
        fighter_name = clean_text(cols[1].get_text(strip=True))

        if "C" == rank_text or rank_text.startswith("C\n") or "Champion" in row_text:
          if fighter_name and fighter_name != "Fighter":
            champion = fighter_name
        elif rank_text.isdigit():
          if fighter_name and fighter_name != champion:
            rankings.append(fighter_name)

    if weight_name:
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
  print("Successfully updated rankings.json with cleaned data.")
