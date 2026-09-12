import json
import re
import requests
from bs4 import BeautifulSoup


def clean_text(text):
  if not text:
    return ""
  text = re.sub(r"\[\d+\]", "", text)
  text = re.sub(
      r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
      "",
      text,
  )
  return text.strip()


def format_fighter_cell(cell_text):
  cleaned = clean_text(cell_text)
  if not cleaned or cleaned.lower() == "vacant":
    return "vacant"

  is_super = False
  if "super champion" in cleaned.lower():
    is_super = True
    cleaned = re.sub(r"super champion", "", cleaned, flags=re.IGNORECASE)

  match = re.search(
      r"(\d+\s*[-–]\s*\d+(?:\s*[-–]\s*\d+)?(?:\s*\(\s*\d+\s*\))?)", cleaned
  )
  record = ""
  if match:
    record = match.group(1).strip()
    cleaned = cleaned.replace(record, "").strip()

  name = re.sub(r"\s*\(.*?\)", "", cleaned).strip()
  if not name:
    return cleaned

  super_badge = (
      ' <span style="color: #fbbf24; font-size: 0.85em;" title="Super'
      ' Champion">★</span>'
      if is_super
      else ""
  )

  if record:
    return f"{name}{super_badge}<br>{record}"
  return f"{name}{super_badge}"


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
      prev = table.find_previous(["h3", "h4", "span", "th"])
      while prev:
        headline = (
            prev.find("span", {"class": "mw-headline"})
            if hasattr(prev, "find")
            else None
        )
        raw_head = headline.get_text() if headline else prev.get_text()
        if raw_head and any(
            w in raw_head
            for w in [
                "weight",
                "Heavy",
                "Cruiser",
                "Light",
                "Middle",
                "Welter",
                "Feather",
                "Bantam",
                "Fly",
                "Straw",
            ]
        ):
          weight_name = (
              raw_head.split("(")[0]
              .replace("Men's", "")
              .replace("Women's", "")
              .strip()
          )
          break
        prev = prev.find_previous(["h3", "h4", "span", "th"])

      for row in rows[1:]:
        cols = row.find_all(["th", "td"])
        if len(cols) >= 5:
          pot_weight = cols[0].get_text(strip=True)
          if any(
              term in pot_weight
              for term in [
                  "lb",
                  "kg",
                  "Heavyweight",
                  "Cruiserweight",
                  "Middleweight",
                  "Welterweight",
                  "Light",
                  "Featherweight",
                  "Bantamweight",
                  "Flyweight",
                  "Strawweight",
              ]
          ):
            weight_name = pot_weight.split("(")[0].strip()
            wba = format_fighter_cell(cols[1].get_text(strip=True))
            wbc = format_fighter_cell(cols[2].get_text(strip=True))
            ibf = format_fighter_cell(cols[3].get_text(strip=True))
            wbo = format_fighter_cell(cols[4].get_text(strip=True))
          else:
            wba = format_fighter_cell(cols[0].get_text(strip=True))
            wbc = format_fighter_cell(cols[1].get_text(strip=True))
            ibf = format_fighter_cell(cols[2].get_text(strip=True))
            wbo = format_fighter_cell(cols[3].get_text(strip=True))

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
      if len(cols) >= 2:
        rank_text = cols[0].get_text(strip=True)
        fighter_name = clean_text(cols[1].get_text(strip=True))

        # Check if the row represents the champion
        if rank_text in ["C", "IC"] or "C" == rank_text:
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
  print("Successfully updated rankings.json with restored UFC structure.")
