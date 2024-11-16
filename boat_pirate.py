import os
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
from colorama import init, Fore, Style

init(autoreset=True)

csv_file_path = "boat_models.csv"
if os.path.exists(csv_file_path):
    os.remove(csv_file_path)
    print(Fore.YELLOW + f"{csv_file_path} har raderats.")

options = Options()
options.add_argument("--headless")
service = Service("/opt/homebrew/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

url = "https://sokbat.se/modeller"
driver.get(url)

boat_models = []
seen_models = set()

print(Fore.CYAN + Style.BRIGHT + "Startar insamling av båtmodeller från webbplatsen.")

soup = BeautifulSoup(driver.page_source, "html.parser")
total_count_element = soup.find("span", attrs={"data-bind": "text: count"})
total_count = int(total_count_element.text.strip()) if total_count_element else 0

try:
    with tqdm(
        total=total_count, desc="Hämtar båtmodeller", unit="modell", colour="BLUE"
    ) as pbar:
        while True:
            try:
                button = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located(
                        (By.XPATH, "//button[@data-bind='click: loadMoreRecords']")
                    )
                )
                ActionChains(driver).move_to_element(button).click(button).perform()
                time.sleep(2)

                soup = BeautifulSoup(driver.page_source, "html.parser")
                model_list = soup.find("div", class_="list-model")
                if model_list:
                    models = model_list.find_all("div", class_="list-item")

                    new_models = []
                    for model in models:
                        model_brand_name = model.find(
                            "div", attrs={"data-bind": "text: model_brand_name"}
                        )
                        model_name = model.find(
                            "div", attrs={"data-bind": "text: name"}
                        )

                        model_brand_name_text = (
                            model_brand_name.text.strip()
                            if model_brand_name
                            else "Okänd tillverkare"
                        )
                        model_name_text = (
                            model_name.text.strip() if model_name else "Okänd modell"
                        )

                        model_identifier = (model_brand_name_text, model_name_text)
                        if model_identifier not in seen_models:
                            seen_models.add(model_identifier)
                            new_models.append(
                                {
                                    "Model Brand Name": model_brand_name_text,
                                    "Model Name": model_name_text,
                                }
                            )

                    boat_models.extend(new_models)
                    pbar.update(len(new_models))

                    try:
                        existing_df = pd.read_csv("boat_models.csv")
                        new_df = pd.DataFrame(new_models)
                        combined_df = (
                            pd.concat([existing_df, new_df])
                            .drop_duplicates()
                            .reset_index(drop=True)
                        )
                    except FileNotFoundError:
                        combined_df = pd.DataFrame(new_models)

                    combined_df.to_csv("boat_models.csv", index=False, encoding="utf-8")

                    time.sleep(2)
                else:
                    print(
                        Fore.GREEN
                        + Style.BRIGHT
                        + "Inga fler modeller att ladda. Vi är klara här."
                    )
                    break
            except Exception as e:
                print(Fore.RED + Style.BRIGHT + f"Ett fel inträffade: {e}")
                break

finally:
    driver.quit()
    print(Fore.CYAN + Style.BRIGHT + "Webbläsaren stängdes.")

df = pd.DataFrame(boat_models)
df.to_csv("boat_models.csv", index=False, encoding="utf-8")
print(
    Fore.CYAN
    + Style.BRIGHT
    + "Data har sparats till 'boat_models.csv'. Totalt antal modeller:",
    len(boat_models),
)


def remove_duplicates_from_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        df.drop_duplicates(inplace=True)
        df.to_csv(file_path, index=False, encoding="utf-8")
        print(Fore.GREEN + Style.BRIGHT + "Dubbletter har raderats från CSV-filen.")
    except FileNotFoundError:
        print(Fore.RED + Style.BRIGHT + "CSV-filen hittades inte.")


remove_duplicates_from_csv("boat_models.csv")
