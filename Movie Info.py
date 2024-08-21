import requests
import json
import csv
import time

# Function to flatten movie data
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
                "VistaCinemaId": showtime.get("VistaCinemaId", ""),
                "CinemaId": showtime.get("CinemaId", ""),
                "CinemaName": cinema_name,
                "Movie_order_link": f"https://compra.cinepolis.com/?cinemaVistaId={showtime.get('VistaCinemaId')}&showtimeVistaId={showtime.get('ShowtimeId')}&countryCode=CL"
            })
    return flattened_data

# Function to fetch data
def fetch_data(city_code, referer, max_retries=5):
    url = "https://cinepolischile.cl/Cartelera.aspx/GetNowPlayingByCity"
    payload = {"claveCiudad": city_code, "esVIP": False}
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-IN,en;q=0.9,kn-IN;q=0.8,kn;q=0.7,en-GB;q=0.6,en-US;q=0.5',
        'Origin': 'https://cinepolischile.cl',
        'Referer': referer,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }

    retry_count = 0
    while retry_count < max_retries:
        try:
            response = requests.post(url, json=payload, headers=headers)
            print(f"Status Code: {response.status_code} for {city_code}")

            if response.status_code == 200:
                return response.json()

            elif response.status_code == 403:
                retry_count += 1
                print(f"Error 403. Retrying ({retry_count}/{max_retries})...")
                time.sleep(2)  # wait for 2 seconds before retrying
            else:
                print(f"Failed to fetch data. Status code: {response.status_code}")
                break

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            retry_count += 1
            time.sleep(2)

    return None

# Function to save data to CSV
def save_to_csv(data_list, csv_file_path='cinepolis_movie_data.csv'):
    if not data_list:
        print("No data to save.")
        return

    keys = data_list[0].keys()
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data_list)
    print(f"Data successfully written to {csv_file_path}")

if __name__ == "__main__":
    city_referer_pairs = {
        # "santiago-poniente-y-norte": "https://cinepolischile.cl/cartelera/santiago-poniente-y-norte/",
        "sur-de-chile": "https://cinepolischile.cl/cartelera/sur-de-chile/",
        # "santiago-sur": "https://cinepolischile.cl/cartelera/santiago-sur/",
        # "santiago-oriente": "https://cinepolischile.cl/cartelera/santiago-oriente/",
        # "santiago-centro": "https://cinepolischile.cl/cartelera/santiago-centro/",
        # "norte-y-centro-de-chile": "https://cinepolischile.cl/cartelera/norte-y-centro-de-chile/",
    }

    all_data = []

    for city_code, referer in city_referer_pairs.items():
        json_data = fetch_data(city_code, referer)
        if json_data:
            cinemas = json_data.get("d", {}).get("Cinemas", [])
            for cinema in cinemas:
                for date in cinema.get("Dates", []):
                    movies = date.get("Movies", [])
                    for movie in movies:
                        all_data.extend(flatten_movie_data(movie, cinemas))

    save_to_csv(all_data)
