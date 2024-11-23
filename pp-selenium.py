from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from datetime import datetime
import time
import math
import json
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from pprint import pprint
import re
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
import random
import subprocess
import json
import pandas as pd
import matplotlib.pyplot as plt
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def click_modal_button(driver):
    """
    Locates the first button underneath a modal div with the attributes:
    role="dialog", aria-modal="true", and aria-labelledby="modal-headline".
    If the button exists, it clicks it.

    Args:
        driver (selenium.webdriver): The Selenium WebDriver instance.

    Returns:
        bool: True if the button was found and clicked, False otherwise.
    """
    try:
        # Locate the modal div with the specified attributes
        modal_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH, "//div[@role='dialog' and @aria-modal='true' and @aria-labelledby='modal-headline']"
            ))
        )
        
        # Locate the first button inside the modal div
        button = modal_div.find_element(By.TAG_NAME, "button")
        
        # Scroll into view if necessary
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        
        # Click the button
        button.click()
        print("Modal button clicked successfully.")
        return True
    except Exception as e:
        print(f"Error clicking the modal button: {e}")
        return False


# Function to process the HTML and extract matching pairs
def process_html(page_source):
    soup = BeautifulSoup(page_source, "html.parser")
    pairs = []


    # Find all matching elements based on the structure
    bet_containers = soup.select(".w-full.mx-auto.mt-2.text-center.text-black")
    for bet_container in bet_containers:

        row = bet_container.select(".flex.flex-row.items-center.mt-2.justify-evenly")[0]
        # buttons = row.find_all("button")
        buttons = row.find_all("button")
        if len(buttons) == 2:  # Ensure there are exactly two buttons
            multipliers = []
            skip_row = False
            for button in buttons:
                # Check for multiplier and associated boost arrow
                text = button.get_text(strip=True).strip()
                if "x" in text:
                    try:
                        multiplier = float(text.replace("x", ""))
                        # Check if there's a boost arrow next to this multiplier
                        boost_arrow = button.find_next_sibling("div")
                        if boost_arrow and boost_arrow.find("img", {"src": "/icons/pp_arrow_promo.svg"}):
                            skip_row = True
                            break
                        multipliers.append(multiplier)
                    except ValueError:
                        continue

            # Get the parent element's text
            parent_text = row.parent.get_text(strip=True)

            # Skip rows with a boost arrow
            if skip_row or len(multipliers) != 2 or len(parent_text) <= 10:
                continue

            # Calculate product and standard deviation
            product = multipliers[0] * multipliers[1]
            product = round(product, 5)
            std_dev = abs(multipliers[0] - multipliers[1]) / math.sqrt(2)
            std_dev = round(std_dev, 5)

            pair = {
                "multiplier1": multipliers[0],
                "multiplier2": multipliers[1],
                "product": product,
                "stdev": std_dev,
                "text": parent_text
            }

            try:
                divs = bet_container.select("div")
                pair['player_name'] = divs[0].get_text(strip=True)
                bet_container_button = bet_container.select("button")[0]
                button_divs = bet_container_button.select("div")
                pair['number'] = button_divs[1].get_text(strip=True)
                pair['stat'] = button_divs[2].get_text(strip=True)
                game_container = divs[4]
                game_container_spans = game_container.select("span")
                pair['game'] = game_container_spans[0].get_text(strip=True)
                pair['game_time'] = game_container_spans[1].get_text(strip=True)
            except Exception as e:
                print(f"Error parsing additional fields: {e}")
                pass

            pairs.append(pair)

    # Sort pairs by product (desc) and standard deviation (asc)
    pairs.sort(key=lambda x: (-x["product"], x["stdev"]))

    return pairs


