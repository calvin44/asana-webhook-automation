from re import sub
from gspread import Worksheet
from gspread.utils import ValueRenderOption, rowcol_to_a1, ValueInputOption
from loguru import logger
from scoring_system.g_sheet import get_sheet_client


def append_new_company(company_name: str):
    """
    Add a new company to the scoring system table.
    """
    try:
        client = get_sheet_client()
        spreadsheet = client.open("Project Scoring System")
        sheet = spreadsheet.worksheet("Project Scoring")

        # Locate header cells
        headers = {
            "Project": sheet.find("Project"),
            "BusinessValue": sheet.find("TOTAL BUSINESS VALUE SCORE"),
            "Complexity": sheet.find("TOTAL COMPLEXITY SCORE"),
        }

        for key, cell in headers.items():
            logger.info(f"{key} Header - Row: {cell.row}, Col: {cell.col}")

        # Determine the next available row by checking Project column
        last_row = get_last_filled_row(sheet, headers["Project"])
        new_row = last_row + 1

        # Extract and shift formulas
        business_formula = get_formula_from_cell(
            sheet, last_row, headers["BusinessValue"].col)
        complexity_formula = get_formula_from_cell(
            sheet, last_row, headers["Complexity"].col)

        # Calculate target cell addresses
        updates = [
            {
                "range": rowcol_to_a1(new_row, headers["Project"].col),
                "values": [[company_name]],
            },
            {
                "range": rowcol_to_a1(new_row, headers["BusinessValue"].col),
                "values": [[business_formula]],
            },
            {
                "range": rowcol_to_a1(new_row, headers["Complexity"].col),
                "values": [[complexity_formula]],
            },
        ]

        # Batch update with formulas using user_entered mode
        sheet.batch_update(
            data=updates,
            value_input_option=ValueInputOption.user_entered,
        )

        logger.success(f"Successfully appended company '{company_name}'")

    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Error appending company '{company_name}': {e}")


def get_formula_from_cell(sheet: Worksheet, row: int, col: int) -> str:
    """
    Extracts and shifts formula in a given cell to the next row.
    """
    address = rowcol_to_a1(row, col)
    formula = sheet.get(
        address, value_render_option=ValueRenderOption.formula).first()
    return shift_formula_rows(formula)


def shift_formula_rows(formula: str, shift: int = 1) -> str:
    """
    Shift all row numbers in Excel-style cell references in a formula.
    E.g., "=SUM(A1, B2)" -> "=SUM(A2, B3)" for shift=1
    """
    def replace(match):
        col = match.group(1)
        row = int(match.group(2))
        return f"{col}{row + shift}"

    pattern = r"([A-Z]+)(\d+)"
    return sub(pattern, replace, formula)


def get_last_filled_row(sheet: Worksheet, header_cell) -> int:
    """
    Get the last filled row in the same column as the header.
    """
    column_values = sheet.col_values(header_cell.col)
    return len(column_values)
