from shared import *
import urllib3

urllib3.disable_warnings()

with sync_playwright() as playwright:
    br = get_browser(playwright)
    
    with open("sites.txt", 'r') as file:
            

                for line in file.readlines():
                    url = line.strip()
                    print(f"Processing {url}")
                    try:
                        
                        if url:
                            page = get_initial_page(br, url)
                            print("Getting database tables")
                            database_tables = get_database_tables(page)
                            sensitivity_scores = {}
                            for index, row in database_tables.iterrows():
                                database_name = row["Database tables"]
                                print(f"Getting data for {database_name}")
                                try:
                                    data = get_dataframe_for_table(page, database_name)
                                    if data is not None and len(data) != 0:
                                        sensitivity_scores[database_name] = judge_data(database_name, data)
                                except:
                                    print(f"could not fetch data for {database_name}")
                            
                            calculated_scores = calculate_scores(sensitivity_scores)

                            output = {
                                "url" : url,
                                "security_scores" : sensitivity_scores,
                                "number_of_tables_with_data" : len(sensitivity_scores),
                                "max_score" : calculated_scores["max"],
                                "avg_score" : calculated_scores["avg"]
                            }
                            write_to_opensearch(output, "mendix-per-site", "https://localhost:9200", "admin", "Unturned-User7-Snugness-Crisped")

                            for key, value in sensitivity_scores.items():
                                if value != None:
                                    value["url"] = url
                                    value["database_table"] = key
                                    write_to_opensearch(value, "mendix-per-table", "https://localhost:9200", "admin", "Unturned-User7-Snugness-Crisped")
                    except:
                        data = {
                             "url" : url,
                             "number_of_tables_with_data" : 0
                        }
                        write_to_opensearch(data, "mendix-per-table", "https://localhost:9200", "admin", "Unturned-User7-Snugness-Crisped")
                        pass