def scrape_pp():

    out = []

    # Set up Selenium WebDriver with Chrome in headless mode
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("mobileEmulation", {
        "deviceMetrics": { "width": 375, "height": 812, "pixelRatio": 3.0 },
        "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
    })

    # Enable geolocation permissions
    prefs = {
        "profile.default_content_setting_values.geolocation": 1  # 1: Allow, 2: Block
    }
    chrome_options.add_experimental_option("prefs", prefs)

    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (recommended for headless)
    chrome_options.add_argument("--window-size=375,812")  # Set window size explicitly

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    DATE = datetime.now().strftime("%Y%m%d")
    TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        # Open the website
        homepage_url = "https://parlayplay.io"
        driver.get(homepage_url)
        time.sleep(5)  # Allow the page to load

        try:
            # Close the location prompt
            click_modal_button(driver)
            time.sleep(3)
        except Exception as e:
            print(f"Error closing location prompt: {e}")

        # Prepare output file
        os.makedirs("output-pp-selenium", exist_ok=True)
        output_file = os.path.join("output-pp-selenium", f"output-pp-selenium-{DATE}.jsonl")

        # Find all Type A buttons
        type_a_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[id^="league-"]')

        # Iterate over each Type A button
        for idx_a, a_button in enumerate(type_a_buttons[:3]):
            try:
                # Skip the "league-Promo" button
                if a_button.get_attribute("id") == "league-Promo":
                    continue

                if idx_a > 0:
                    # Click the Type A button
                    # a_button.click()
                    ActionChains(driver).move_to_element(a_button).click().perform()
                    time.sleep(5)  # Wait for the page to update

                # Find all Type B buttons under the current Type A category
                type_b_buttons = driver.find_elements(By.CSS_SELECTOR, 'button.mx-2.border-b-2')

                # Iterate over each Type B button
                for idx_b, b_button in enumerate(type_b_buttons):

                    try:
                        TIMESTAMP_STRING = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"[{TIMESTAMP_STRING}] Processing {a_button.text} - {b_button.text}")
                    except:
                        pass

                    try:

                        if idx_b > 0:
                            # Click the Type B button
                            ActionChains(driver).move_to_element(b_button).click().perform()
                            # b_button.click()
                            time.sleep(5)  # Wait for the page to update

                        # Pretty print the current driver page_source
                        # print(BeautifulSoup(driver.page_source, "html.parser").prettify())


                        # Click the "Change card style" button
                        try:
                            change_card_style_button = driver.find_element(By.CSS_SELECTOR, 
                                'button[aria-label="Change card style from list"]')
                            change_card_style_button.click()
                            time.sleep(2)  # Wait for the page to update
                        except Exception as e:
                            pass
                            # print(f"Error clicking 'Change card style' button: {e}")

                        # Get the page source
                        page_source = driver.page_source

                        # Process the HTML
                        results = process_html(page_source)

                        # Save each result as a JSON object
                        with open(output_file, "a") as file:
                            for result in results:
                                if result["product"] >= 3.45 and result["multiplier1"] >= 1.8 and result["multiplier2"] >= 1.8:
                                    print("\n\n\n*************************")
                                    print(f"Found a good pair")
                                    pprint(result)
                                    print("*************************\n\n\n")
                                result["timestamp"] = TIMESTAMP  # Add timestamp
                                result["type_a"] = a_button.text  # Add Type A category (e.g., NBA)
                                result["type_b"] = b_button.text  # Add Type B category (e.g., Rebounds)
                                file.write(json.dumps(result) + "\n")
                                out.append(result)

                    except Exception as e:
                        print(f"Error processing Type B button: {e}")
                        continue  # Skip to the next Type B button

            except Exception as e:
                print(f"Error processing Type A button: {e}")
                continue  # Skip to the next Type A button

    finally:
        # Close the browser
        driver.quit()

    return out



