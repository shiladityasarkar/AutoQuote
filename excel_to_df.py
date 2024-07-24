import base64
from dotenv import load_dotenv
import pandas as pd
import openpyxl
from pathlib import Path
import win32com.client
from io import BytesIO
from openpyxl_image_loader import SheetImageLoader
 
load_dotenv()

def convert_xls_to_xlsx(path):
    excel = win32com.client.Dispatch('Excel.Application')
    excel.Visible = False
    try:
        wb = excel.Workbooks.Open(path)
        xlsx_path = path[:-4] + ".xlsx"
        wb.SaveAs(xlsx_path, FileFormat=51) # 51 is the file format for xlsx
        wb.Close()
    except Exception as e:
        raise RuntimeError("An error occurred while converting the file.")
    finally:
        excel.Quit()
    return xlsx_path

def images_xlsx(sheet, header_row, img_col):
    loader = SheetImageLoader(sheet)
    images = []
    for row in sheet.iter_rows(min_row=header_row + 2, max_row=sheet.max_row, min_col=img_col + 1, max_col=img_col + 1):
        for cell in row:
            try:
                image = loader.get(cell.coordinate)
                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format='png')
                images.append(base64.b64encode(img_byte_arr.getvalue()))
            except:
                images.append(None)
    return images

def dfmaker(path):
    excel_obj = pd.ExcelFile(path)
    sheets = []

    # Checking if a .xlsx file already exists
    file_check = Path(path[:-4] + ".xlsx")
    if not file_check.is_file():
        convert_xls_to_xlsx(path)
        
    path = path[:-4] + ".xlsx"

    for sheet in excel_obj.book:
        # Getting the index of header row
        for idx, row in enumerate(sheet):
            header_cols = ['qty', 'price']
            if any([val in ''.join([str(row_str) for row_str in row]).lower() for val in header_cols]):
                header_row = idx
                break
        # Getting the sheet name and loading the sheet
        sheet_name = str(sheet).split(':')[1].replace('<', '').replace('>', '')
        if sheet_name != "Summary":
            df = pd.read_excel(excel_obj, sheet_name, header=header_row)

            # Getting the image column
            img_cols, col_name = [], []
            for idx, key in enumerate(df.keys()):
                if 'image' in key.lower():
                    img_cols.append(idx)
                    col_name.append(key)

            xlsx_file = openpyxl.load_workbook(path)
            img_sheet = xlsx_file[sheet_name]

            # Adding the images to their respective columns
            if col_name != None:
                for img_col, col in zip(img_cols, col_name):
                    images = images_xlsx(img_sheet, header_row, img_col)
                    df[col] = images#list(map(lambda x: x.decode(), images))
            sheets.append(df)

    return sheets
    
if __name__ == "__main__":
    path = r"S:\AutoQuote\data\WALTHR PRICE LIST.xls"
    df = df_maker(path)
    df[0].to_excel('multiple_images.xlsx')
    print("File saved!")