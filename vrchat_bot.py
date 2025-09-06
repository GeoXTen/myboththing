import os
import requests
from bs4 import BeautifulSoup

# --- Configuration ---
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
BOOTH_URL = "https://booth.pm/en/browse/VRChat?sort=new"
STATE_FILE = "last_item.txt"

# --- Headers to mimic a real browser ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1'
}

def get_last_seen_id():
    """Reads the last seen item ID from the state file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return f.read().strip()
    return None

def set_last_seen_id(item_id):
    """Writes the new last seen item ID to the state file."""
    with open(STATE_FILE, 'w') as f:
        f.write(str(item_id))

def send_to_discord(item, webhook_url):
    """Sends a new item notification to the Discord webhook."""
    data = {
        # This new line will tag you in the message.
        "content": "<@572614372812390410>",
        "embeds": [
            {
                "title": item["title"],
                "url": item["url"],
                "color": 5814783,  # A nice blue color
                "description": f"**By:** {item['author']}\n**Price:** {item['price']}",
                # Use "image" for a large preview
                "image": {
                    "url": item["image_url"]
                },
                "footer": {
                    "text": "VRChat Booth Notifier"
                }
            }
        ]
    }
    response = requests.post(webhook_url, json=data)
    response.raise_for_status() # Raise an exception for bad status codes
    print(f"Successfully sent notification for item ID: {item['id']}")

def fetch_booth_items():
    """Fetches and parses the latest items from Booth.pm."""
    print("Fetching Booth page...")
    response = requests.get(BOOTH_URL, headers=HEADERS)
    response.raise_for_status()
    print("Page fetched successfully.")

    soup = BeautifulSoup(response.text, 'html.parser')
    items = []
    
    # Use a more robust selector that is less likely to change.
    item_elements = soup.find_all('li', {'data-product-id': True})
    
    print(f"Found {len(item_elements)} item elements.")

    for element in item_elements:
        try:
            item_id = element['data-product-id']
            title_element = element.find('div', class_='item-card__title')
            link_element = title_element.find('a') if title_element else None
            price_element = element.find('div', class_='price')
            author_element = element.find('div', class_='item-card__shop-name')
            # Look for the image inside a noscript tag for reliability
            image_noscript = element.find('noscript')
            image_tag = image_noscript.find('img') if image_noscript else element.find('img')

            if all([item_id, link_element, price_element, author_element, image_tag]):
                items.append({
                    'id': item_id,
                    'title': link_element.text.strip(),
                    'url': link_element['href'],
                    'price': price_element.text.strip(),
                    'author': author_element.text.strip(),
                    'image_url': image_tag['src']
                })
        except Exception as e:
            print(f"Skipping an item due to parsing error: {e}")

    return items

def main():
    if not WEBHOOK_URL:
        print("Error: DISCORD_WEBHOOK_URL environment variable not set.")
        return

    last_seen_id = get_last_seen_id()
    print(f"Last seen item ID: {last_seen_id}")

    try:
        items = fetch_booth_items()
        if not items:
            print("No items found on the page.")
            return

        # Find the index of the last seen item
        last_seen_index = -1
        if last_seen_id:
            for i, item in enumerate(items):
                if item['id'] == last_seen_id:
                    last_seen_index = i
                    break
        
        # Determine which items are new
        new_items = items[:last_seen_index] if last_seen_index != -1 else items
        
        if new_items:
            print(f"Found {len(new_items)} new items.")
            # Reverse to send the oldest new item first
            for item in reversed(new_items):
                send_to_discord(item, WEBHOOK_URL)
            
            # Update the last seen ID to the newest item found on the page
            newest_item_id = items[0]['id']
            set_last_seen_id(newest_item_id)
            print(f"Updated last item ID to: {newest_item_id}")
        else:
            print("No new items found.")
            # If there's no last_seen_id, set it to the newest item on the first run
            if not last_seen_id and items:
                first_run_id = items[0]['id']
                set_last_seen_id(first_run_id)
                print(f"First run. Set last item ID to: {first_run_id}")


    except requests.exceptions.RequestException as e:
        print(f"An error occurred fetching the page: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()

