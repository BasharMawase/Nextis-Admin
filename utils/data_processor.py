@st.cache_data
def load_and_clean_data(uploaded_files):
    # This function is now DEPRECATED in favor of direct processing in app.py or simplified logic
    # But to maintain compatibility if called:
    return pd.DataFrame()

# Simplified processing logic for Flask
def process_excel_file(file_path):
    # Already implemented in app.py process_excel? 
    # Let's check app.py. It imports process_excel from HERE?
    # app.py: from utils.data_processor import process_excel
    pass

# We need to find `process_excel` definition. 
# The `view_file` showed `load_and_clean_data` at top, but didn't show `process_excel`?
# Ah, I viewed lines 1-98. "The above content shows the entire... file".
# ERROR: `process_excel` IS NOT IN THE FILE?
# Then `app.py` `from utils.data_processor import process_excel` would FAIL.
# But server IS RUNNING.
# Maybe `process_excel` IS `load_and_clean_data`? 
# No, `app.py` calls `process_excel(filepath)`. `load_and_clean_data` takes `uploaded_files`.
# I MUST HAVE MISSED IT.
# I'll check `app.py` imports.

    """
    Loads multiple Excel/CSV files, cleans them, and merges into one DataFrame.
    """
    all_data = []

    for file in uploaded_files:
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            # 1. Add Source File Column
            df['source_file'] = file.name
            
            # 2. Standardize Columns (strip whitespace)
            df.columns = df.columns.str.strip()
            
            # 3. Ensure Essential Columns Exist (Fuzzy matching or Defaulting)
            # We look for 'Location' or 'City' or 'עיר' or 'מיקום'
            # We look for 'AnyDesk'
            
            # 3. Ensure Essential Columns Exist (Fuzzy Matching)
            # We iterate through columns and check for keywords to rename them standard names
            
            # Define keywords for each target column
            target_keywords = {
                'Location': ['location', 'city', 'address', 'עיר', 'מיקום', 'כתובת', 'מקום'],
                'AnyDesk': ['anydesk', 'אנידסק'],
                'Phone': ['phone', 'mobile', 'cell', 'tel', 'טלפון', 'נייד', 'פלאפון'],
                'Business Name': ['business', 'company', 'name', 'שם עסק', 'עסק']
            }
            
            # Create a renaming map based on existing columns
            rename_map = {}
            for col in df.columns:
                col_lower = str(col).lower()
                for target, keywords in target_keywords.items():
                    # If we haven't found a match for this target yet
                    # Check if any keyword matches the column name
                    if any(k in col_lower for k in keywords):
                        # Avoid overwriting if we already found a primary column for this target?
                        # For now, let's just map it. First match wins or last match wins?
                        # Usually "City" is better than "City Address", but let's just take the first one we find.
                         if target not in rename_map.values():
                             rename_map[col] = target
                             break # Stop checking other targets for this column
            
            if rename_map:
                df.rename(columns=rename_map, inplace=True)
            
            # Fill missing core columns if they don't exist
            if 'Location' not in df.columns:
                df['Location'] = 'אין'
            if 'AnyDesk' not in df.columns:
                df['AnyDesk'] = 'אין'
            if 'Business Name' not in df.columns:
                # Try to find the first string column? Or just name it Unknown
                df['Business Name'] = 'עסק ללא שם'

            # 4. Clean Data
            # Drop empty rows
            df.dropna(how='all', inplace=True)
            
            # Clean Phone Numbers (Israeli Format)
            if 'Phone' in df.columns:
                def format_israeli_phone(val):
                    s = str(val).strip()
                    # Remove non-digits
                    digits = ''.join(filter(str.isdigit, s))
                    
                    # Check for Mobile (05X)
                    if len(digits) == 10 and digits.startswith('05'):
                        return f"{digits[:3]}-{digits[3:]}"
                    
                    # Check for Landline (02, 03, 04, 08, 09)
                    elif len(digits) == 9 and digits.startswith('0'):
                        return f"{digits[:2]}-{digits[2:]}"
                    
                    return s # Return original if not matching standard lengths

                df['Phone'] = df['Phone'].apply(format_israeli_phone)

            all_data.append(df)
            
        except Exception as e:
            st.error(f"Error loading {file.name}: {e}")

    if all_data:
        merged_df = pd.concat(all_data, ignore_index=True)
        return merged_df
    return pd.DataFrame()
