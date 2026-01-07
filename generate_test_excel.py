import pandas as pd
import os

data = {
    'שם עסק': ['עסק בדיקה מורחב'],
    'עיר': ['הרצליה'],
    'טלפון': ['052-9999999'],
    'AnyDesk': ['987654321'],
    'מסגרת אשראי': [50000],
    'איש קשר': ['מנהל חשבונות'],
    'הערות': ['לבצע גבייה בסוף חודש'],
    'Last Order Date': ['2025-12-31']
}
df = pd.DataFrame(data)
output_path = '/Users/basharmawase/Nexsis/test_full_data.xlsx'
df.to_excel(output_path, index=False)
print(f"Created {output_path}")
