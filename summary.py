import excel_to_df as ed
import warnings
warnings.filterwarnings('ignore')
import pandas as pd
sheets, names = ed.df_maker(r"C:\Users\purus\Downloads\generated_quotation(26).xls")
rows = []

for i, df in enumerate(sheets):
    df.rename(columns=str.lower, inplace=True)
    summ = sum(df['total price'].dropna())
    d = df['total price']*df['gst']
    d.dropna(inplace=True)
    gst = sum(d)
    row = {'Sheet':names[i], 'Amount': summ, 'GST value':gst}
    rows.append(row)

print(pd.DataFrame(rows))