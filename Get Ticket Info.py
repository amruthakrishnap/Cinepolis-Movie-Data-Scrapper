import csv
import asyncio
import time
from playwright.async_api import async_playwright

async def fetch_ticket_prices(page, url):
    await page.goto(url, timeout=60000)
    await page.wait_for_timeout(5000)

    print("Entered to Scrape:")
    
    # Capture both responses
    responses = []
    print(response)

    async def capture_response(response):
        if 'tickets' in response.url:
            responses.append(response)
            if len(responses) == 2:  # We expect two responses
                return
            await response.body()  # Ensure we capture the body

    # Set up response capturing
    page.on('response', capture_response)

    # Navigate to the page
    await page.goto(url, timeout=60000)
    
    # Wait for both responses to be captured
    while len(responses) < 2:
        await page.wait_for_timeout(1000)
    
    # Process responses
    ticket_info = {}
    
    for response in responses:
        if response.status == 200:
            data = await response.json()
            print(data)
            
            # Extract data if not empty
            if data:
                for area in data.get("areas", []):
                    for ticket in area.get("tickets", []):
                        ticket_info[ticket["description"]] = ticket["price"]
    
    return ticket_info

async def main():
    csv_file_path = 'data.csv'
    updated_csv_file_path = 'updated_data.csv'
    data_list = []
    seen_combinations = {}

    async with async_playwright() as p:
        user_data_path = '/Users/amruthakrishna/documents/chrome/AKP/Default'
        context = await p.chromium.launch_persistent_context(user_data_path, channel='chromium', headless=False)
        page = context.pages[0]
        # Read the existing CSV file
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                combination_key = (row["Name"], row["CinemaName"], row["Title"], row["CinemaId"])
                if combination_key in seen_combinations:
                    row.update(seen_combinations[combination_key])
                else:
                    try:
                        ticket_prices = await fetch_ticket_prices(page, row["Movie_order_link"])
                        row.update(ticket_prices)
                        seen_combinations[combination_key] = ticket_prices
                    except Exception as e:
                        print(f"Error fetching ticket prices for {combination_key}: {e}")
                data_list.append(row)

        await page.close()

        # Write the updated data to a new CSV file
        if data_list:
            keys = data_list[0].keys()
            with open(updated_csv_file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data_list)
            print(f"Data successfully written to {updated_csv_file_path}")
        else:
            print("No data to write to CSV.")

asyncio.run(main())
