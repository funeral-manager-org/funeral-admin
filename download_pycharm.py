import requests
def main():
    url = "https://download.jetbrains.com/python/pycharm-professional-2024.1.4.exe"
    output_file = "H:\\projects\\source\\pycharm-professional-2024.1.4.exe"

    try:
        # Send GET request
        response = requests.get(url, stream=True, verify=False)
        response.raise_for_status()  # Raise an error for bad status codes

        # Write the content to a file
        with open(output_file, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"Downloaded file saved to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
