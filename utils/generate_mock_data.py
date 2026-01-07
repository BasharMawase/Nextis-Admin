import pandas as pd
import random

def generate_mock_data():
    cities = ['תל אביב', 'חיפה', 'ירושלים', 'ראשון לציון', 'אילת', 'New York', 'London']
    categories = ['Cafe', 'Restaurant', 'Retail', 'Supermarket', 'Bar']
    
    data = []
    for i in range(50):
        city = random.choice(cities)
        data.append({
            'Business Name': f'Business {i+1} {random.choice(categories)}',
            'עיר כתובת או מקום העלסק': city,
            'Phone': f'05{random.randint(0,9)}-{random.randint(1000000, 9999999)}',
            'AnyDesk': f'{random.randint(100, 999)} {random.randint(100, 999)} {random.randint(100, 999)}',
            'Category': random.choice(categories)
        })
    
    df = pd.DataFrame(data)
    df.to_excel('/Users/basharmawase/Nexsis/mock_clients_hebrew.xlsx', index=False)
    print("Mock data created: mock_clients_hebrew.xlsx")

if __name__ == "__main__":
    generate_mock_data()
