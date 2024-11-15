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

options = Options()
options.add_argument("--headless")
service = Service("/opt/homebrew/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

url = "https://sokbat.se/modeller"
driver.get(url)

boat_models = []

print("Startar olaglig insamling av båtmodeller från webbplatsen.")

try:
    while True:
        try:
            button = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//button[@data-bind='click: loadMoreRecords']")
                )
            )
            print("Knappen 'Visa fler modeller' hittad. Laddar fler modeller...")
            ActionChains(driver).move_to_element(button).click(button).perform()
            time.sleep(2)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            model_list = soup.find("div", class_="list-model")
            if model_list:
                models = model_list.find_all("div", class_="list-item")
                print(f"Antal hittade objekt: {len(models)}")

                new_models = []
                for model in models:
                    model_brand_name = model.find(
                        "div", attrs={"data-bind": "text: model_brand_name"}
                    )
                    model_name = model.find("div", attrs={"data-bind": "text: name"})

                    model_brand_name_text = (
                        model_brand_name.text.strip()
                        if model_brand_name
                        else "Okänd tillverkare"
                    )
                    model_name_text = (
                        model_name.text.strip() if model_name else "Okänd modell"
                    )

                    new_models.append(
                        {
                            "Model Brand Name": model_brand_name_text,
                            "Model Name": model_name_text,
                        }
                    )

                boat_models.extend(new_models)

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
                print("Data har sparats till 'boat_models.csv'.")

                time.sleep(2)
        except:
            print("Inga fler modeller att ladda. Vi är klara här.")
            break

finally:
    driver.quit()
    print("Webbläsaren stängdes. SÄPO är notifierat.")

df = pd.DataFrame(boat_models)
df.to_csv("boat_models.csv", index=False, encoding="utf-8")
print(
    "Data har sparats till 'boat_models.csv'. Totalt antal modeller:", len(boat_models)
)
