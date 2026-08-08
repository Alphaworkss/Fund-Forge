import pandas as pd
import os


def save_to_excel(news_list, excel_path):
    """
    Saves news articles into an Excel file.

    - Creates the file if it doesn't exist.
    - Updates the existing file if it exists.
    - Prevents duplicate articles using the URL.
    """

    new_df = pd.DataFrame(news_list)

    found = len(new_df)

    if os.path.exists(excel_path):

        old_df = pd.read_excel(excel_path)
        old_count = len(old_df)

        combined_df = pd.concat([old_df, new_df], ignore_index=True)

        combined_df.drop_duplicates(
            subset=["URL"],
            keep="first",
            inplace=True
        )

        new_count = len(combined_df)

        added = new_count - old_count
        skipped = found - added

    else:

        combined_df = new_df

        added = found
        skipped = 0

    combined_df.to_excel(excel_path, index=False)

    print(f"Articles found   : {found}")
    print(f"New articles     : {added}")
    print(f"Duplicates skipped: {skipped}")
    print(f"Total stored     : {len(combined_df)}")