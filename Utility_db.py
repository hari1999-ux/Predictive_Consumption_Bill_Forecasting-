import sqlite3
import pandas as pd

# 1. Establish a connection to the SQLite database
conn = sqlite3.connect('utility_data.db')

# 2. Load the newest historical data containing the Year and Reading Date
gas_df = pd.read_csv("gas_customers_data_with_dates.csv")
elec_df = pd.read_csv("electric_customers_data_with_dates.csv")

# 3. Combine both datasets into a single Pandas DataFrame
combined_df = pd.concat([gas_df, elec_df], ignore_index=True)

# 4. Write the DataFrame directly into the database
# if_exists='replace' will overwrite the old table and automatically add the new date columns
combined_df.to_sql('customer_billing', conn, if_exists='replace', index=False)

print("Database 'utility_data.db' successfully updated with the new date fields.")

# 5. Close the database connection
conn.close()