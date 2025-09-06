import requests
import json
import os
from bs4 import BeautifulSoup

# --- Configuration ---
# The webhook URL will be pulled from GitHub Secrets, not written here.
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

BOOTH_URL = "https://booth.pm/en/browse/VRChat?sort=new"
STATE_FILE = "last_item.txt"
# --- End of Configuration ---


def send_to_discord(item):
    """Sends a new item notification to the Discord webhook."""
    embed = {
        "title": item['title'],
        "url": item['url'],
        "color": 5814783,
        "description": f"**By:** {item['author']}\n**Price:** {item['price']}",
        "image": {"url": item['image_url']},
        "footer": {"text": "VRChat Booth Notifier"}
    }
    payload = {"embeds": [embed]}
    try:
        response = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        response.raise_for_status()
        print(f"Successfully sent notification for: {item['title']}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Discord: {e}")


def get_last_id():
    """Reads the last known item ID from the state file."""
    try:
        with open(STATE_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def set_last_id(item_id):
    """Writes the new latest item ID to the state file."""
    with open(STATE_FILE, 'w') as f:
        f.write(str(item_id))


def main():
    """Main function to run the bot."""
    if not WEBHOOK_URL:
        print("CRITICAL ERROR: DISCORD_WEBHOOK_URL is not set in GitHub Secrets.")
        return

    last_id = get_last_id()
    newest_id_found = None
    new_items = []

    print(f"Checking for new items... Last known ID is: {last_id}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        response = requests.get(BOOTH_URL, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Booth page: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    item_elements = soup.find_all('li', attrs={'data-product-id': True})

    if not item_elements:
        print("Could not find item cards on the page.")
        return

    for item_element in item_elements:
        item_id = item_element['data-product-id']

        if not newest_id_found:
            newest_id_found = item_id

        if item_id == last_id:
            break

        title_element = item_element.find('div', class_='item-card__title').find('a')
        new_items.append({
            'id': item_id,
            'title': title_element.text.strip(),
            'url': "https://booth.pm" + title_element['href'],
            'price': item_element.find('div', class_='price').text.strip(),
            'author': item_element.find('div', class_='item-card__shop-name').text.strip(),
            'image_url': (item_element.find('img').get('data-src') or item_element.find('img').get('src'))
        })

    if new_items:
        print(f"Found {len(new_items)} new items. Posting to Discord.")
        for item in reversed(new_items):
            send_to_discord(item)
        
        set_last_id(newest_id_found)
        print(f"Updated last item ID to: {newest_id_found}")
    else:
        print("No new items found.")


if __name__ == "__main__":
    main()
