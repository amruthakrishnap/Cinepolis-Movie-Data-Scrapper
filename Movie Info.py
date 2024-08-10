from playwright.async_api import async_playwright
import json
import asyncio
import csv

def flatten_movie_data(movie, cinemas):
    flattened_data = []
    for format_ in movie.get("Formats", []):
        for showtime in format_.get("Showtimes", []):
            cinema_id = showtime.get("CinemaId")
            cinema_name = next((c['Name'] for c in cinemas if c['Id'] == cinema_id), "")
            flattened_data.append({
                "Title": movie.get("Title", ""),
                "Rating": movie.get("Rating", ""),
                "RunTime": movie.get("RunTime", ""),
                "Poster": movie.get("Poster", ""),
                "Trailer": movie.get("Trailer", ""),
                "Director": movie.get("Director", ""),
                "Actors": ", ".join(movie.get("Actors", [])),
                "Name": format_.get("Name", ""),
                "ShowtimeId": showtime.get("ShowtimeId", ""),
                "ShowtimeAMPM": showtime.get("ShowtimeAMPM", ""),
                "VistaCinemaId":showtime.get("VistaCinemaId", ""),
                "CinemaId": showtime.get("CinemaId", ""),
                "CinemaName": cinema_name,
                "Movie_order_link": f"https://compra.cinepolis.com/?cinemaVistaId={showtime.get('VistaCinemaId')}&showtimeVistaId={showtime.get('ShowtimeId')}&countryCode=CL"
            })
    return flattened_data

async def extract_data_from_page(page, data_list):
    async def handle_response(response):
        if response.status == 200 and "GetNowPlayingByCity" in response.url:
            try:
                json_data = await response.json()
                cinemas = json_data.get("d", {}).get("Cinemas", [])
                for cinema in cinemas:
                    for date in cinema.get("Dates", []):
                        movies = date.get("Movies", [])
                        for movie in movies:
                            data_list.extend(flatten_movie_data(movie, cinemas))
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")

    page.on('response', handle_response)
    await page.goto("https://cinepolischile.cl/cartelera/sur-de-chile", timeout=60000)
    await page.wait_for_timeout(5000)

async def main():
    max_retries = 3
    retry_count = 0
    data_list = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        while retry_count < max_retries:
            try:
                page = await browser.new_page()
                if await extract_data_from_page(page, data_list):
                    break
                else:
                    retry_count += 1
                    print(f"Retrying ({retry_count}/{max_retries})...")
                    await page.close()
            except Exception as e:
                print(f"Exception occurred: {e}")
                retry_count += 1
                print(f"Retrying ({retry_count}/{max_retries})...")
                if not page.is_closed():
                    await page.close()
        await browser.close()

        csv_file_path = 'data.csv'

        if data_list:
            keys = data_list[0].keys()
            with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data_list)
            print(f"Data successfully written to {csv_file_path}")
        else:
            print("No data to write to CSV.")

asyncio.run(main())
