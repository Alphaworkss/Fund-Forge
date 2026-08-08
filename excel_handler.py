import os
import pandas as pd


DATA_FOLDER = "data"
EXCEL_FILE = os.path.join(DATA_FOLDER, "FundForge_Data.xlsx")


def save_dataframe(df, sheet_name):

    if df.empty:
        print(f"{sheet_name}: No data found.")
        return

    os.makedirs(DATA_FOLDER, exist_ok=True)

    # ---------------------------------------------------
    # Excel doesn't exist yet
    # ---------------------------------------------------

    if not os.path.exists(EXCEL_FILE):

        with pd.ExcelWriter(
            EXCEL_FILE,
            engine="openpyxl"
        ) as writer:

            df.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False
            )

        print(f"{sheet_name}: Excel created.")

        return

    # ---------------------------------------------------
    # Excel exists
    # ---------------------------------------------------

    try:

        excel = pd.ExcelFile(EXCEL_FILE)

        if sheet_name in excel.sheet_names:

            old_df = pd.read_excel(
                EXCEL_FILE,
                sheet_name=sheet_name
            )

            combined = pd.concat(
                [old_df, df],
                ignore_index=True
            )

            # Remove duplicates
            combined.drop_duplicates(
                inplace=True
            )

        else:

            combined = df

        # Read all existing sheets
        sheets = {}

        for sheet in excel.sheet_names:

            if sheet == sheet_name:
                sheets[sheet] = combined

            else:
                sheets[sheet] = pd.read_excel(
                    EXCEL_FILE,
                    sheet_name=sheet
                )

        # Add new sheet if needed
        if sheet_name not in sheets:

            sheets[sheet_name] = combined

        # Rewrite workbook
        with pd.ExcelWriter(
            EXCEL_FILE,
            engine="openpyxl"
        ) as writer:

            for name, dataframe in sheets.items():

                dataframe.to_excel(
                    writer,
                    sheet_name=name,
                    index=False
                )

        print(
            f"{sheet_name}: {len(df)} new rows added."
        )

    except Exception as e:

        print("Excel Error:", e)