def create_figure(input_file_path, output_file_path):
    try:
        # Read the JSONL file
        data = []
        with open(input_file_path, 'r') as file:
            for line in file:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"Skipping invalid line: {line.strip()}")

        if not data:
            print("No valid data found in the file.")
            return

        # Create a DataFrame and ensure rows are unique
        df = pd.DataFrame(data).drop_duplicates()

        # Ensure required columns
        required_columns = ['multiplier1', 'multiplier2', 'timestamp', 'text']
        for col in required_columns:
            if col not in df.columns:
                print(f"Missing required column: {col}")
                return

        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])

        # Calculate the min_multiplier and the product
        df['min_multiplier'] = df[['multiplier1', 'multiplier2']].min(axis=1)
        df['product'] = df['multiplier1'] * df['multiplier2']

        # Identify the rows with the highest and second-highest max min multiplier
        sorted_rows = df.sort_values(by=['min_multiplier', 'product'], ascending=[False, False])

        # Get the highest max min row
        first_max_row = sorted_rows.iloc[0]
        
        # Get the second-highest max min row
        second_max_row = None
        if len(sorted_rows) > 1:
            second_max_row = sorted_rows.iloc[1]

        # Prepare data for plotting
        plot_data = (
            sorted_rows[['timestamp', 'product']]
            .groupby('timestamp')
            .max()
            .reset_index()
        ).set_index('timestamp')

        print(plot_data.head())

        # Plot the data
        plt.figure(figsize=(12, 6))
        plt.plot(plot_data.index, plot_data['product'], marker='o', label='Max Product (Filtered)')
        plt.title("Maximum Product with Maximum Minimum Multiplier Over Time")
        plt.xlabel("Timestamp")
        plt.ylabel("Product")
        plt.xticks(rotation=45)
        plt.grid(True)

        # Annotate the highest max min product
        plt.annotate(
            f"Highest: {first_max_row['text']}\nProduct: {first_max_row['product']:.2f}",
            xy=(first_max_row['timestamp'], first_max_row['product']),
            xytext=(first_max_row['timestamp'], first_max_row['product'] + 0.02),
            arrowprops=dict(facecolor='red', arrowstyle='->', lw=1.5),
            fontsize=10,
            color='blue'
        )

        # Annotate the second-highest max min product (if it exists)
        if second_max_row is not None:
            plt.annotate(
                f"Second Highest: {second_max_row['text']}\nProduct: {second_max_row['product']:.2f}",
                xy=(second_max_row['timestamp'], second_max_row['product']),
                xytext=(second_max_row['timestamp'], second_max_row['product'] - 0.02),
                arrowprops=dict(facecolor='green', arrowstyle='->', lw=1.5),
                fontsize=10,
                color='green'
            )

        plt.legend()
        plt.tight_layout()

        # Save the plot
        plt.savefig(output_file_path, format='pdf')
        plt.close()

        print(f"Plot saved to {output_file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")


def convert_jsonl_to_csv(input_file_path, output_file_path):
    """Converts a JSONL file to a CSV file."""
    try:
        # Read the JSONL file
        data = []
        with open(input_file_path, 'r') as file:
            for line in file:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"Skipping invalid line: {line.strip()}")

        if not data:
            print("No valid data found in the file.")
            return

        # Create a DataFrame and ensure rows are unique
        df = pd.DataFrame(data).drop_duplicates()

        # Save the DataFrame to a CSV file
        df.to_csv(output_file_path, index=False)

        TIMESTAMP_STR = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{TIMESTAMP_STR}] CSV file saved to: {output_file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")


def create_plots_with_r():
    """Creates plots using R scripts."""
    subprocess.run(["Rscript", "pp-plot.R"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":

    TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{TIMESTAMP}] Beginning Scrape")

    create_plots_with_r()
    results = scrape_pp()

    # Sort by product (descending) and standard deviation (ascending)
    results = [x for x in results if x['multiplier1'] >= 1.8 and x['multiplier2'] >= 1.8]
    results.sort(key=lambda x: (-x["product"], x["stdev"]))

    # Print the top 5 results
    print("\n\n\n*************************")
    print("Top 5 Results:")
    pprint(results[:5])
    print("*************************\n\n\n")

    output_dir = "output-pp-selenium"
    jsonl_files = os.listdir(output_dir)
    jsonl_files = [f for f in jsonl_files if f.endswith(".jsonl")]
    for jsonl_file in jsonl_files:
        input_file_path = os.path.join(output_dir, jsonl_file)
        output_file_path = input_file_path.replace(".jsonl", ".csv")
        convert_jsonl_to_csv(input_file_path, output_file_path)
    
    # Create figures with R
    create_plots_with_r()
    TIMESTAMP_STR = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{TIMESTAMP_STR}] FIGURES CREATED")
