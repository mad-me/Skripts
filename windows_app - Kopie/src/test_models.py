from models import PandasModel, DataLoader
import pandas as pd

# Test PandasModel
df = pd.DataFrame({"A":[1,2], "B":[3,4]})
model = PandasModel(df)
print("Rows:", model.rowCount(), "Cols:", model.columnCount())

# Test DataLoader
def on_data(df):
    print("DataLoader hat geladen:", df.head())

loader = DataLoader()
loader.data_ready.connect(on_data)
loader.start()
loader.wait()
