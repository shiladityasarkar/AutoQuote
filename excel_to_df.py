import os
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
    wb = excel.Workbooks.Open(path)
    wb.SaveAs(path[:-4] + ".xlsx", FileFormat=51)
    wb.Close()
    excel.Application.Quit()

def images_xlsx(sheet, header_row, img_col):
    loader = SheetImageLoader(sheet)
    images = []
    for row in sheet.iter_rows(min_row=header_row + 2, max_row=sheet.max_row, min_col=img_col + 1, max_col=img_col + 1):
        for cell in row:
            if loader.image_in(cell.coordinate):
                image = loader.get(cell.coordinate)
                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format='PNG')
                images.append(img_byte_arr.getvalue())
            else:
                images.append(None)
    return images

def main(path):
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
            if 'qty' in ''.join([str(row_str) for row_str in row]).lower():
                header_row = idx
                break
        # Getting the sheet name and loading the sheet
        sheet_name = str(sheet).split(':')[1].replace('<', '').replace('>', '')
        df = pd.read_excel(excel_obj, sheet_name, header=header_row)
        
        # Getting the image column
        img_col = None
        for idx, key in enumerate(df.keys()):
            if 'image' in key.lower():
                img_col = idx
                col_name = key
                break

        xlsx_file = openpyxl.load_workbook(path)
        img_sheet = xlsx_file[sheet_name]

        if img_col != None:
            images = images_xlsx(img_sheet, header_row, img_col)
            df[col_name] = images
            
        sheets.append(df)

    return sheets
    
if __name__ == "__main__":
    path = os.environ["FILE_PATH"]
    df = main(path)
    print(df[1])